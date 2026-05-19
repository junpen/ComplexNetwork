"""
数据加载器基类模块

本模块定义了所有数据加载器的抽象基类 BaseDataLoader，为不同格式的数据源
（XML、JSON、CSV、纯文本等）提供统一的数据加载接口和标准化处理流程。

主要功能：
    - 定义数据加载的抽象接口（load、validate）
    - 提供节点和边的提取方法（extract_nodes、extract_edges）
    - 提供数据格式标准化方法（normalize），将不同来源的数据统一为
      标准的节点-边结构

标准化后的数据结构包含：
    - nodes: 节点列表，每个节点包含 id、type、label、attributes、source
    - edges: 边列表，每条边包含 source、target、type、weight、attributes、source_type
    - metadata: 元数据字典
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseDataLoader(ABC):
    """
    数据加载器抽象基类，定义文电数据加载的统一接口。

    所有具体的数据加载器（XML、JSON、CSV、文本等）都必须继承此类，
    并实现 load() 和 validate() 两个抽象方法。本类还提供了
    extract_nodes()、extract_edges() 和 normalize() 等通用方法，
    子类可以直接复用或按需重写。
    """

    @abstractmethod
    def load(self, source: str) -> Dict[str, Any]:
        """
        加载数据源，返回标准化的节点与边数据。

        子类必须实现此方法，根据不同的数据格式解析数据源。

        参数：
            source: 数据源路径，可以是文件路径或目录路径

        返回：
            包含 nodes、edges、metadata 的标准化字典
        """
        pass

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证数据格式是否符合要求。

        子类必须实现此方法，检查解析后的数据是否包含必要的字段。

        参数：
            data: 待验证的数据字典

        返回：
            数据格式是否合法的布尔值
        """
        pass

    def extract_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从原始数据中提取节点列表。

        参数：
            data: 包含 "nodes" 键的数据字典

        返回：
            节点列表，若不存在 "nodes" 键则返回空列表
        """
        return data.get("nodes", [])

    def extract_edges(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从原始数据中提取边列表。

        参数：
            data: 包含 "edges" 键的数据字典

        返回：
            边列表，若不存在 "edges" 键则返回空列表
        """
        return data.get("edges", [])

    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化数据格式。

        将不同来源的原始数据统一转换为标准的节点-边结构，
        对缺失字段填充默认值，确保输出格式一致。

        节点标准化后的字段：
            - id: 节点唯一标识（默认空字符串）
            - type: 节点类型（默认"未知"）
            - label: 节点显示标签（默认使用 id 值）
            - attributes: 节点附加属性（默认空字典）
            - source: 数据来源标识（默认"未知"）

        边标准化后的字段：
            - source: 起始节点 id（默认空字符串）
            - target: 目标节点 id（默认空字符串）
            - type: 边类型（默认"关联"）
            - weight: 边权重（默认 1.0）
            - attributes: 边附加属性（默认空字典）
            - source_type: 数据来源类型（默认"未知"）

        参数：
            data: 包含 nodes 和 edges 的原始数据字典

        返回：
            标准化后的数据字典，包含 nodes、edges、metadata
        """
        nodes = self.extract_nodes(data)
        edges = self.extract_edges(data)

        normalized_nodes = []
        for node in nodes:
            normalized_nodes.append({
                "id": node.get("id", ""),
                "type": node.get("type", "未知"),
                "label": node.get("label", node.get("id", "")),
                "attributes": node.get("attributes", {}),
                "source": node.get("source", "未知"),
            })

        normalized_edges = []
        for edge in edges:
            normalized_edges.append({
                "source": edge.get("source", ""),
                "target": edge.get("target", ""),
                "type": edge.get("type", "关联"),
                "weight": float(edge.get("weight", 1.0)),
                "attributes": edge.get("attributes", {}),
                "source_type": edge.get("source_type", "未知"),
            })

        return {
            "nodes": normalized_nodes,
            "edges": normalized_edges,
            "metadata": data.get("metadata", {}),
        }
