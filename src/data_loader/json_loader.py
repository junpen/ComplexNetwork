"""
JSON数据加载器模块

本模块实现了 JSONDataLoader 类，用于从 JSON 格式的文件中解析并加载
网络图的节点和边数据。支持单文件加载和目录批量加载两种模式。

支持的JSON数据格式：
    1. 标准格式：直接包含 "nodes" 和 "edges" 键的字典
    2. 列表格式：JSON数组，自动根据内容区分节点（含id字段）和边（含source/target字段）
    3. 字典分组格式：以类别名为键、对象列表为值的嵌套字典，类别名作为节点类型
"""

import json
import os
from typing import Dict, Any
from .base_loader import BaseDataLoader
from config import DEFAULT_ENCODING


class JSONDataLoader(BaseDataLoader):
    """
    JSON结构化数据加载器，支持单文件和目录批量加载。

    能够自动识别和处理多种常见的JSON数据格式，将其统一转换为
    标准的节点-边结构。
    """

    def load(self, source: str) -> Dict[str, Any]:
        """
        加载JSON数据源。

        根据source参数判断是文件还是目录：
            - 若为目录：遍历目录下所有 .json 文件，合并所有节点和边
            - 若为文件：直接加载单个JSON文件

        参数：
            source: JSON文件路径或包含JSON文件的目录路径

        返回：
            标准化后的数据字典
        """
        if os.path.isdir(source):
            all_nodes = []
            all_edges = []
            for filename in os.listdir(source):
                if filename.endswith(".json"):
                    filepath = os.path.join(source, filename)
                    data = self._load_single_json(filepath)
                    all_nodes.extend(data.get("nodes", []))
                    all_edges.extend(data.get("edges", []))
            return self.normalize({"nodes": all_nodes, "edges": all_edges,
                                   "metadata": {"source_type": "json_directory"}})
        else:
            data = self._load_single_json(source)
            return self.normalize(data)

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证JSON解析后的数据格式。

        检查数据字典中是否同时包含 "nodes" 和 "edges" 键。

        参数：
            data: 待验证的数据字典

        返回：
            数据格式是否合法
        """
        return "nodes" in data and "edges" in data

    def _load_single_json(self, filepath: str) -> Dict[str, Any]:
        """
        加载并解析单个JSON文件。

        自动识别JSON数据的格式并选择对应的解析策略：
            - 列表格式：调用 _parse_list_format() 处理
            - 标准字典格式（含nodes/edges键）：直接提取
            - 分组字典格式：调用 _parse_dict_format() 处理

        参数：
            filepath: JSON文件路径

        返回：
            包含 nodes、edges 的数据字典
        """
        with open(filepath, "r", encoding=DEFAULT_ENCODING) as f:
            data = json.load(f)

        if isinstance(data, list):
            return self._parse_list_format(data)
        elif isinstance(data, dict):
            if "nodes" in data or "edges" in data:
                return {
                    "nodes": data.get("nodes", []),
                    "edges": data.get("edges", []),
                    "metadata": data.get("metadata", {}),
                }
            else:
                return self._parse_dict_format(data)

        return {"nodes": [], "edges": []}

    def _parse_list_format(self, data: list) -> Dict[str, Any]:
        """
        解析列表格式的JSON数据。

        遍历列表中的每个字典元素，根据其包含的键自动分类：
            - 包含 "source" 和 "target" 键的元素 → 边
            - 包含 "id" 键的元素 → 节点
            - 其他元素 → 忽略

        参数：
            data: JSON列表数据

        返回：
            包含 nodes、edges 的数据字典
        """
        nodes = []
        edges = []

        for item in data:
            if not isinstance(item, dict):
                continue
            if "source" in item and "target" in item:
                edges.append(item)
            elif "id" in item:
                nodes.append(item)

        return {"nodes": nodes, "edges": edges}

    def _parse_dict_format(self, data: dict) -> Dict[str, Any]:
        """
        解析字典分组格式的JSON数据。

        将字典的每个键作为类别名（即节点类型），值列表中的每个元素
        根据内容分类为节点或边：
            - 包含 "source" 和 "target" 的元素 → 边（补充source_type）
            - 其他字典元素 → 节点（键名作为type，原始数据存入attributes）

        参数：
            data: JSON字典数据，键为类别名，值为对象列表

        返回：
            包含 nodes、edges 的数据字典
        """
        nodes = []
        edges = []

        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    if not isinstance(item, dict):
                        continue
                    if "source" in item and "target" in item:
                        item_copy = dict(item)
                        item_copy["source_type"] = item_copy.get("source_type", "json")
                        edges.append(item_copy)
                    else:
                        node = {"id": item.get("id", str(item)),
                                "type": key, "label": item.get("label", item.get("id", str(item))),
                                "attributes": item, "source": "json"}
                        nodes.append(node)

        return {"nodes": nodes, "edges": edges}
