"""
节点重要性分析模块

本模块提供了网络中节点重要度的多维度评估功能，包括：
- 综合重要度评估：融合度中心性、介数中心性、接近中心性、特征向量中心性和PageRank的加权综合评分
- 可替代程度分析：评估节点在网络中被其他节点替代的难易程度
- 结构洞分析：识别占据网络结构洞位置的关键"桥梁"节点
- 关键参与者分析：通过节点移除模拟评估节点对网络完整性的影响
- 脆弱性贡献分析：量化各节点对网络整体脆弱性的贡献程度

这些分析有助于识别网络中的关键节点，为网络优化、风险管理和
资源分配策略提供数据支持。
"""

import networkx as nx
import numpy as np
from typing import Dict, Any, List, Optional
from itertools import combinations

from src.network.heterogeneous_graph import HeterogeneousGraph
from config import ANALYSIS_CONFIG


class ImportanceAnalyzer:
    """
    节点重要度与可替代程度分析器

    通过多种互补的分析方法，从不同维度评估异构信息网络中每个节点的重要性。
    包括基于中心性的综合评分、结构洞占据能力、节点移除影响力模拟，
    以及基于邻居相似度和网络效率的替代难度评估。

    Attributes:
        het_graph: 异构图对象，包含多类型节点和边
        projected: 异构图的投影图（无向加权图），作为分析的基础
        _cache: 内部缓存字典，用于存储中间计算结果
    """

    def __init__(self, graph: HeterogeneousGraph):
        """
        初始化节点重要性分析器

        Args:
            graph: 异构图对象，提供底层网络数据及节点/边类型信息
        """
        self.het_graph = graph
        # 获取异构图的投影图（无向加权图），后续分析基于该投影图
        self.projected = graph.get_projected_graph()
        self._cache: Dict[str, Any] = {}

    def analyze_all(self, top_n: int = None) -> Dict[str, Any]:
        """
        执行全量节点重要性分析

        依次调用所有子分析模块，汇总返回完整的节点重要性评估报告。

        Args:
            top_n: 各分析模块返回排名前 N 的节点，默认从配置文件读取

        Returns:
            Dict[str, Any]: 包含所有重要性分析结果的字典，键包括：
                - comprehensive_importance: 综合重要度评估
                - substitutability: 可替代程度分析
                - structural_holes: 结构洞分析
                - key_player_analysis: 关键参与者分析
                - vulnerability_contribution: 脆弱性贡献分析
        """
        if top_n is None:
            top_n = ANALYSIS_CONFIG["default_top_n"]

        return {
            "comprehensive_importance": self.comprehensive_importance(top_n),
            "substitutability": self.substitutability_analysis(top_n),
            "structural_holes": self.structural_holes_analysis(top_n),
            "key_player_analysis": self.key_player_analysis(top_n),
            "vulnerability_contribution": self.vulnerability_contribution_analysis(top_n),
        }

    def comprehensive_importance(self, top_n: int = None) -> Dict[str, Any]:
        """
        综合重要度评估：融合多种中心性指标

        将度中心性、介数中心性、接近中心性、特征向量中心性和PageRank
        五种中心性指标进行加权融合，计算每个节点的综合重要度分数。

        加权策略：
        - 介数中心性（0.25）：权重最高，强调节点作为信息桥梁的作用
        - 度中心性（0.20）：衡量直接连接的广泛性
        - 特征向量中心性（0.20）：衡量与重要节点的连接质量
        - PageRank（0.20）：衡量基于随机游走的全局影响力
        - 接近中心性（0.15）：衡量信息传播的效率

        Args:
            top_n: 返回综合重要度排名前 N 的节点，默认从配置文件读取

        Returns:
            Dict[str, Any]: 综合重要度分析结果，包含：
                - top_important_nodes: 最重要节点列表（含各中心性原始值）
                - importance_distribution: 重要度分数分布统计
                - total_nodes_analyzed: 参与分析的节点总数
        """
        if top_n is None:
            top_n = ANALYSIS_CONFIG["default_top_n"]

        n = self.projected.number_of_nodes()

        # 分别计算五种中心性指标
        dc = nx.degree_centrality(self.projected) if n > 0 else {}
        bc = nx.betweenness_centrality(self.projected, weight="weight",
                                        normalized=True) if n > 1 else {}
        cc = nx.closeness_centrality(self.projected) if n > 1 else {}
        try:
            ec = nx.eigenvector_centrality_numpy(self.projected,
                                                  weight="weight") if n > 0 else {}
        except Exception:
            ec = nx.eigenvector_centrality(self.projected, weight="weight",
                                            max_iter=1000) if n > 0 else {}
        pr = nx.pagerank(self.projected, weight="weight") if n > 0 else {}

        # 加权融合计算综合重要度分数
        scores = {}
        for node in self.projected.nodes():
            if node in dc and node in bc and node in cc and node in ec and node in pr:
                # 五种中心性指标按权重加权求和
                scores[node] = (
                    0.20 * dc[node] +   # 度中心性权重
                    0.25 * bc[node] +   # 介数中心性权重（最高，强调桥梁作用）
                    0.15 * cc[node] +   # 接近中心性权重
                    0.20 * ec[node] +   # 特征向量中心性权重
                    0.20 * pr[node]     # PageRank权重
                )
            elif node in dc:
                # 降级处理：若部分指标缺失，仅使用度中心性
                scores[node] = dc[node]

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return {
            "top_important_nodes": [
                {
                    "node": node,
                    "comprehensive_score": round(score, 6),
                    "type": self.het_graph.get_node_info(node).get("node_type", "未知"),
                    "label": self.het_graph.get_node_info(node).get("label", node),
                    "degree_centrality": round(dc.get(node, 0), 6),
                    "betweenness_centrality": round(bc.get(node, 0), 6),
                    "closeness_centrality": round(cc.get(node, 0), 6),
                    "eigenvector_centrality": round(ec.get(node, 0), 6),
                    "pagerank": round(pr.get(node, 0), 6),
                }
                for node, score in sorted_scores[:top_n]
            ],
            "importance_distribution": self._distribution_stats(list(scores.values())),
            "total_nodes_analyzed": len(scores),
        }

    def substitutability_analysis(self, top_n: int = None) -> Dict[str, Any]:
        """
        节点可替代程度分析

        评估网络中每个节点被其他节点替代的难易程度。可替代性高的节点
        意味着其功能可由邻居节点承接，而可替代性低的节点则是网络中
        不可或缺的关键节点。

        评估维度（加权融合）：
        1. 邻居相似度（0.35）：基于介数中心性计算节点与邻居的相似程度
        2. 度比率（0.25）：节点度与邻居平均度的接近程度
        3. 连通性惩罚（0.15）：移除节点后是否导致网络分裂
        4. 效率保持率（0.25）：移除节点后网络全局效率的保持比例

        Args:
            top_n: 返回排名前 N 的节点，默认从配置文件读取

        Returns:
            Dict[str, Any]: 可替代程度分析结果，包含：
                - top_substitutable_nodes: 最容易被替代的节点列表
                - top_irreplaceable_nodes: 最难以被替代的节点列表
                - distribution: 可替代性分数分布统计
        """
        if top_n is None:
            top_n = ANALYSIS_CONFIG["default_top_n"]

        nodes = list(self.projected.nodes())
        if len(nodes) < 2:
            return {"substitutability_scores": [], "message": "节点数量不足，无法进行分析"}

        # 计算原始网络的介数中心性和全局效率，作为后续比较的基准
        bc_original = nx.betweenness_centrality(self.projected, weight="weight",
                                                 normalized=True)
        original_efficiency = self._global_efficiency(self.projected)

        substitutability_scores = {}
        for node in nodes:
            neighbors = list(self.projected.neighbors(node))
            # 孤立节点（无邻居）的可替代性为0
            if len(neighbors) < 1:
                substitutability_scores[node] = 0.0
                continue

            # 维度1：邻居相似度 —— 基于介数中心性衡量节点与邻居的相似程度
            # 若邻居的介数中心性与该节点接近，说明邻居能承担类似的中转功能
            neighbor_similarity = []
            for neighbor in neighbors:
                try:
                    neighbor_bc = bc_original.get(neighbor, 0)
                    node_bc = bc_original.get(node, 0)
                    max_bc = max(neighbor_bc, node_bc, 1e-10)
                    # 介数中心性相似度 = 1 - 归一化差异
                    bc_sim = 1.0 - abs(neighbor_bc - node_bc) / max_bc
                    neighbor_similarity.append(bc_sim)
                except Exception:
                    neighbor_similarity.append(0.0)

            avg_similarity = np.mean(neighbor_similarity) if neighbor_similarity else 0.0

            # 维度2：度比率 —— 节点度与邻居平均度的接近程度
            # min/max 归一化，值越接近1说明节点与邻居的能力越匹配
            degree = self.projected.degree(node)
            avg_degree = np.mean([self.projected.degree(n)
                                  for n in neighbors]) if neighbors else 0
            degree_ratio = min(degree, avg_degree) / max(degree, avg_degree, 1)

            # 维度3：连通性惩罚 —— 移除该节点后是否导致网络分裂为多个分量
            G_test = self.projected.copy()
            G_test.remove_node(node)

            if len(list(nx.connected_components(G_test))) > 1:
                # 移除后网络不连通，降低可替代性（该节点是割点）
                connectivity_penalty = 0.5
            else:
                # 移除后网络仍连通，不影响可替代性
                connectivity_penalty = 1.0

            # 维度4：效率保持率 —— 移除节点后网络效率的保持程度
            new_efficiency = self._global_efficiency(G_test)
            eff_ratio = new_efficiency / max(original_efficiency, 1e-10)

            # 加权融合四个维度得到最终可替代性分数
            substitutability = (
                0.35 * avg_similarity +       # 邻居相似度
                0.25 * degree_ratio +          # 度比率
                0.15 * connectivity_penalty +  # 连通性惩罚
                0.25 * eff_ratio               # 效率保持率
            )

            substitutability_scores[node] = substitutability

        # 按可替代性降序排列
        sorted_scores = sorted(substitutability_scores.items(), key=lambda x: x[1], reverse=True)

        return {
            # 可替代性最高的节点（最容易替代的）
            "top_substitutable_nodes": [
                {
                    "node": node,
                    "substitutability_score": round(score, 6),
                    "type": self.het_graph.get_node_info(node).get("node_type", "未知"),
                    "label": self.het_graph.get_node_info(node).get("label", node),
                }
                for node, score in sorted_scores[:top_n]
            ],
            # 可替代性最低的节点（最不可替代的，即最关键的）
            "top_irreplaceable_nodes": [
                {
                    "node": node,
                    "substitutability_score": round(score, 6),
                    "type": self.het_graph.get_node_info(node).get("node_type", "未知"),
                    "label": self.het_graph.get_node_info(node).get("label", node),
                }
                for node, score in sorted_scores[-top_n:] if sorted_scores
            ],
            "distribution": self._distribution_stats(list(substitutability_scores.values())),
        }

    def structural_holes_analysis(self, top_n: int = None) -> Dict[str, Any]:
        """
        结构洞分析：识别网络中占据结构洞位置的节点

        结构洞（Structural Hole）是指网络中两个互不连接的节点群体之间的间隙。
        占据结构洞位置的节点（"桥梁"节点）具有信息优势和控制优势：
        - 信息优势：能够更早获取非冗余信息
        - 控制优势：能够控制信息在不同群体之间的流动

        本方法使用两个互补指标：
        - 约束度（Constraint）：值越低表示节点的社交网络越多样化，
          即占据越多的结构洞（排序按升序，约束度低的排在前面）
        - 有效规模（Effective Size）：衡量节点的联系人网络的非冗余程度，
          值越高表示结构洞优势越大（排序按降序）

        Args:
            top_n: 返回排名前 N 的节点，默认从配置文件读取

        Returns:
            Dict[str, Any]: 结构洞分析结果，包含：
                - top_structural_hole_nodes: 约束度最低的节点（占据最多结构洞）
                - top_effective_size_nodes: 有效规模最大的节点（非冗余联系最多）
        """
        if top_n is None:
            top_n = ANALYSIS_CONFIG["default_top_n"]

        n = self.projected.number_of_nodes()
        if n < 3:
            return {"top_structural_hole_nodes": [], "message": "节点数量不足，无法进行结构洞分析"}

        # 约束度（Constraint）：衡量节点的社交资本被其联系人"约束"的程度
        # 低约束度 = 更多的结构洞机会 = 更大的信息/控制优势
        try:
            constraint = nx.constraint(self.projected)
        except Exception:
            constraint = {}

        # 有效规模（Effective Size）：节点实际可利用的非冗余联系数量
        # 等于节点的度减去其联系人之间的冗余连接
        try:
            effective_size = nx.effective_size(self.projected)
        except Exception:
            effective_size = {}

        # 约束度按升序排列（值越低越重要）
        sorted_constraint = sorted(constraint.items(), key=lambda x: x[1])
        # 有效规模按降序排列（值越高越重要）
        sorted_effective = sorted(effective_size.items(), key=lambda x: x[1], reverse=True)

        return {
            "top_structural_hole_nodes": [
                {
                    "node": node,
                    "constraint": round(c, 6),
                    "effective_size": round(effective_size.get(node, 0), 4),
                    "type": self.het_graph.get_node_info(node).get("node_type", "未知"),
                    "label": self.het_graph.get_node_info(node).get("label", node),
                }
                for node, c in sorted_constraint[:top_n]
            ],
            "top_effective_size_nodes": [
                {
                    "node": node,
                    "effective_size": round(es, 4),
                    "constraint": round(constraint.get(node, 1), 6),
                    "type": self.het_graph.get_node_info(node).get("node_type", "未知"),
                    "label": self.het_graph.get_node_info(node).get("label", node),
                }
                for node, es in sorted_effective[:top_n]
            ],
        }

    def key_player_analysis(self, top_n: int = None) -> Dict[str, Any]:
        """
        关键参与者分析：识别移除后对网络影响最大的节点

        通过模拟逐个移除网络中的节点，量化每个节点被移除后对网络结构
        造成的破坏程度。综合考量以下四个维度：

        1. 碎片化程度（0.30）：移除后增加的连通分量数量
        2. 效率损失（0.40）：移除后全局效率的下降幅度
        3. 孤立节点数（0.20）：移除后导致邻居变为孤立节点的比例
        4. 原始介数（0.10）：节点自身的介数中心性贡献

        Args:
            top_n: 返回影响最大的前 N 个节点，默认从配置文件读取

        Returns:
            Dict[str, Any]: 关键参与者分析结果，包含：
                - top_key_players: 对网络影响最大的节点列表
                - distribution: 影响力分数分布统计
        """
        if top_n is None:
            top_n = ANALYSIS_CONFIG["default_top_n"]

        # 记录原始网络的关键指标作为基准
        original_bc = nx.betweenness_centrality(self.projected, weight="weight",
                                                 normalized=True)
        original_efficiency = self._global_efficiency(self.projected)
        original_components = nx.number_connected_components(self.projected)

        impact_scores = {}
        for node in list(self.projected.nodes()):
            # 模拟移除当前节点
            G_test = self.projected.copy()
            G_test.remove_node(node)

            # 维度1：碎片化程度 —— 移除后增加的连通分量数量
            components_after = nx.number_connected_components(G_test)
            fragmentation = components_after - original_components

            # 维度2：效率损失 —— 移除后全局效率的下降量
            efficiency_after = self._global_efficiency(G_test)
            eff_loss = max(0, original_efficiency - efficiency_after)

            # 维度3：孤立节点数 —— 移除后度变为0的邻居节点数量
            nodes_isolated = 0
            for neighbor in self.projected.neighbors(node):
                if G_test.degree(neighbor) == 0:
                    nodes_isolated += 1

            # 综合影响分数：四个维度的加权融合
            impact = (
                0.30 * (fragmentation / max(self.projected.number_of_nodes(), 1)) +
                0.40 * (eff_loss / max(original_efficiency, 1e-10)) +
                0.20 * (nodes_isolated / max(self.projected.degree(node), 1)) +
                0.10 * original_bc.get(node, 0)
            )

            impact_scores[node] = impact

        sorted_scores = sorted(impact_scores.items(), key=lambda x: x[1], reverse=True)

        return {
            "top_key_players": [
                {
                    "node": node,
                    "impact_score": round(score, 6),
                    "type": self.het_graph.get_node_info(node).get("node_type", "未知"),
                    "label": self.het_graph.get_node_info(node).get("label", node),
                }
                for node, score in sorted_scores[:top_n]
            ],
            "distribution": self._distribution_stats(list(impact_scores.values())),
        }

    def vulnerability_contribution_analysis(self, top_n: int = None) -> Dict[str, Any]:
        """
        节点脆弱性贡献分析：各节点对网络脆弱性的贡献程度

        评估每个节点对网络整体脆弱性的贡献。通过模拟移除每个节点，
        观察网络在效率下降、最大连通分量缩小和碎片化加剧方面的变化，
        来量化各节点的脆弱性贡献。

        评估维度（加权融合）：
        1. 效率损失率（0.35）：移除后全局效率的相对下降比例
        2. 连通性损失（0.25）：最大连通分量占比的下降程度
        3. 碎片化增量（0.25）：连通分量数量的相对增加量
        4. 度占比（0.15）：节点度占全网络的相对比例

        Args:
            top_n: 返回脆弱性贡献最高的前 N 个节点，默认从配置文件读取

        Returns:
            Dict[str, Any]: 脆弱性贡献分析结果，包含：
                - top_vulnerability_contributors: 脆弱性贡献最高的节点列表
                - distribution: 脆弱性分数分布统计
        """
        if top_n is None:
            top_n = ANALYSIS_CONFIG["default_top_n"]

        n = self.projected.number_of_nodes()
        if n < 2:
            return {"top_vulnerable_nodes": [], "message": "节点数量不足"}

        # 记录原始网络的基准指标
        original_efficiency = self._global_efficiency(self.projected)
        original_components = nx.number_connected_components(self.projected)

        vulnerability_scores = {}
        for node in list(self.projected.nodes()):
            # 模拟移除当前节点
            G_test = self.projected.copy()
            G_test.remove_node(node)

            # 统计移除后的连通分量情况
            new_components = nx.number_connected_components(G_test)
            # 计算最大连通分量占移除后网络节点总数的比例
            largest_cc_ratio = 0
            if new_components > 0:
                components_list = list(nx.connected_components(G_test))
                if components_list:
                    largest_cc = max(components_list, key=len)
                    largest_cc_ratio = len(largest_cc) / G_test.number_of_nodes()

            # 维度1：效率损失率 —— 移除后效率的相对下降比例
            new_efficiency = self._global_efficiency(G_test)
            eff_loss = max(0, 1.0 - new_efficiency / max(original_efficiency, 1e-10))

            # 维度3：碎片化增量 —— 连通分量数量的相对增加
            frag_increase = (new_components - original_components) / max(n, 1)

            # 综合脆弱性贡献分数
            vulnerability = (
                0.35 * eff_loss +                                    # 效率损失率
                0.25 * (1.0 - largest_cc_ratio) +                   # 连通性损失
                0.25 * frag_increase +                              # 碎片化增量
                0.15 * (self.projected.degree(node) / max(n, 1))   # 度占比
            )

            vulnerability_scores[node] = vulnerability

        sorted_scores = sorted(vulnerability_scores.items(),
                               key=lambda x: x[1], reverse=True)

        return {
            "top_vulnerability_contributors": [
                {
                    "node": node,
                    "vulnerability_score": round(score, 6),
                    "type": self.het_graph.get_node_info(node).get("node_type", "未知"),
                    "label": self.het_graph.get_node_info(node).get("label", node),
                }
                for node, score in sorted_scores[:top_n]
            ],
            "distribution": self._distribution_stats(list(vulnerability_scores.values())),
        }

    def _global_efficiency(self, G: nx.Graph) -> float:
        """
        计算网络的全局效率

        全局效率衡量的是网络中节点间信息传递的平均效率。
        定义为所有节点对之间效率倒数的平均值：
        E_global = (1/(n*(n-1))) * Σ(1/d(i,j))
        其中 d(i,j) 为节点 i 到 j 的最短路径长度。

        Args:
            G: 待计算的 NetworkX 图对象

        Returns:
            float: 全局效率值，范围 [0, 1]
        """
        n = G.number_of_nodes()
        if n < 2:
            return 0.0
        try:
            return nx.global_efficiency(G)
        except Exception:
            # 降级计算：手动遍历所有节点对计算效率倒数均值
            total = 0.0
            count = 0
            for source, targets in nx.all_pairs_shortest_path_length(G):
                for target, dist in targets.items():
                    if source != target and dist > 0:
                        total += 1.0 / dist
                        count += 1
            return total / count if count > 0 else 0.0

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
                - p25: 第25百分位数
                - p50: 第50百分位数（中位数）
                - p75: 第75百分位数
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
