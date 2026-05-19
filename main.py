#!/usr/bin/env python3
"""
多源异构数据复杂网络分析模型 - 主程序入口
===========================================

本模块是命令行模式下的主入口程序，用于直接在终端运行完整的网络分析流程。
与server.py的Web服务模式不同，本模块直接在控制台输出分析结果。

功能模块：
  1. 文电数据 → 多源异构复杂网络构建
  2. 网络特征指标分析（度、距离、介数、接近度、聚集系数等）
  3. 节点可替代程度与重要度分析
  4. 网络韧性与脆弱性分析

使用方式：
  python main.py              # 使用默认示例数据运行分析
  分析结果将输出到控制台，并可选导出为JSON文件
"""

import sys
import os

# 将当前脚本所在目录加入系统路径，确保可以正确引用本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.network import NetworkBuilder
from src.analysis import FeatureAnalyzer, ImportanceAnalyzer, ResilienceAnalyzer
from src.utils import export_to_json, print_section, print_subsection, format_number


def run_analysis(graph, output_dir: str = None):
    """执行完整的网络分析流程并输出结果到控制台。

    该函数依次执行四大分析模块：
      1. 网络概览 - 基本统计信息（节点数、边数、密度等）
      2. 网络特征指标分析 - 度分析、距离分析、中心性分析、聚集系数、网络级指标
      3. 节点重要度与可替代程度分析 - 综合重要度、可替代性、结构洞、关键参与者
      4. 网络韧性与脆弱性分析 - 韧性指标、脆弱性指标、攻击模拟、鲁棒性曲线

    Args:
        graph: 异构图对象（HeterogeneousGraph实例）
        output_dir: 分析结果JSON文件的输出目录，为None时不导出文件
    """
    # 如果指定了输出目录，确保目录存在
    os.makedirs(output_dir, exist_ok=True) if output_dir else None

    # ========== 第一部分：网络概览 ==========
    print_section("1. 网络概览")
    summary = graph.summary()
    print(f"  节点总数: {summary['node_count']}")
    print(f"  边总数:   {summary['edge_count']}")
    print(f"  网络密度: {format_number(summary['density'], 6)}")

    # ========== 第二部分：网络特征指标分析 ==========
    print_section("2. 网络特征指标分析")
    feature_analyzer = FeatureAnalyzer(graph)
    features = feature_analyzer.analyze_all()

    # 2.1 度分析：分析节点连接数的统计特征
    print_subsection("2.1 度分析")
    degree = features["degree_analysis"]
    print(f"  平均度: {format_number(degree['average_degree'])}")
    print(f"  最大度: {degree['max_degree']}")
    print(f"  度最高的节点 Top 5:")
    for item in degree["top_nodes_by_degree"][:5]:
        print(f"    {item['label']} ({item['type']}): 度={item['degree']}")

    # 2.2 距离分析：分析网络中节点间的最短路径特征
    print_subsection("2.2 距离分析")
    dist = features["distance_analysis"]
    print(f"  网络是否连通: {dist['is_connected']}")
    print(f"  平均最短路径: {format_number(dist['average_shortest_path_length'])}")
    print(f"  网络直径:     {dist['diameter']}")       # 网络中最长的最短路径
    print(f"  网络半径:     {dist['radius']}")         # 网络中最短的最长最短路径

    # 2.3 中心性分析：分析节点在网络中的重要性排名
    print_subsection("2.3 中心性分析")
    centrality = features["centrality_analysis"]
    # 遍历四种中心性指标，分别展示Top 3节点
    for key in ["degree_centrality", "betweenness_centrality",
                "closeness_centrality", "pagerank"]:
        top_nodes = centrality[key]["top_nodes"][:3]
        print(f"  {key} Top 3:")
        for item in top_nodes:
            print(f"    {item['label']} ({item['type']}): {format_number(item['value'])}")

    # 2.4 聚集系数分析：衡量节点邻居之间的连接紧密程度
    print_subsection("2.4 聚集系数分析")
    clustering = features["clustering_analysis"]
    print(f"  平均聚集系数: {format_number(clustering['average_clustering_coefficient'])}")
    print(f"  总三角形数:   {clustering['triangles_per_node']['total_triangles']}")

    # 2.5 网络级指标：整体网络结构特征
    print_subsection("2.5 网络级指标")
    net_metrics = features["network_level_metrics"]
    print(f"  同配性:         {format_number(net_metrics['assortativity'])}")        # 度-度相关性
    print(f"  幂律指数(估计): {format_number(net_metrics['power_law_exponent'])}")  # 度分布是否符合幂律

    # ========== 第三部分：节点重要度与可替代程度分析 ==========
    print_section("3. 节点重要度与可替代程度分析")
    importance_analyzer = ImportanceAnalyzer(graph)
    importance = importance_analyzer.analyze_all()

    # 3.1 综合重要度：综合多种中心性指标的加权排名
    print_subsection("3.1 综合重要度")
    comp_imp = importance["comprehensive_importance"]
    print("  综合重要度最高节点 Top 5:")
    for item in comp_imp["top_important_nodes"][:5]:
        print(f"    {item['label']} ({item['type']}): "
              f"综合={format_number(item['comprehensive_score'])}, "
              f"介数={format_number(item['betweenness_centrality'])}")

    # 3.2 可替代程度分析：评估节点被替换的难易程度
    print_subsection("3.2 可替代程度分析")
    subst = importance["substitutability"]
    print("  可替代程度最高节点 Top 3 (最易被替代):")
    for item in subst["top_substitutable_nodes"][:3]:
        print(f"    {item['label']} ({item['type']}): "
              f"可替代性={format_number(item['substitutability_score'])}")
    print("  不可替代节点 Top 3 (最难被替代):")
    for item in subst["top_irreplaceable_nodes"][:3]:
        print(f"    {item['label']} ({item['type']}): "
              f"可替代性={format_number(item['substitutability_score'])}")

    # 3.3 结构洞分析：识别处于网络信息桥梁位置的节点
    print_subsection("3.3 结构洞分析")
    sh = importance["structural_holes"]
    if "top_structural_hole_nodes" in sh and sh["top_structural_hole_nodes"]:
        print("  结构洞位置节点 Top 3:")
        for item in sh["top_structural_hole_nodes"][:3]:
            print(f"    {item['label']} ({item['type']}): "
                  f"约束={format_number(item['constraint'])}, "          # 约束系数越低，结构洞优势越大
                  f"有效规模={format_number(item['effective_size'])}")    # 有效规模越大，结构洞优势越大

    # 3.4 关键参与者分析：识别移除后对网络影响最大的节点
    print_subsection("3.4 关键参与者分析")
    kp = importance["key_player_analysis"]
    print("  关键参与者 Top 5 (移除后影响最大):")
    for item in kp["top_key_players"][:5]:
        print(f"    {item['label']} ({item['type']}): "
              f"影响分={format_number(item['impact_score'])}")

    # ========== 第四部分：网络韧性与脆弱性分析 ==========
    print_section("4. 网络韧性与脆弱性分析")
    resilience_analyzer = ResilienceAnalyzer(graph)
    resilience = resilience_analyzer.analyze_all()

    # 4.1 韧性指标：评估网络抵抗故障和攻击的能力
    print_subsection("4.1 韧性指标")
    res_metrics = resilience["resilience_metrics"]
    print(f"  自然连通度:     {format_number(res_metrics['natural_connectivity'])}")     # 反映网络冗余程度
    print(f"  代数连通度:     {format_number(res_metrics['algebraic_connectivity'])}")   # 反映网络同步能力
    print(f"  平均节点连通度: {format_number(res_metrics['average_node_connectivity'])}") # 节点对之间的独立路径数
    print(f"  边连通度:       {res_metrics['edge_connectivity']}")                       # 最小割边数
    print(f"  网络是否连通:   {res_metrics['is_connected']}")
    print(f"  连通分量数:     {res_metrics['connected_components']}")
    print(f"  综合韧性评分:   {format_number(res_metrics['resilience_score'])}")

    # 4.2 脆弱性指标：识别网络中的薄弱环节
    print_subsection("4.2 脆弱性指标")
    vul_metrics = resilience["vulnerability_metrics"]
    print(f"  关节点数量:     {vul_metrics['articulation_points_count']}")   # 移除后会导致网络分裂的节点
    print(f"  桥接边数量:     {vul_metrics['bridges_count']}")               # 移除后会导致网络分裂的边
    print(f"  最大K-core:     {vul_metrics['max_k_core']}")                  # 最大k核的k值
    print(f"  总体脆弱性评分: {format_number(vul_metrics['overall_vulnerability_score'])}")

    # 展示脆弱性贡献最高的节点
    if "node_vulnerability" in vul_metrics:
        print("  脆弱性贡献最高节点 Top 3:")
        for item in vul_metrics["node_vulnerability"]["top_nodes"][:3]:
            print(f"    {item['label']} ({item['type']}): "
                  f"脆弱性={format_number(item['vulnerability'])}")

    # 4.3 攻击模拟：模拟不同攻击策略对网络连通性的影响
    print_subsection("4.3 攻击模拟")
    attack = resilience["attack_simulation"]
    if "comparison" in attack:
        print("  不同攻击策略下的网络表现对比:")
        for strategy, data in attack["comparison"].items():
            print(f"    {strategy}: 平均LCC比率={format_number(data['mean_lcc_ratio'])}, "
                  f"平均效率={format_number(data['mean_efficiency'])}")

    # 4.4 鲁棒性曲线：通过AUC指标评估不同攻击策略的效果
    print_subsection("4.4 鲁棒性曲线")
    robustness = resilience["robustness_curves"]
    if "robustness_ranking" in robustness:
        print("  鲁棒性排序 (AUC越大越鲁棒):")
        for strategy, auc in robustness["robustness_ranking"]:
            print(f"    {strategy}: AUC={format_number(auc)}")

    # 如果指定了输出目录，将三个分析模块的结果分别导出为JSON文件
    if output_dir:
        export_to_json(features, os.path.join(output_dir, "features.json"))
        export_to_json(importance, os.path.join(output_dir, "importance.json"))
        export_to_json(resilience, os.path.join(output_dir, "resilience.json"))
        print(f"\n分析结果已导出到: {output_dir}")

    print_section("分析完成")


def main():
    """主函数：加载数据并执行完整的网络分析流程。

    数据加载策略：
      1. 优先加载本地示例数据文件 (data/sample_data.json)
      2. 如果示例文件不存在，使用内置的演示文本数据构建小型网络
    """
    # 构建示例数据文件的路径
    sample_data_path = os.path.join(os.path.dirname(__file__),
                                    "data", "sample_data.json")

    if not os.path.exists(sample_data_path):
        # 示例数据文件不存在，使用内置演示数据
        print(f"[错误] 未找到示例数据文件: {sample_data_path}")
        builder = NetworkBuilder(name="demo_network")

        print("使用内置示例数据演示...")
        # 内置的演示文本数据，包含人员、单位、地点、通信、事件等实体和关系
        demo_text = """
人员：张三
单位：研发部
地点：北京总部
通信：张三 与 李四 通信
事件：技术研讨会

人员：李四
单位：研发部
地点：北京总部
通信：李四 与 王五 通信

人员：王五
单位：测试中心
地点：上海分部
通信：王五 与 张三 通信

人员：赵六
单位：产品部
地点：深圳分部
通信：赵六 与 张三 通信

人员：孙七
单位：研发部
地点：北京总部
通信：孙七 与 李四 通信
"""

        # 从文本内容解析构建网络图
        graph = builder.build_from_text(demo_text)
    else:
        # 从JSON文件加载示例数据
        print(f"加载示例数据: {sample_data_path}")
        builder = NetworkBuilder(name="sample_network")
        graph = builder.build_from_source(sample_data_path, source_type="json")

    # 设置输出目录并执行分析
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    run_analysis(graph, output_dir)


if __name__ == "__main__":
    main()
