"""
网络韧性/抗毁性分析模块

本模块提供了网络韧性与脆弱性的全面分析功能，包括：
- 韧性指标计算：自然连通度、代数连通度、谱半径、同配性、节点/边连通度等
- 脆弱性指标计算：割点与桥的识别、K-Core分解、节点脆弱性评估
- 攻击模拟：基于不同策略（介数/度/PageRank/随机）的节点移除对网络的影响
- 级联失效分析：模拟节点失效引发的连锁反应及传播路径
- 鲁棒性曲线：评估网络在不同攻击策略下的衰退曲线及鲁棒性排名

这些分析能够帮助理解网络在面对节点故障或恶意攻击时的抗毁能力，
为网络加固策略和容错设计提供量化依据。
"""

import networkx as nx
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import random

from src.network.heterogeneous_graph import HeterogeneousGraph
from config import ANALYSIS_CONFIG


class ResilienceAnalyzer:
    """
    网络韧性与脆弱性分析器

    通过多种互补的分析方法，全面评估异构信息网络在面对节点移除、
    故障和攻击时的结构稳定性和抗毁能力。分析范围涵盖基于图论的
    结构韧性指标、基于模拟的攻击与级联失效评估，以及鲁棒性曲线对比。

    Attributes:
        het_graph: 异构图对象，包含多类型节点和边
        projected: 异构图的投影图（无向加权图），作为分析的基础
    """

    def __init__(self, graph: HeterogeneousGraph):
        """
        初始化韧性分析器

        设置随机种子以确保模拟结果的可复现性。

        Args:
            graph: 异构图对象，提供底层网络数据及节点/边类型信息
        """
        self.het_graph = graph
        # 获取异构图的投影图（无向加权图），后续分析基于该投影图
        self.projected = graph.get_projected_graph()
        # 设置随机种子以确保攻击模拟等随机过程的结果可复现
        random.seed(ANALYSIS_CONFIG["random_seed"])
        np.random.seed(ANALYSIS_CONFIG["random_seed"])

    def analyze_all(self, simulation_iterations: int = None) -> Dict[str, Any]:
        """
        执行全量网络韧性分析

        依次调用所有子分析模块，汇总返回完整的网络韧性评估报告。

        Args:
            simulation_iterations: 攻击模拟的迭代次数，默认从配置文件读取

        Returns:
            Dict[str, Any]: 包含所有韧性分析结果的字典，键包括：
                - resilience_metrics: 韧性指标计算结果
                - vulnerability_metrics: 脆弱性指标计算结果
                - attack_simulation: 攻击模拟结果
                - cascading_failure_analysis: 级联失效分析结果
                - robustness_curves: 鲁棒性曲线分析结果
        """
        if simulation_iterations is None:
            simulation_iterations = ANALYSIS_CONFIG["simulation_iterations"]

        return {
            "resilience_metrics": self.resilience_metrics(),
            "vulnerability_metrics": self.vulnerability_metrics(),
            "attack_simulation": self.attack_simulation(simulation_iterations),
            "cascading_failure_analysis": self.cascading_failure_analysis(),
            "robustness_curves": self.robustness_curves(),
        }

    def resilience_metrics(self) -> Dict[str, Any]:
        """
        网络韧性指标计算

        从多个维度计算网络的结构韧性指标，综合反映网络在面对
        节点或边故障时的抗毁能力。

        主要指标说明：
        - 自然连通度：基于邻接矩阵特征值，反映网络的冗余连接程度
        - 代数连通度：拉普拉斯矩阵第二小特征值，反映网络的连通性强度
        - 谱半径：邻接矩阵最大特征值的绝对值，反映网络的活跃程度
        - 度同配性：高度节点与高度节点连接的倾向
        - 平均节点连通度：任意两节点间独立路径数的平均值
        - 边连通度：使网络不连通需要移除的最少边数
        - 度异质性：度分布的变异系数，反映网络度分布的不均匀程度

        Returns:
            Dict[str, Any]: 韧性指标字典，包含各项韧性指标及综合韧性评分
        """
        n = self.projected.number_of_nodes()
        m = self.projected.number_of_edges()

        if n < 2:
            return {"message": "节点数量不足，无法计算韧性指标"}

        # 自然连通度：基于邻接矩阵特征值的 e^λ 加权平均
        # 反映网络中替代路径的丰富程度，值越大表示韧性越强
        natural_connectivity = self._natural_connectivity()

        # 代数连通度（Fiedler值）：拉普拉斯矩阵的第二小特征值
        # 值越大表示网络连通性越强，越不容易被分裂
        # 仅在图连通时计算有意义
        if nx.is_connected(self.projected):
            algebraic_connectivity = nx.algebraic_connectivity(
                self.projected, weight="weight"
            )
        else:
            algebraic_connectivity = 0.0

        # 谱半径：邻接矩阵最大特征值的绝对值
        # 反映网络中信息/影响的传播速度
        try:
            spectral_radius = max(abs(e) for e in
                                  nx.adjacency_spectrum(self.projected, weight="weight"))
        except Exception:
            spectral_radius = 0.0

        # 度同配性系数：衡量高度节点是否倾向连接高度节点
        try:
            degree_assortativity = nx.degree_assortativity_coefficient(
                self.projected, weight="weight"
            )
        except Exception:
            degree_assortativity = 0.0

        # 平均节点连通度：任意两节点间独立路径数的平均值
        # 独立路径越多，网络越不容易因节点故障而断开
        try:
            avg_node_connectivity = nx.average_node_connectivity(self.projected)
        except Exception:
            avg_node_connectivity = 0.0

        # 边连通度：使网络不连通所需移除的最少边数
        try:
            avg_edge_connectivity = n / m if m > 0 else 0.0
            edge_connectivity = nx.edge_connectivity(self.projected)
        except Exception:
            edge_connectivity = 0
            avg_edge_connectivity = 0.0

        # 边密度：实际边数 / 最大可能边数
        edge_density = 2 * m / (n * (n - 1)) if n > 1 else 0

        # 度异质性：度分布的变异系数（标准差/均值）
        # 值越大表示网络度分布越不均匀，存在高度集线器节点
        degree_sequence = [d for _, d in self.projected.degree()]
        degree_variance = np.var(degree_sequence) if degree_sequence else 0.0
        degree_heterogeneity = np.sqrt(degree_variance) / max(np.mean(degree_sequence), 1e-10)

        return {
            "natural_connectivity": natural_connectivity,
            "algebraic_connectivity": algebraic_connectivity,
            "spectral_radius": spectral_radius,
            "degree_assortativity": degree_assortativity,
            "average_node_connectivity": avg_node_connectivity,
            "edge_connectivity": edge_connectivity,
            "edge_density": edge_density,
            "degree_heterogeneity": degree_heterogeneity,
            "is_connected": nx.is_connected(self.projected),
            "connected_components": nx.number_connected_components(self.projected),
            "resilience_score": self._compute_resilience_score(
                natural_connectivity, algebraic_connectivity,
                avg_node_connectivity, edge_density
            ),
        }

    def vulnerability_metrics(self) -> Dict[str, Any]:
        """
        网络脆弱性指标计算

        从多个维度评估网络的脆弱程度，识别网络中的结构性弱点。

        主要分析内容：
        - 割点（Articulation Points）：移除后导致网络不连通的关键节点
        - 桥（Bridges）：移除后导致网络不连通的关键边
        - K-Core分解：按核心度逐层剥离分析网络的层次结构
        - 节点脆弱性：通过模拟移除每个节点，量化其对网络的影响

        Returns:
            Dict[str, Any]: 脆弱性指标字典，包含：
                - articulation_points: 割点列表及数量
                - bridges: 桥列表及数量
                - k_core_decomposition: 各k-core层的节点数
                - node_vulnerability: 各节点的脆弱性评分
                - overall_vulnerability_score: 网络整体脆弱性评分
        """
        n = self.projected.number_of_nodes()
        if n < 2:
            return {"message": "节点数量不足"}

        # 记录原始网络的基准指标
        original_efficiency = self._global_efficiency(self.projected)
        original_components = nx.number_connected_components(self.projected)

        # 割点（Articulation Points）：移除后会使网络连通分量增加的节点
        # 这些节点是网络的"瓶颈"，其故障会导致网络分裂
        articulation_points = list(nx.articulation_points(self.projected)) if n > 0 else []

        # 桥（Bridges）：移除后会使网络连通分量增加的边
        # 这些边是网络中关键的"连接线"
        bridges = list(nx.bridges(self.projected)) if n > 0 else []

        # K-Core分解：核心度（Core Number）分析
        # k-core 是最大子图，其中每个节点的度都至少为 k
        # 核心度越高表示节点处于网络的越"核心"位置
        try:
            core_number = nx.core_number(self.projected)
        except Exception:
            core_number = {}

        # 按 k 值统计各层 k-core 中的节点数量
        try:
            k_core_decomposition = {}
            max_k = max(core_number.values()) if core_number else 0
            for k in range(1, max_k + 1):
                k_core = nx.k_core(self.projected, k)
                k_core_decomposition[k] = k_core.number_of_nodes()
        except Exception:
            k_core_decomposition = {}

        # 逐个模拟节点移除，计算每个节点对网络脆弱性的贡献
        node_vulnerability = {}
        for node in list(self.projected.nodes()):
            G_test = self.projected.copy()
            G_test.remove_node(node)

            # 效率下降比例：移除节点后网络效率的相对损失
            new_efficiency = self._global_efficiency(G_test)
            eff_drop = max(0, 1.0 - new_efficiency / max(original_efficiency, 1e-10))

            # 碎片化增量：移除节点后连通分量数量的相对增加
            new_components = nx.number_connected_components(G_test)
            frag_increase = (new_components - original_components) / max(n, 1)

            # 节点脆弱性 = 0.6 * 效率损失 + 0.4 * 碎片化增量
            node_vulnerability[node] = 0.6 * eff_drop + 0.4 * frag_increase

        # 按脆弱性降序排列
        sorted_vulnerability = sorted(node_vulnerability.items(),
                                      key=lambda x: x[1], reverse=True)

        return {
            "articulation_points_count": len(articulation_points),
            "articulation_points": [
                {
                    "node": ap,
                    "label": self.het_graph.get_node_info(ap).get("label", ap),
                    "type": self.het_graph.get_node_info(ap).get("node_type", "未知"),
                }
                for ap in articulation_points[:ANALYSIS_CONFIG["default_top_n"]]
            ],
            "bridges_count": len(bridges),
            "bridges": [
                {"source": u, "target": v} for u, v in list(bridges)[:ANALYSIS_CONFIG["default_top_n"]]
            ],
            "k_core_decomposition": k_core_decomposition,
            "max_k_core": max(core_number.values()) if core_number else 0,
            "node_vulnerability": {
                "top_nodes": [
                    {
                        "node": node,
                        "vulnerability": round(score, 6),
                        "label": self.het_graph.get_node_info(node).get("label", node),
                        "type": self.het_graph.get_node_info(node).get("node_type", "未知"),
                    }
                    for node, score in sorted_vulnerability[:ANALYSIS_CONFIG["default_top_n"]]
                ],
                "average_vulnerability": np.mean(list(node_vulnerability.values()))
                if node_vulnerability else 0,
            },
            # 网络整体脆弱性评分：所有节点脆弱性的平均值
            "overall_vulnerability_score": np.mean(list(node_vulnerability.values()))
            if node_vulnerability else 0,
        }

    def attack_simulation(self, iterations: int = 500) -> Dict[str, Any]:
        """
        攻击模拟：模拟不同策略下的节点移除对网络的影响

        通过模拟多种攻击策略（按介数中心性、度、PageRank排序的针对性攻击，
        以及随机攻击），逐步移除网络中的节点，观察网络在连通性和效率方面
        的衰退情况。

        这有助于评估网络在面对不同类型攻击时的脆弱程度差异：
        - 针对性攻击（targeted attack）：移除最重要的节点
        - 随机攻击（random attack）：模拟随机故障

        Args:
            iterations: 每种策略的模拟迭代次数，默认500

        Returns:
            Dict[str, Any]: 攻击模拟结果，包含：
                - strategies: 使用的攻击策略列表
                - remove_fractions: 节点移除比例序列
                - results: 各策略在不同移除比例下的网络状态
                - comparison: 各策略的平均效果对比
        """
        n = self.projected.number_of_nodes()
        if n < 5:
            return {"message": "节点数量不足，无法进行攻击模拟"}

        # 生成节点移除比例序列：从5%到100%
        remove_fractions = np.linspace(0.05, 1.0, min(20, max(1, n // 2)))
        # 从配置文件获取攻击策略列表
        strategies = ANALYSIS_CONFIG["attack_strategies"]

        # 对每种策略执行攻击模拟
        results = {}
        for strategy in strategies:
            strategy_results = self._simulate_attack_strategy(
                strategy, remove_fractions, iterations
            )
            results[strategy] = strategy_results

        return {
            "strategies": strategies,
            "remove_fractions": [round(f, 2) for f in remove_fractions],
            "results": results,
            "comparison": self._compare_strategies(results),
        }

    def cascading_failure_analysis(self) -> Dict[str, Any]:
        """
        级联失效分析

        模拟网络中级联失效的传播过程。当某个节点失效后，其负载会转移到
        邻居节点，如果邻居节点的负载超过其容量阈值，则会引发二次失效，
        依此类推形成级联效应。

        分析流程：
        1. 容量阈值分析：测试不同容量阈值下的级联失效规模
        2. 详细级联路径追踪：追踪特定触发节点的级联传播路径

        容量阈值 = multiplier × 平均度，multiplier 越小表示容量越小，
        网络越容易发生大规模级联失效。

        Returns:
            Dict[str, Any]: 级联失效分析结果，包含：
                - capacity_threshold_analysis: 不同阈值下的级联失效统计
                - detailed_cascades: 特定触发节点的详细级联信息
        """
        n = self.projected.number_of_nodes()
        if n < 2:
            return {"message": "节点数量不足"}

        # 测试不同的容量阈值乘数
        # 乘数越大表示节点容量越高，越不容易发生级联失效
        threshold_multipliers = [0.5, 0.75, 1.0, 1.25, 1.5]

        cascade_results = {}

        for multiplier in threshold_multipliers:
            # 计算平均度作为基准容量
            avg_capacity = np.mean([d for _, d in self.projected.degree()])
            # 为所有节点设置统一的容量阈值 = multiplier × 平均度
            thresholds = {}
            for node in self.projected.nodes():
                # 初始负载取节点的度值
                initial_load = self.projected.degree(node)
                # 容量阈值 = 乘数 × 平均度（统一容量模型）
                thresholds[node] = multiplier * avg_capacity

            # 对多个触发节点分别模拟级联失效
            total_failure_results = []
            for trigger_node in list(self.projected.nodes())[:min(20, n)]:
                failed_count = self._simulate_cascade(
                    trigger_node, thresholds
                )
                total_failure_results.append(failed_count)

            cascade_results[f"threshold_{multiplier}"] = {
                "avg_cascade_size": np.mean(total_failure_results),
                "max_cascade_size": max(total_failure_results),
                "min_cascade_size": min(total_failure_results),
            }

        # 对前5个节点进行详细的级联路径追踪
        initial_triggers = list(self.projected.nodes())[:min(5, n)]
        detailed_cascades = {}
        for trigger in initial_triggers:
            cascade_path = self._trace_cascade(trigger)
            detailed_cascades[trigger] = {
                "trigger_node": trigger,
                "label": self.het_graph.get_node_info(trigger).get("label", trigger),
                # 级联深度：失效传播经过的层级数
                "cascade_depth": len(cascade_path),
                # 受影响节点总数（去重后的唯一节点数）
                "affected_nodes": len(set(cascade_path)),
            }

        return {
            "capacity_threshold_analysis": cascade_results,
            "detailed_cascades": list(detailed_cascades.values()),
        }

    def robustness_curves(self) -> Dict[str, Any]:
        """
        鲁棒性曲线分析

        通过绘制网络在不同攻击策略下的"衰退曲线"来评估网络的鲁棒性。
        曲线横轴为节点移除比例，纵轴为最大连通分量（LCC）占原始网络的比例。

        对比三种攻击策略：
        1. 介数中心性针对性攻击：优先移除介数最高的节点
        2. 度针对性攻击：优先移除度最高的节点
        3. 随机攻击：随机顺序移除节点

        曲线下面积（AUC）越大表示网络在该攻击策略下越鲁棒。
        曲线下降越缓慢，说明网络对攻击的抵抗能力越强。

        Returns:
            Dict[str, Any]: 鲁棒性曲线分析结果，包含：
                - robustness_curves: 各策略在不同移除比例下的LCC占比
                - area_under_curve: 各策略曲线下的面积
                - robustness_ranking: 按AUC排序的鲁棒性排名
        """
        n = self.projected.number_of_nodes()
        if n < 5:
            return {"message": "节点数量不足"}

        # 按介数中心性降序排列（介数针对性攻击序列）
        betweenness = nx.betweenness_centrality(self.projected, weight="weight",
                                                 normalized=True)
        sorted_by_bc = sorted(betweenness, key=betweenness.get, reverse=True)

        # 按度降序排列（度针对性攻击序列）
        sorted_by_degree = sorted(self.projected.degree(), key=lambda x: x[1],
                                  reverse=True)
        sorted_by_degree = [node for node, _ in sorted_by_degree]

        # 随机排列（随机攻击序列）
        random_order = list(self.projected.nodes())
        random.shuffle(random_order)

        # 生成移除比例序列：从0到100%，共21个采样点
        fractions = np.linspace(0, 1.0, 21)

        # 对三种策略分别计算鲁棒性曲线
        curves = {}
        for label, order in [("betweenness_targeted", sorted_by_bc),
                              ("degree_targeted", sorted_by_degree),
                              ("random", random_order)]:
            curve_points = []
            for f in fractions:
                # 计算当前移除比例下需要移除的节点数
                remove_count = int(f * n)
                # 确定被移除的节点集合
                removed = set(order[:remove_count])

                # 获取剩余节点并构建子图
                remaining = [node for node in self.projected.nodes()
                             if node not in removed]
                subG = self.projected.subgraph(remaining)

                if subG.number_of_nodes() > 0:
                    # 找到最大连通分量
                    components = list(nx.connected_components(subG))
                    if components:
                        largest_component = max(components, key=len)
                        # LCC占比 = 最大连通分量节点数 / 原始网络节点数
                        lcc_ratio = len(largest_component) / n
                    else:
                        lcc_ratio = 0
                else:
                    lcc_ratio = 0

                curve_points.append({"fraction": round(f, 2), "lcc_ratio": round(lcc_ratio, 4)})

            curves[label] = curve_points

        # 计算各策略曲线下的面积（AUC）—— 鲁棒性的量化度量
        area_under_curves = {}
        for label, points in curves.items():
            try:
                # 使用梯形法则计算曲线下面积
                auc = np.trapezoid([p["lcc_ratio"] for p in points],
                                   [p["fraction"] for p in points])
            except AttributeError:
                # 兼容旧版 NumPy，回退到 scipy 的梯形积分
                from scipy import integrate
                auc = integrate.trapezoid([p["lcc_ratio"] for p in points],
                                          [p["fraction"] for p in points])
            area_under_curves[label] = round(float(auc), 4)

        return {
            "robustness_curves": curves,
            "area_under_curve": area_under_curves,
            # 按AUC降序排列，AUC越大表示网络在该策略下越鲁棒
            "robustness_ranking": sorted(area_under_curves.items(),
                                         key=lambda x: x[1], reverse=True),
        }

    def _natural_connectivity(self) -> float:
        """
        计算自然连通度作为网络韧性指标

        自然连通度基于邻接矩阵的特征值，通过计算 e^λ 的加权平均来衡量
        网络的冗余路径丰富程度。公式为：
        NC = ln( (1/n) × Σ e^(λ_i) )
        其中 λ_i 为邻接矩阵的第 i 个特征值。

        自然连通度越大，说明网络中有越多的替代路径，韧性越强。

        Returns:
            float: 自然连通度值
        """
        n = self.projected.number_of_nodes()
        if n < 2:
            return 0.0
        try:
            # 获取邻接矩阵的所有特征值
            eigenvalues = nx.adjacency_spectrum(self.projected)
            # 提取实部（理论上邻接矩阵的特征值应为实数）
            eigenvalues = [float(e.real) if hasattr(e, 'real') else float(e)
                           for e in eigenvalues]
            # 按降序排列
            eigenvalues.sort(reverse=True)
            # 计算 Σ e^(λ_i)
            total = sum(np.exp(e) for e in eigenvalues)
            # NC = ln( (1/n) × Σ e^(λ_i) )
            natural_conn = np.log(total / n) if total > 0 else 0.0
            return round(float(natural_conn), 6)
        except Exception:
            return 0.0

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

    def _compute_resilience_score(self, natural_connectivity: float,
                                   algebraic_connectivity: float,
                                   avg_node_connectivity: float,
                                   edge_density: float) -> float:
        """
        计算综合韧性评分

        将四个关键韧性指标归一化后加权融合，得到0~1的综合韧性评分。
        各指标先通过除以参考值归一化到 [0, 1] 范围，再按权重加总。

        加权策略：
        - 自然连通度（0.30）：反映网络的冗余路径丰富度
        - 代数连通度（0.25）：反映网络的连通性强度
        - 平均节点连通度（0.25）：反映网络的独立路径丰富度
        - 边密度（0.20）：反映网络的连接稠密程度

        Args:
            natural_connectivity: 自然连通度
            algebraic_connectivity: 代数连通度（Fiedler值）
            avg_node_connectivity: 平均节点连通度
            edge_density: 边密度

        Returns:
            float: 综合韧性评分，范围约 [0, 1]
        """
        # 各指标归一化：除以参考值并截断到 [0, 1]
        nc_norm = min(natural_connectivity / 5.0, 1.0)
        ac_norm = min(algebraic_connectivity / 5.0, 1.0)
        anc_norm = min(avg_node_connectivity / 3.0, 1.0)
        ed_norm = min(edge_density * 5, 1.0)

        # 加权融合
        score = 0.30 * nc_norm + 0.25 * ac_norm + 0.25 * anc_norm + 0.20 * ed_norm
        return round(score, 4)

    def _simulate_attack_strategy(self, strategy: str,
                                   remove_fractions: np.ndarray,
                                   iterations: int) -> Dict[str, Any]:
        """
        模拟单种攻击策略

        按指定策略对网络进行节点移除模拟，记录在每个移除比例下的
        最大连通分量占比和网络全局效率。

        支持的策略：
        - "betweenness": 按介数中心性降序移除
        - "degree": 按度降序移除
        - "pagerank": 按PageRank值降序移除
        - "random": 随机顺序移除（每次迭代重新随机）

        Args:
            strategy: 攻击策略名称
            remove_fractions: 节点移除比例数组
            iterations: 模拟迭代次数

        Returns:
            Dict[str, Any]: 各移除比例下的平均LCC占比和平均效率
        """
        n = self.projected.number_of_nodes()
        # 初始化结果容器：每个移除比例对应一个LCC和效率的列表
        results = {round(f, 2): {"lcc_ratio": [], "efficiency": []}
                   for f in remove_fractions}

        # 预先计算各中心性指标，用于排序攻击序列
        betweenness = nx.betweenness_centrality(self.projected, weight="weight",
                                                 normalized=True)
        degree_dict = dict(self.projected.degree())
        pagerank = nx.pagerank(self.projected, weight="weight")

        # 根据策略选择排序方式，确定节点移除顺序
        if strategy == "betweenness":
            sorted_nodes = sorted(betweenness, key=betweenness.get, reverse=True)
        elif strategy == "degree":
            sorted_nodes = sorted(degree_dict, key=degree_dict.get, reverse=True)
        elif strategy == "pagerank":
            sorted_nodes = sorted(pagerank, key=pagerank.get, reverse=True)
        else:
            sorted_nodes = list(self.projected.nodes())

        # 限制迭代次数以控制计算开销
        for _ in range(min(iterations, 50)):
            if strategy == "random":
                # 随机策略：每次迭代重新随机排列攻击顺序
                attack_order = list(self.projected.nodes())
                random.shuffle(attack_order)
            else:
                # 确定性策略：使用预设的排序
                attack_order = sorted_nodes

            G_current = self.projected.copy()
            for f in remove_fractions:
                # 计算当前比例下需要移除的节点数
                remove_count = int(f * n)
                removed_nodes = set(attack_order[:remove_count])

                # 获取剩余节点并构建子图
                remaining = [node for node in G_current.nodes()
                             if node not in removed_nodes]
                subG = G_current.subgraph(remaining)

                if subG.number_of_nodes() > 0:
                    # 计算最大连通分量占比
                    components = list(nx.connected_components(subG))
                    if components:
                        lcc = max(components, key=len)
                        lcc_ratio = len(lcc) / n
                    else:
                        lcc_ratio = 0
                    # 计算剩余网络的全局效率
                    eff = self._global_efficiency(subG)
                else:
                    lcc_ratio = 0
                    eff = 0

                results[round(f, 2)]["lcc_ratio"].append(lcc_ratio)
                results[round(f, 2)]["efficiency"].append(eff)

        # 汇总各比例下的统计结果（取所有迭代的均值）
        summary = {}
        for f, data in results.items():
            summary[f] = {
                "avg_lcc_ratio": round(np.mean(data["lcc_ratio"]), 4)
                if data["lcc_ratio"] else 0,
                "avg_efficiency": round(np.mean(data["efficiency"]), 6)
                if data["efficiency"] else 0,
            }

        return summary

    def _compare_strategies(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        对比不同攻击策略的整体效果

        汇总各策略在所有移除比例下的平均LCC占比和平均效率，
        用于横向对比不同策略对网络的破坏程度。

        Args:
            results: 各策略的攻击模拟结果

        Returns:
            Dict[str, Any]: 各策略的平均效果对比
        """
        comparison = {}
        for strategy, data in results.items():
            if isinstance(data, dict):
                # 提取各移除比例下的平均LCC占比和平均效率
                lcc_values = [v.get("avg_lcc_ratio", 0)
                              for v in data.values()
                              if isinstance(v, dict)]
                eff_values = [v.get("avg_efficiency", 0)
                              for v in data.values()
                              if isinstance(v, dict)]
                comparison[strategy] = {
                    # 均值越低表示该策略对网络的破坏越大
                    "mean_lcc_ratio": round(np.mean(lcc_values), 4) if lcc_values else 0,
                    "mean_efficiency": round(np.mean(eff_values), 6) if eff_values else 0,
                }
        return comparison

    def _simulate_cascade(self, trigger_node: str,
                           thresholds: Dict[str, float]) -> int:
        """
        模拟从指定触发节点开始的级联失效

        级联失效模型：
        1. 触发节点失效（被移除）
        2. 其负载转移到邻居节点
        3. 若任何节点的当前度（作为负载代理）超过其容量阈值，则该节点也失效
        4. 重复步骤2-3直到不再有新节点失效

        在本实现中，节点的"负载"以其当前度值作为代理，当度值超过
        容量阈值时触发失效。

        Args:
            trigger_node: 触发级联失效的初始节点
            thresholds: 各节点的容量阈值字典

        Returns:
            int: 级联失效导致的总失效节点数
        """
        G = self.projected.copy()
        # 记录已失效的节点集合
        failed = {trigger_node}
        failed_count = 1

        # 移除触发节点
        G.remove_node(trigger_node)

        # 迭代传播级联失效
        changed = True
        while changed:
            changed = False
            for node in list(G.nodes()):
                if node in failed:
                    continue
                # 检查节点的当前负载（以度值作为代理）是否超过容量阈值
                load = G.degree(node)
                if load > thresholds.get(node, float("inf")):
                    # 节点过载，加入失效集合
                    failed.add(node)
                    G.remove_node(node)
                    failed_count += 1
                    changed = True

        return failed_count

    def _trace_cascade(self, trigger_node: str) -> List[str]:
        """
        追踪级联失效的传播路径

        记录级联失效过程中失效节点的顺序，用于分析级联传播的范围和深度。
        使用更低的阈值（平均度的50%）作为失效判定条件。

        Args:
            trigger_node: 触发级联失效的初始节点

        Returns:
            List[str]: 失效节点的有序列表（按失效顺序排列）
        """
        G = self.projected.copy()
        # 计算网络的平均度作为参考阈值
        avg_degree = np.mean([d for _, d in G.degree()])

        failed = [trigger_node]
        G.remove_node(trigger_node)

        # 迭代传播：度值低于平均度50%的节点被视为失效
        changed = True
        while changed:
            changed = False
            for node in list(G.nodes()):
                if node in failed:
                    continue
                # 如果节点剩余度低于平均度的一半，视为失效
                if G.degree(node) < avg_degree * 0.5:
                    failed.append(node)
                    G.remove_node(node)
                    changed = True

        return failed
