"""
文本数据加载器模块

本模块实现了 TextDataLoader 类，用于从非结构化文本中通过正则表达式
提取实体（人员、组织、地点、事件、文档、通信）和关系信息，构建网络图数据。

主要功能：
    - 从纯文本文件或字符串中解析结构化信息
    - 使用正则表达式匹配"键：值"格式的实体描述
    - 自动识别通信关系（如"A与B通信"）
    - 当无法直接提取关系时，通过共现分析推断隐含关系

文本格式示例：
    人员：张三
    单位：信息中心
    通信：张三 与 李四 发送
"""

import re
import json
from typing import Dict, Any
from .base_loader import BaseDataLoader
from config import DEFAULT_ENCODING


class TextDataLoader(BaseDataLoader):
    """
    文电文本数据加载器，从非结构化文本中提取实体与关系。

    通过预定义的正则表达式模式，识别文本中的人员、组织、地点、事件、
    文档和通信等实体信息，并尝试从中提取实体间的关系。
    当无法直接提取显式关系时，采用共现分析策略推断隐含关系。
    """

    def load(self, source: str) -> Dict[str, Any]:
        """
        从文本文件加载数据。

        读取指定路径的文本文件，使用默认编码解析内容后，
        调用内部解析方法提取实体和关系。

        参数：
            source: 文本文件路径

        返回：
            标准化后的数据字典
        """
        with open(source, "r", encoding=DEFAULT_ENCODING) as f:
            content = f.read()
        return self._parse_text(content)

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        验证文本解析后的数据格式。

        检查数据中是否包含 nodes 和 edges 键，且节点列表不为空。
        相比其他加载器，增加了节点数量检查，确保至少提取到一个有效实体。

        参数：
            data: 待验证的数据字典

        返回：
            数据格式是否合法
        """
        return "nodes" in data and "edges" in data and len(data["nodes"]) > 0

    def load_from_string(self, text: str) -> Dict[str, Any]:
        """
        从字符串直接加载数据。

        提供直接传入文本字符串的便捷接口，无需创建文件即可解析。

        参数：
            text: 待解析的文本字符串

        返回：
            标准化后的数据字典
        """
        return self._parse_text(text)

    def _parse_text(self, text: str) -> Dict[str, Any]:
        """
        核心文本解析方法。

        处理流程：
            1. 按空行将文本分割为多个条目（entry）
            2. 对每个条目使用正则表达式提取实体和关系
            3. 如果没有提取到显式关系，则通过共现分析推断隐含关系
            4. 对结果进行标准化处理

        参数：
            text: 待解析的完整文本

        返回：
            标准化后的数据字典，metadata 中包含来源类型和条目数量
        """
        nodes = []
        edges = []

        entries = self._split_entries(text)
        node_id_counter = 0

        for entry in entries:
            entry_nodes, entry_edges = self._parse_entry(entry, node_id_counter)
            nodes.extend(entry_nodes)
            edges.extend(entry_edges)
            node_id_counter += len(entry_nodes)

        if not edges:
            edges = self._infer_edges_from_cooccurrence(nodes, entries)

        return self.normalize({
            "nodes": nodes,
            "edges": edges,
            "metadata": {"source_type": "text", "entry_count": len(entries)},
        })

    def _split_entries(self, text: str) -> list:
        """
        将文本按空行分割为多个条目。

        使用正则表达式匹配连续的换行符（含空白字符）作为分隔符，
        过滤掉空白条目。

        参数：
            text: 待分割的原始文本

        返回：
            非空条目字符串列表
        """
        entries = re.split(r"\n\s*\n", text.strip())
        return [e.strip() for e in entries if e.strip()]

    def _parse_entry(self, entry: str, id_offset: int) -> tuple:
        """
        解析单个文本条目，提取实体节点和关系边。

        使用预定义的正则表达式模式识别以下六类实体：
            - 人员：匹配"人员/人物/联系人/发送者/接收者"关键字
            - 组织：匹配"单位/机构/组织/部门"关键字
            - 地点：匹配"地点/位置/地址"关键字
            - 事件：匹配"事件/活动/会议"关键字
            - 文档：匹配"文件/文档/编号"关键字
            - 通信：匹配"通信/联系/交互"关键字

        同时尝试识别"A与B通信"模式的显式关系。

        参数：
            entry: 单个文本条目字符串
            id_offset: 节点ID偏移量，用于避免不同条目间的ID冲突

        返回：
            元组 (节点列表, 边列表)
        """
        nodes = []
        edges = []

        person_pattern = r'(?:人员|人物|联系人|发送者|接收者)[：:]\s*([^\n，,。.]+)'
        org_pattern = r'(?:单位|机构|组织|部门)[：:]\s*([^\n，,。.]+)'
        location_pattern = r'(?:地点|位置|地址)[：:]\s*([^\n，,。.]+)'
        event_pattern = r'(?:事件|活动|会议)[：:]\s*([^\n，,。.]+)'
        doc_pattern = r'(?:文件|文档|编号)[：:]\s*([^\n，,。.]+)'
        communication_pattern = r'(?:通信|联系|交互)[：:]\s*([^\n，,。.]+)'

        node_id = id_offset

        persons = re.findall(person_pattern, entry)
        orgs = re.findall(org_pattern, entry)
        locations = re.findall(location_pattern, entry)
        events = re.findall(event_pattern, entry)
        docs = re.findall(doc_pattern, entry)
        comms = re.findall(communication_pattern, entry)

        for p in persons:
            nodes.append({"id": f"person_{node_id}", "type": "人员",
                          "label": p.strip(), "attributes": {"raw_text": entry}})
            node_id += 1
        for o in orgs:
            nodes.append({"id": f"org_{node_id}", "type": "组织",
                          "label": o.strip(), "attributes": {"raw_text": entry}})
            node_id += 1
        for l in locations:
            nodes.append({"id": f"loc_{node_id}", "type": "地点",
                          "label": l.strip(), "attributes": {"raw_text": entry}})
            node_id += 1
        for e in events:
            nodes.append({"id": f"event_{node_id}", "type": "事件",
                          "label": e.strip(), "attributes": {"raw_text": entry}})
            node_id += 1
        for d in docs:
            nodes.append({"id": f"doc_{node_id}", "type": "文档",
                          "label": d.strip(), "attributes": {"raw_text": entry}})
            node_id += 1
        for c in comms:
            nodes.append({"id": f"comm_{node_id}", "type": "通信",
                          "label": c.strip(), "attributes": {"raw_text": entry}})
            node_id += 1

        comm_pairs = re.findall(r'(\S+)\s*[与和跟同]\s*(\S+)\s*(?:通信|联系|交互|发送|接收)', entry)
        for src, tgt in comm_pairs:
            src_node = self._find_or_create_node(nodes, src, "人员", entry, id_offset)
            tgt_node = self._find_or_create_node(nodes, tgt, "人员", entry, id_offset)
            edges.append({
                "source": src_node["id"], "target": tgt_node["id"],
                "type": "通信", "weight": 1.0,
                "attributes": {"raw_text": entry},
                "source_type": "text",
            })

        return nodes, edges

    def _find_or_create_node(self, nodes, label, node_type, raw_text, id_offset):
        """
        在已有节点列表中查找指定标签的节点，若不存在则创建新节点。

        用于处理关系提取时，关系两端可能引用了尚未作为独立实体提取的对象。
        先在已有节点中按 label 匹配查找，找不到则创建一个新节点并加入列表。

        参数：
            nodes: 当前已有的节点列表
            label: 要查找/创建的节点标签
            node_type: 节点类型（如 "人员"、"组织" 等）
            raw_text: 原始文本，保存到节点属性中
            id_offset: 节点ID偏移量

        返回：
            匹配到或新创建的节点字典
        """
        for n in nodes:
            if n["label"] == label:
                return n
        new_id = f"{node_type}_{len(nodes) + id_offset}"
        node = {"id": new_id, "type": node_type, "label": label,
                "attributes": {"raw_text": raw_text}}
        nodes.append(node)
        return node

    def _infer_edges_from_cooccurrence(self, nodes, entries):
        """
        通过共现分析推断节点间的隐含关系。

        当正则表达式未能直接提取到显式关系时，采用以下两种策略推断关系：
            1. 人员-组织关联：若某人员和某组织源自同一条目文本，
               则推断二者存在"属于"关系（权重0.5）
            2. 跨条目关联：若不同条目中包含来自同一类型或不同类型的节点，
               则推断二者存在"相关"关系（权重0.3）

        使用 seen 集合避免生成重复的边。

        参数：
            nodes: 所有已提取的节点列表
            entries: 所有文本条目列表

        返回：
            推断出的边列表
        """
        edges = []
        person_nodes = [n for n in nodes if n["type"] == "人员"]
        org_nodes = [n for n in nodes if n["type"] == "组织"]

        seen = set()
        for p in person_nodes:
            for o in org_nodes:
                p_text = p.get("attributes", {}).get("raw_text", "")
                o_text = o.get("attributes", {}).get("raw_text", "")
                if p_text == o_text and p_text:
                    key = (p["id"], o["id"])
                    if key not in seen:
                        seen.add(key)
                        edges.append({
                            "source": p["id"], "target": o["id"],
                            "type": "属于", "weight": 0.5,
                            "attributes": {}, "source_type": "text",
                        })

        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                entry_i_nodes = [n for n in nodes
                                 if n.get("attributes", {}).get("raw_text", "") == entries[i]]
                entry_j_nodes = [n for n in nodes
                                 if n.get("attributes", {}).get("raw_text", "") == entries[j]]
                for ni in entry_i_nodes:
                    for nj in entry_j_nodes:
                        if ni["id"] != nj["id"]:
                            key = tuple(sorted([ni["id"], nj["id"]]))
                            if key not in seen:
                                seen.add(key)
                                edges.append({
                                    "source": ni["id"], "target": nj["id"],
                                    "type": "关联", "weight": 0.3,
                                    "attributes": {}, "source_type": "text",
                                })

        return edges
