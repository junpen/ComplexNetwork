"""
XML数据加载器模块

本模块实现了 XMLDataLoader 类，用于从 XML 格式的文件中解析并加载
网络图的节点和边数据。支持单文件加载和目录批量加载两种模式。

XML解析策略：
    - 优先使用 lxml 库（性能更好，功能更强）
    - 若 lxml 不可用，回退到标准库 xml.etree.ElementTree

支持的XML标签格式：
    - <node> 标签：标准节点格式，通过属性 id/type/label 描述节点
    - <edge> 标签：标准边格式，通过属性 source/target/type/weight 描述边
    - <entity> 标签：实体格式，兼容不同的实体表示方式
    - <relationship> 标签：关系格式，兼容不同的关系表示方式
"""

import os
from typing import Dict, Any, List
from .base_loader import BaseDataLoader
from config import DEFAULT_ENCODING

try:
    from lxml import etree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class XMLDataLoader(BaseDataLoader):
    """
    XML格式数据加载器。

    从XML文件中解析节点（node/entity）和边（edge/relationship）数据，
    支持单文件加载和目录下所有XML文件的批量加载。
    """

    def load(self, source: str) -> Dict[str, Any]:
        """
        加载XML数据源。

        根据source参数判断是文件还是目录：
            - 若为目录：遍历目录下所有 .xml 文件，合并所有节点和边
            - 若为文件：直接加载单个XML文件

        参数：
            source: XML文件路径或包含XML文件的目录路径

        返回：
            标准化后的数据字典
        """
        if os.path.isdir(source):
            all_nodes = []
            all_edges = []
            for filename in os.listdir(source):
                if filename.endswith(".xml"):
                    filepath = os.path.join(source, filename)
                    data = self._load_single_xml(filepath)
                    all_nodes.extend(data.get("nodes", []))
                    all_edges.extend(data.get("edges", []))
            return self.normalize({"nodes": all_nodes, "edges": all_edges,
                                   "metadata": {"source_type": "xml_directory"}})
        else:
            data = self._load_single_xml(source)
            return self.normalize(data)

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证XML解析后的数据格式。

        检查数据字典中是否同时包含 "nodes" 和 "edges" 键。

        参数：
            data: 待验证的数据字典

        返回：
            数据格式是否合法
        """
        return "nodes" in data and "edges" in data

    def _load_single_xml(self, filepath: str) -> Dict[str, Any]:
        """
        加载并解析单个XML文件。

        解析XML文件中的四种标签：
            1. <node> 标签 - 标准节点，子元素作为节点属性
            2. <edge> 标签 - 标准边关系
            3. <entity> 标签 - 实体节点，兼容不同的实体表示
            4. <relationship> 标签 - 关系边，兼容不同的关系表示

        参数：
            filepath: XML文件路径

        返回：
            包含 nodes、edges、metadata 的数据字典
        """
        tree = ET.parse(filepath)
        root = tree.getroot()

        nodes = []
        edges = []

        for node_elem in root.findall(".//node"):
            node_data = {
                "id": node_elem.get("id", ""),
                "type": node_elem.get("type", "未知"),
                "label": node_elem.get("label", node_elem.get("id", "")),
                "attributes": {},
                "source": "xml",
            }
            for child in node_elem:
                node_data["attributes"][child.tag] = child.text or ""
            nodes.append(node_data)

        for edge_elem in root.findall(".//edge"):
            edge_data = {
                "source": edge_elem.get("source", ""),
                "target": edge_elem.get("target", ""),
                "type": edge_elem.get("type", "关联"),
                "weight": float(edge_elem.get("weight", 1.0)),
                "attributes": {},
                "source_type": "xml",
            }
            edges.append(edge_data)

        for node_elem in root.findall(".//entity"):
            node_data = {
                "id": node_elem.get("id", node_elem.findtext("id", "")),
                "type": node_elem.tag if node_elem.tag != "entity"
                        else node_elem.get("type", "未知"),
                "label": node_elem.get("label",
                                       node_elem.findtext("name", node_elem.get("id", ""))),
                "attributes": {},
                "source": "xml",
            }
            nodes.append(node_data)

        for rel_elem in root.findall(".//relationship"):
            edge_data = {
                "source": rel_elem.get("source", rel_elem.findtext("source", "")),
                "target": rel_elem.get("target", rel_elem.findtext("target", "")),
                "type": rel_elem.get("type", rel_elem.findtext("type", "关联")),
                "weight": float(rel_elem.get("weight", 1.0)),
                "attributes": {},
                "source_type": "xml",
            }
            edges.append(edge_data)

        return {
            "nodes": nodes, "edges": edges,
            "metadata": {"source_type": "xml", "root_tag": root.tag},
        }
