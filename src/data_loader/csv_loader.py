"""
CSV数据加载器模块

本模块实现了 CSVDataLoader 类，用于从 CSV 格式的文件中解析并加载
网络图的节点和边数据。支持单文件加载和目录批量加载两种模式。

CSV数据格式识别策略：
    - 若CSV表头包含 "source" 和 "target" 列 → 边关系格式，
      自动从边数据中提取涉及的节点
    - 否则 → 节点列表格式，将每行数据解析为一个节点

示例表头格式（边关系格式）：
    source, target, type, weight, source_type, target_type

示例表头格式（节点列表格式）：
    id, type, label, ...
"""

import csv
import os
from typing import Dict, Any
from .base_loader import BaseDataLoader
from config import DEFAULT_ENCODING


class CSVDataLoader(BaseDataLoader):
    """
    CSV结构化数据加载器。

    从CSV文件中解析节点和边数据，自动根据表头列名判断数据格式，
    并转换为标准的节点-边结构。
    """

    def load(self, source: str) -> Dict[str, Any]:
        """
        加载CSV数据源。

        根据source参数判断是文件还是目录：
            - 若为目录：遍历目录下所有 .csv 文件，合并所有节点和边
            - 若为文件：直接加载单个CSV文件

        参数：
            source: CSV文件路径或包含CSV文件的目录路径

        返回：
            标准化后的数据字典
        """
        if os.path.isdir(source):
            nodes = []
            edges = []
            metadata = {}
            for filename in os.listdir(source):
                if filename.endswith(".csv"):
                    filepath = os.path.join(source, filename)
                    data = self._load_single_csv(filepath)
                    nodes.extend(data.get("nodes", []))
                    edges.extend(data.get("edges", []))
            return self.normalize({"nodes": nodes, "edges": edges, "metadata": metadata})
        else:
            data = self._load_single_csv(source)
            return self.normalize(data)

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证CSV解析后的数据格式。

        检查数据字典中是否同时包含 "nodes" 和 "edges" 键。

        参数：
            data: 待验证的数据字典

        返回：
            数据格式是否合法
        """
        return "nodes" in data and "edges" in data

    def _load_single_csv(self, filepath: str) -> Dict[str, Any]:
        """
        加载并解析单个CSV文件。

        解析流程：
            1. 读取CSV文件并获取表头信息
            2. 根据表头判断数据格式：
               - 边关系格式（含source和target列）：从边数据中自动提取节点
               - 节点列表格式：每行解析为一个节点，边列表为空
            3. 返回标准化的数据字典

        参数：
            filepath: CSV文件路径

        返回：
            包含 nodes、edges、metadata 的数据字典
        """
        nodes = []
        edges = []

        basename = os.path.splitext(os.path.basename(filepath))[0]

        with open(filepath, "r", encoding=DEFAULT_ENCODING) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            return {"nodes": [], "edges": []}

        headers = rows[0].keys()

        if "source" in headers and "target" in headers:
            nodes_set = {}
            for row in rows:
                src = row.get("source", "").strip()
                tgt = row.get("target", "").strip()
                etype = row.get("type", "关联").strip()
                weight = float(row.get("weight", 1.0))
                src_type = row.get("source_type", row.get("source_label", "未知")).strip()
                tgt_type = row.get("target_type", row.get("target_label", "未知")).strip()

                if src and src not in nodes_set:
                    nodes_set[src] = {
                        "id": src, "type": src_type, "label": src,
                        "attributes": {}, "source": basename,
                    }
                if tgt and tgt not in nodes_set:
                    nodes_set[tgt] = {
                        "id": tgt, "type": tgt_type, "label": tgt,
                        "attributes": {}, "source": basename,
                    }
                edges.append({
                    "source": src, "target": tgt, "type": etype,
                    "weight": weight, "attributes": {},
                    "source_type": "csv",
                })

            nodes = list(nodes_set.values())
        else:
            for i, row in enumerate(rows):
                node_id = row.get("id", row.get("name", f"node_{i}")).strip()
                node_type = row.get("type", row.get("label", "未知")).strip()
                nodes.append({
                    "id": node_id, "type": node_type, "label": node_id,
                    "attributes": {k: v for k, v in row.items()
                                   if k not in ("id", "name", "type", "label")},
                    "source": basename,
                })

        return {
            "nodes": nodes, "edges": edges,
            "metadata": {"source_type": "csv", "filename": basename},
        }
