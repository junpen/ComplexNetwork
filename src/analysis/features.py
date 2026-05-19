"""
网络特征分析模块

本模块提供了复杂网络的特征指标分析功能，包括：
- 基础拓扑指标：节点数、边数、密度等
- 度分析：度分布统计、入度/出度分析、Top节点排名
- 距离分析：连通分量识别、最短路径、直径、半径等
- 中心性分析：度中心性、介数中心性、接近中心性、特征向量中心性、PageRank
- 聚集分析：聚集系数、三角形计数、方形聚集系数
- 网络级指标：同配性、幂律指数、度序列等

该模块基于异构图（HeterogeneousGraph）的投影图进行分析，
投影图是将异构信息网络中的多类型节点和边统一映射为同构图后的表示。
"""

import networkx as nx
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

from src.network.heterogeneous_graph import HeterogeneousGraph
from config import ANALYSIS_CONFIG


class FeatureAnalyzer:
    """
    复杂网络特征指标分析器

    负责对异构信息网络进行全面的结构特征分析。分析器基于异构图的投影图
    （无向加权图）进行计算，涵盖基础指标、度分布、距离、中心性、聚集性
    以及网络级别的宏观指标。

    Attributes:
        het_graph: 异构图对象，包含多类型节点和边
        projected: 异构图的投影图（无向加权图），作为大多数分析的基础
        _cache: 内部缓存字典，用于存储中间计算结果，避免重复计算
    """

    def __init__(self, graph: HeterogeneousGraph):
        """
        初始化特征分析器

        Args:
            graph: 异构图对象，提供底层网络数据及节点/边类型信息
        """
        self.het_graph = graph
        # 获取异构图的投影图（无向加权图），后续大部分分析基于该投影图
        self.projected = graph.get_projected_graph()
        self._cache: Dict[str, Any] = {}

    def analyze_all(self) -> Dict[str, Any]:
        """
        执行全量网络特征分析

        依次调用所有子分析模块，汇总返回完整的网络特征报告。

        Returns:
            Dict[str, Any]: 包含所有特征分析结果的字典，键包括：
                - basic_metrics: 基础拓扑指标
                - degree_analysis: 度分析结果
                - distance_analysis: 距离分析结果
                - centrality_analysis: 中心性分析结果
                - clustering_analysis: 聚集性分析结果
                - network_level_metrics: 网络级宏观指标
        """
        results = {
            "basic_metrics": self.basic_metrics(),
            "degree_analysis": self.degree_analysis(),
            "distance_analysis": self.distance_analysis(),
            "centrality_analysis": self.centrality_analysis(),
            "clustering_analysis": self.clustering_analysis(),
            "network_level_metrics": self.network_level_metrics(),
        }
        return results

    def basic_metrics(self) -> Dict[str, Any]:
        """
        计算网络的基础拓扑指标

        包括节点数量、边数量以及网络密度。

        Returns:
            Dict[str, Any]: 基础指标字典，包含：
                - node_count: 节点总数
                - edge_count: 边总数
                - density: 网络密度（实际边数 / 最大可能边数）
        """
        return {
            "node_count": self.het_graph.get_node_count(),
            "edge_count": self.het_graph.get_edge_count(),
            "density": nx.density(self.projected),
        }

    def degree_analysis(self, top_n: int = None) -> Dict[str, Any]:
        """
        节点的度分析

        分析投影图中的度分布特征，同时在异构图上分别计算入度和出度。
        度（Degree）是衡量节点连接数目的基本指标，反映了节点的直接影响力。

        Args:
            top_n: 返回度最高的前 N 个节点，默认从配置文件读取

        Returns:
            Dict[str, Any]: 度分析结果，包含：
                - degree_distribution: 度分布统计（均值、标准差、分位数等）
                - top_nodes_by_degree: 度最高的前 N 个节点列表
                - average_degree: 平均度
                - max_degree: 最大度
                - min_degree: 最小度
                - in_degree_stats: 入度分布统计
                - out_degree_stats: 出度分布统计
        """
        if top_n is None:
            top_n = ANALYSIS_CONFIG["default_top_n"]

        # 计算投影图上每个节点的加权度（考虑边权重的度值）
        degrees = dict(self.projected.degree(weight="weight"))
        # 分别统计异构图上每个节点的入度和出度（有向图的度分解）
        in_degrees = {}
        out_degrees = {}

        for node in self.het_graph.graph.nodes():
            # 入度：指向该节点的边数（加权）
            in_degrees[node] = self.het_graph.graph.in_degree(node, weight="weight")
            # 出度：从该节点出发的边数（加权）
            out_degrees[node] = self.het_graph.graph.out_degree(node, weight="weight")

        # 按度值降序排列，用于后续提取 Top 节点
        sorted_degrees = sorted(degrees.items(), key=lambda x: x[1], reverse=True)

        return {
            "degree_distribution": self._distribution_stats(list(degrees.values())),
            "top_nodes_by_degree": [
                {"node": node, "degree": deg,
                 "label": self.het_graph.get_node_info(node).get("label", node)}
                for node, deg in sorted_degrees[:top_n]
            ],
            "average_degree": np.mean(list(degrees.values())),
            "max_degree": max(degrees.values()) if degrees else 0,
            "min_degree": min(degrees.values()) if degrees else 0,
            "in_degree_stats": self._distribution_stats(list(in_degrees.values())),
            "out_degree_stats": self._distribution_stats(list(out_degrees.values())),
        }

    def distance_analysis(self) -> Dict[str, Any]:
        """
        网络距离分析

        分析网络中节点间的距离特征，包括连通性检测、最短路径长度、
        网络直径和半径等。对于不连通的网络，分析在最大连通分量上进行。

        算法流程：
        1. 检测网络连通性，若不连通则提取最大连通分量
        2. 计算所有节点对之间的最短路径长度
        3. 基于最短路径计算离心率（eccentricity）、直径和半径

        Returns:
            Dict[str, Any]: 距离分析结果，包含：
                - is_connected: 网络是否连通
                - component_count: 连通分量数量
                - largest_component_size: 最大连通分量大小
                - largest_component_ratio: 最大连通分量占比
                - average_shortest_path_length: 平均最短路径长度
                - diameter: 网络直径（最大离心率）
                - radius: 网络半径（最小离心率）
                - distance_distribution: 距离分布统计
        """
        # 步骤1：检测网络连通性，若不连通则提取最大连通分量进行分析
        if not nx.is_connected(self.projected):
            # 网络不连通，获取所有连通分量
            components = list(nx.connected_components(self.projected))
            # 提取最大连通分量（包含节点数最多的分量）
            largest_cc = max(components, key=len)
            # 基于最大连通分量构建子图
            subgraph = self.projected.subgraph(largest_cc).copy()
            component_info = {
                "is_connected": False,
                "component_count": len(components),
                "largest_component_size": len(largest_cc),
                "largest_component_ratio": len(largest_cc) / self.projected.number_of_nodes(),
            }
        else:
            # 网络连通，直接使用整个投影图
            subgraph = self.projected
            component_info = {
                "is_connected": True,
                "component_count": 1,
                "largest_component_size": subgraph.number_of_nodes(),
                "largest_component_ratio": 1.0,
            }

        # 步骤2：计算最短路径相关指标（仅在连通子图上）
        if subgraph.number_of_nodes() > 1:
            # 计算所有节点对之间的最短路径长度（BFS/Dijkstra）
            shortest_paths = dict(nx.all_pairs_shortest_path_length(subgraph))
            all_distances = []
            # 离心率：某节点到网络中最远节点的最短路径长度
            eccentricities = {}
            for source, targets in shortest_paths.items():
                for target, dist in targets.items():
                    if source != target:
                        all_distances.append(dist)
                # 取该节点到所有可达节点中的最大距离作为离心率
                if targets:
                    eccentricities[source] = max(targets.values())
                else:
                    eccentricities[source] = 0

            # 平均最短路径长度：所有节点对之间距离的均值
            avg_shortest_path = np.mean(all_distances) if all_distances else 0
            # 网络直径：所有节点中最大的离心率（网络中任意两节点间的最长最短路径）
            diameter = max(eccentricities.values()) if eccentricities else 0
            # 网络半径：所有节点中最小的离心率（网络的"中心"到达最远节点的距离）
            radius = min(eccentricities.values()) if eccentricities else 0
            distance_distribution = self._distribution_stats(all_distances)
        else:
            avg_shortest_path = 0
            diameter = 0
            radius = 0
            distance_distribution = {}

        return {
            **component_info,
            "average_shortest_path_length": avg_shortest_path,
            "diameter": diameter,
            "radius": radius,
            "distance_distribution": distance_distribution,
        }

    def centrality_analysis(self, top_n: int = None) -> Dict[str, Any]:
        """
        中心性分析：度中心性、介数中心性、接近中心性、特征向量中心性、PageRank

        中心性指标用于量化网络中每个节点的重要程度，不同指标从不同维度刻画节点影响力：
        - 度中心性（Degree Centrality）：基于直接连接数衡量影响力
        - 介数中心性（Betweenness Centrality）：基于最短路径上的中转次数衡量"桥梁"作用
        - 接近中心性（Closeness Centrality）：基于到所有其他节点的平均距离衡量可达性
        - 特征向量中心性（Eigenvector Centrality）：衡量与高中心性节点的连接程度
        - PageRank：基于随机游走模型的节点重要性排序算法

        Args:
            top_n: 返回各中心性指标排名前 N 的节点，默认从配置文件读取

        Returns:
            Dict[str, Any]: 各中心性指标的分析结果，每个指标包含：
                - top_nodes: 中心性最高的前 N 个节点列表
                - distribution: 中心性值的分布统计
        """
        if top_n is None:
            top_n = ANALYSIS_CONFIG["default_top_n"]

        n = self.projected.number_of_nodes()

        # 度中心性：节点的度 / (n-1)，归一化到 [0, 1]
        # 反映节点直接连接的广泛程度
        degree_centrality = nx.degree_centrality(self.projected) if n > 0 else {}

        # 介数中心性：经过该节点的最短路径数量 / 所有可能的最短路径数量
        # 反映节点作为"信息中转站"的重要程度，使用边权重进行归一化
        betweenness_centrality = nx.betweenness_centrality(
            self.projected, weight="weight", normalized=True
        ) if n > 1 else {}

        # 接近中心性：(n-1) / 节点到所有其他节点的最短路径长度之和
        # 值越大表示该节点越"接近"网络中心，信息传播越快
        closeness_centrality = nx.closeness_centrality(self.projected) if n > 1 else {}

        # 特征向量中心性：节点的重要性取决于其邻居的重要性
        # 优先使用 NumPy 实现（更快更稳定），失败时回退到迭代方法
        try:
            eigenvector_centrality = nx.eigenvector_centrality_numpy(
                self.projected, weight="weight"
            ) if n > 0 else {}
        except Exception:
            eigenvector_centrality = nx.eigenvector_centrality(
                self.projected, weight="weight", max_iter=1000
            ) if n > 0 else {}

        # PageRank：基于网页排名思想，考虑邻居的权重和数量
        # 通过模拟随机游走来评估节点的全局重要性
        pagerank = nx.pagerank(self.projected, weight="weight") if n > 0 else {}

        return {
            "degree_centrality": {
                "top_nodes": self._top_centrality_nodes(degree_centrality, top_n),
                "distribution": self._distribution_stats(list(degree_centrality.values())),
            },
            "betweenness_centrality": {
                "top_nodes": self._top_centrality_nodes(betweenness_centrality, top_n),
                "distribution": self._distribution_stats(list(betweenness_centrality.values())),
            },
            "closeness_centrality": {
                "top_nodes": self._top_centrality_nodes(closeness_centrality, top_n),
                "distribution": self._distribution_stats(list(closeness_centrality.values())),
            },
            "eigenvector_centrality": {
                "top_nodes": self._top_centrality_nodes(eigenvector_centrality, top_n),
                "distribution": self._distribution_stats(list(eigenvector_centrality.values())),
            },
            "pagerank": {
                "top_nodes": self._top_centrality_nodes(pagerank, top_n),
                "distribution": self._distribution_stats(list(pagerank.values())),
            },
        }

    def clustering_analysis(self, top_n: int = None) -> Dict[str, Any]:
        """
        聚集系数分析

        聚集系数衡量的是网络中节点的邻居之间也相互连接的倾向程度。
        高聚集系数意味着"朋友之间也互为朋友"的现象更加普遍。

        本方法分析：
        - 局部聚集系数：每个节点的邻居之间实际连接数 / 最大可能连接数
        - 全局平均聚集系数：所有节点局部聚集系数的均值
        - 三角形计数：每个节点参与的三元环数量
        - 方形聚集系数：基于四元环的聚集度量，适用于稀疏网络

        Args:
            top_n: 返回聚集系数最高的前 N 个节点，默认从配置文件读取

        Returns:
            Dict[str, Any]: 聚集性分析结果，包含：
                - average_clustering_coefficient: 全局平均聚集系数
                - top_nodes_by_clustering: 聚集系数最高的节点列表
                - clustering_distribution: 聚集系数分布统计
                - triangles_per_node: 三角形统计（平均数和总数）
                - square_clustering: 方形聚集系数统计
        """
        if top_n is None:
            top_n = ANALYSIS_CONFIG["default_top_n"]

        n = self.projected.number_of_nodes()

        # 局部聚集系数（考虑边权重）
        clustering_coeffs = nx.clustering(self.projected, weight="weight") if n > 1 else {}
        # 全局平均聚集系数：所有节点局部聚集系数的算术平均值
        avg_clustering = nx.average_clustering(self.projected, weight="weight") if n > 1 else 0.0

        sorted_clustering = sorted(clustering_coeffs.items(), key=lambda x: x[1], reverse=True)

        # 三角形计数：每个节点参与的三元环（三角形）数量
        # 三角形是网络中最基本的闭合结构，反映局部凝聚程度
        try:
            triangles_per_node = nx.triangles(self.projected)
        except Exception:
            triangles_per_node = {}

        # 方形聚集系数：基于四元环的聚集度量
        # 与三角形聚集系数相比，方形聚集在边密度较低时仍可提供有意义的信息
        square_clustering = {}
        try:
            if n > 0:
                square_clustering = nx.square_clustering(self.projected)
        except Exception:
            pass

        return {
            "average_clustering_coefficient": avg_clustering,
            "top_nodes_by_clustering": [
                {"node": node, "clustering": coeff,
                 "label": self.het_graph.get_node_info(node).get("label", node)}
                for node, coeff in sorted_clustering[:top_n]
            ],
            "clustering_distribution": self._distribution_stats(list(clustering_coeffs.values())),
            "triangles_per_node": {
                # 每个三角形被3个节点各计数一次，因此总三角形数需除以3
                "average": np.mean(list(triangles_per_node.values())) if triangles_per_node else 0,
                "total_triangles": sum(triangles_per_node.values()) // 3 if triangles_per_node else 0,
            },
            "square_clustering": {
                "average": np.mean(list(square_clustering.values())) if square_clustering else 0,
            },
        }

    def network_level_metrics(self) -> Dict[str, Any]:
        """
        网络级别宏观指标计算

        从全局视角评估网络的结构特征，包括：
        - 同配性（Assortativity）：高度节点是否倾向连接高度节点
        - 平均最短路径长度：反映网络的整体"大小"
        - 密度：边的稠密程度
        - 幂律指数：度分布是否符合无标度网络特征
        - 度序列：用于分析度分布模式

        Returns:
            Dict[str, Any]: 网络级指标，包含：
                - average_shortest_path_length: 平均最短路径长度
                - assortativity: 度-度相关性系数（正=同配，负=异配）
                - density: 网络密度
                - power_law_exponent: 幂律分布指数（若符合幂律）
                - degree_sequence: 降序排列的度序列（前20个）
        """
        n = self.projected.number_of_nodes()
        m = self.projected.number_of_edges()

        # 度同配性系数：衡量节点度的相关性
        # > 0 表示同配（高度节点连接高度节点）
        # < 0 表示异配（高度节点连接低度节点）
        # ≈ 0 表示无相关性
        assortativity = nx.degree_assortativity_coefficient(
            self.projected, weight="weight"
        ) if n > 1 else 0.0

        # 计算平均最短路径长度（优先在整个网络上计算，不连通则在最大连通分量上计算）
        try:
            if nx.is_connected(self.projected):
                avg_shortest_path = nx.average_shortest_path_length(
                    self.projected, weight="weight"
                )
            else:
                components = list(nx.connected_components(self.projected))
                largest_cc = max(components, key=len)
                subgraph = self.projected.subgraph(largest_cc)
                avg_shortest_path = nx.average_shortest_path_length(
                    subgraph, weight="weight"
                )
        except Exception:
            avg_shortest_path = 0.0

        # 度序列：将所有节点的度按降序排列
        degree_sequence = sorted([d for _, d in self.projected.degree()], reverse=True)
        # 统计每个度值出现的次数，用于度分布分析
        degree_count = defaultdict(int)
        for d in degree_sequence:
            degree_count[d] += 1
        # 提取度值和对应频次，按度值排序
        degs, counts = zip(*sorted(degree_count.items()))

        # 幂律指数估计：通过在对数坐标系中进行线性回归来估计
        # 若度分布 P(k) ∝ k^(-γ)，则 log(P(k)) 与 log(k) 呈线性关系
        # 斜率的负值即为幂律指数 γ
        if len(degs) > 1 and len(counts) > 1:
            try:
                # 对度值和频次取对数
                log_degs = np.log(degs)
                log_counts = np.log(counts)
                # 一阶多项式拟合（线性回归），得到斜率 slope
                slope, _ = np.polyfit(log_degs, log_counts, 1)
                # 幂律指数 γ = -slope（斜率通常为负）
                power_law_exponent = -slope
            except Exception:
                power_law_exponent = 0.0
        else:
            power_law_exponent = 0.0

        return {
            "average_shortest_path_length": avg_shortest_path,
            "assortativity": assortativity,
            # 无向图密度公式：2m / (n*(n-1))
            "density": 2 * m / (n * (n - 1)) if n > 1 else 0,
            "power_law_exponent": power_law_exponent,
            # 保留前20个度值用于可视化或进一步分析
            "degree_sequence": degree_sequence[:20],
        }

    def _top_centrality_nodes(self, centrality_dict: Dict[str, float],
                               top_n: int) -> List[Dict[str, Any]]:
        """
        提取中心性排名最高的前 N 个节点

        对中心性字典按值降序排列，并附带节点的标签信息。

        Args:
            centrality_dict: 节点到中心性值的映射字典
            top_n: 需要返回的节点数量

        Returns:
            List[Dict[str, Any]]: 排名前 N 的节点信息列表，
                每个元素包含节点ID、中心性值和标签
        """
        sorted_items = sorted(centrality_dict.items(), key=lambda x: x[1], reverse=True)
        return [
            {
                "node": node,
                "value": round(value, 6),
                "label": self.het_graph.get_node_info(node).get("label", node),
            }
            for node, value in sorted_items[:top_n]
        ]

    def _distribution_stats(self, values: List[float]) -> Dict[str, float]:
        """
        计算数值序列的分布统计量

        包括均值、标准差、最小值、最大值以及25/50/75百分位数。

        Args:
            values: 待分析的数值列表

        Returns:
            Dict[str, float]: 分布统计字典，包含：
                - mean: 均值
                - std: 标准差
                - min: 最小值
                - max: 最大值
                - p25: 第25百分位数（下四分位数）
                - p50: 第50百分位数（中位数）
                - p75: 第75百分位数（上四分位数）
        """
        if not values:
            return {"mean": 0, "std": 0, "min": 0, "max": 0,
                    "p25": 0, "p50": 0, "p75": 0}
        arr = np.array(values)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "p25": float(np.percentile(arr, 25)),
            "p50": float(np.percentile(arr, 50)),
            "p75": float(np.percentile(arr, 75)),
        }
