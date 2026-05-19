"""
异构网络图核心模块。

本模块定义了 HeterogeneousGraph 类，用于表示和操作多源异构复杂网络。
基于 NetworkX 的 MultiDiGraph（多重有向图）实现，支持：
- 从标准化数据批量构建网络
- 异构网络到同构网络的投影
- 网络统计摘要信息生成
"""

import networkx as nx
from typing import Dict, Any, Optional, List, Tuple


class HeterogeneousGraph:
    """
    多源异构复杂网络图表示类。

    使用 NetworkX 的 MultiDiGraph（多重有向图）作为底层存储结构，
    支持在同一个图中包含多种节点和边。

    核心数据结构：
        - graph: NetworkX 多重有向图实例，存储所有节点和边

    Attributes:
        name: 网络名称标识
        graph: NetworkX MultiDiGraph 实例
    """

    def __init__(self, name: str = "heterogeneous_network"):
        """
        初始化异构图实例。

        Args:
            name: 网络名称，默认为 "heterogeneous_network"
        """
        self.name = name
        self.graph = nx.MultiDiGraph(name=name)

    def add_node(self, node_id: str, node_type: str = "未知",
                 label: str = "", attributes: Optional[Dict[str, Any]] = None,
                 source: str = "未知") -> None:
        """
        向图中添加一个节点。

        Args:
            node_id: 节点唯一标识符
            node_type: 节点类型，如 "单位" 等，默认为 "未知"
            label: 节点显示标签，若为空则使用 node_id 作为标签
            attributes: 节点附加属性字典，默认为空字典
            source: 节点数据来源标识，默认为 "未知"
        """
        self.graph.add_node(
            node_id,
            node_type=node_type,
            label=label or node_id,
            attributes=attributes or {},
            source=source,
        )

    def add_edge(self, source: str, target: str, edge_type: str = "关联",
                 weight: float = 1.0, attributes: Optional[Dict[str, Any]] = None,
                 source_type: str = "未知", receive_time: str = None) -> None:
        """
        向图中添加一条边（关系）。

        Args:
            source: 源节点ID
            target: 目标节点ID
            edge_type: 边类型，默认为 "关联"
            weight: 边权重，默认为 1.0
            attributes: 边附加属性字典，默认为空字典
            source_type: 数据来源类型标识，默认为 "未知"
            receive_time: 数据接收时间字符串，可选
        """
        edge_data = {
            "edge_type": edge_type,
            "weight": weight,
            "attributes": attributes or {},
            "source_type": source_type,
        }
        if receive_time:
            edge_data["receive_time"] = receive_time
        self.graph.add_edge(source, target, **edge_data)

    def build_from_normalized_data(self, data: Dict[str, Any]) -> None:
        """
        从标准化数据字典批量构建网络图。

        标准化数据格式要求：
            - nodes: 节点列表，每个节点包含 id, type, label 字段
            - edges: 边列表，每条边包含 source, target, type 字段
            - metadata: 元数据字典

        注意：只会添加两端节点均存在的边，跳过无效边。

        Args:
            data: 标准化数据字典，包含 "nodes"、"edges"、"metadata" 键
        """
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        metadata = data.get("metadata", {})

        # 第一阶段：批量添加所有节点
        for node in nodes:
            self.add_node(
                node_id=node["id"],
                node_type=node["type"],
                label=node["label"],
                attributes=node.get("attributes", {}),
                source=node.get("source", "未知"),
            )

        # 第二阶段：添加边（仅当源节点和目标节点均存在时才添加）
        for edge in edges:
            src = edge["source"]
            tgt = edge["target"]
            if src in self.graph and tgt in self.graph:
                self.add_edge(
                    source=src,
                    target=tgt,
                    edge_type=edge["type"],
                    weight=edge.get("weight", 1.0),
                    attributes=edge.get("attributes", {}),
                    source_type=edge.get("source_type", "未知"),
                    receive_time=edge.get("receive_time"),
                )

        # 将元数据存储到图的属性中
        self.graph.graph["metadata"] = metadata

    def get_node_count(self) -> int:
        """
        获取图中节点总数。

        Returns:
            节点数量
        """
        return self.graph.number_of_nodes()

    def get_edge_count(self) -> int:
        """
        获取图中边总数。

        Returns:
            边数量
        """
        return self.graph.number_of_edges()

    def get_node_info(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定节点的完整属性信息。

        Args:
            node_id: 节点ID

        Returns:
            节点属性字典（包含 node_type, label, attributes, source），
            若节点不存在则返回 None
        """
        if node_id in self.graph:
            return dict(self.graph.nodes[node_id])
        return None

    def get_adjacency_matrix(self) -> Any:
        """
        获取无向化后的邻接矩阵。

        将有向图转为无向图后生成邻接矩阵，用于图算法分析。

        Returns:
            SciPy 稀疏矩阵格式的邻接矩阵
        """
        return nx.adjacency_matrix(self.graph.to_undirected())

    def get_projected_graph(self, weight: str = "weight") -> nx.Graph:
        """
        将异构网络投影到同构网络上进行分析。

        保留所有节点和边，将多重有向图简化为简单无向图，
        合并相同节点对之间的边权重。

        Args:
            weight: 权重属性名，默认为 "weight"

        Returns:
            投影后的 NetworkX Graph（无向图）实例
        """
        projected = nx.Graph()
        for u, v, data in self.graph.edges(data=True):
            if not projected.has_edge(u, v):
                projected.add_edge(u, v, weight=data.get("weight", 1.0))
            else:
                projected[u][v]["weight"] = projected[u][v].get("weight", 0) + data.get("weight", 1.0)

        for node_id in self.graph.nodes():
            if node_id not in projected:
                projected.add_node(node_id, **self.graph.nodes[node_id])

        return projected

    @classmethod
    def _from_projected(cls, projected_graph: nx.Graph, name: str) -> "HeterogeneousGraph":
        """
        从投影图（同构图）反向构建 HeterogeneousGraph 实例。

        这是一个类方法（工厂方法），用于在投影分析后需要将结果
        重新封装为异构图对象的场景。

        Args:
            projected_graph: 投影后的 NetworkX Graph 实例
            name: 新网络的名称

        Returns:
            从投影图构建的 HeterogeneousGraph 实例
        """
        instance = cls(name=name)
        instance.graph = nx.MultiDiGraph(name=name)
        for node_id, node_data in projected_graph.nodes(data=True):
            instance.graph.add_node(node_id, **node_data)
        for u, v, data in projected_graph.edges(data=True):
            instance.graph.add_edge(u, v, **data)
        return instance

    def summary(self) -> Dict[str, Any]:
        """
        生成网络统计摘要信息。

        包含网络名称、节点数、边数、网络密度等。

        Returns:
            摘要信息字典，包含以下键：
                - name: 网络名称
                - node_count: 节点总数
                - edge_count: 边总数
                - density: 网络密度（0~1之间的浮点数）
        """
        return {
            "name": self.name,
            "node_count": self.get_node_count(),
            "edge_count": self.get_edge_count(),
            "density": nx.density(self.graph.to_undirected()),
        }
