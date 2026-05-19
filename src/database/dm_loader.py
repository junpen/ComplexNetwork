"""
达梦数据库数据加载器模块。

本模块定义了 DMDataLoader 类，负责从达梦数据库的 NETWORK_EDGES 表中
加载网络边数据，并自动提取节点信息，构建标准化的网络数据格式。

主要功能：
- 从数据库边表加载网络数据，支持按时间范围过滤
- 自动从边数据中提取唯一节点
- 支持"各战区"等聚合目标的展开（拆分为5个具体战区）
- 提供边数据的插入、清空、统计等数据库操作
"""

import json
import logging
from typing import Dict, Any, List, Optional

from .dm_manager import db, DM_AVAILABLE
from config import DM_DATABASE

logger = logging.getLogger(__name__)

# 五大战区名称常量，用于展开"各战区"聚合目标
THEATER_COMMANDS = ["中部战区", "北部战区", "东部战区", "南部战区", "西部战区"]


class DMDataLoader:
    """
    达梦数据库数据加载器。

    负责从达梦数据库的 NETWORK_EDGES 表中读取网络边数据，
    并从中提取节点信息，输出为标准化格式的网络数据。

    数据流程：
        数据库 NETWORK_EDGES 表 -> 查询边数据 -> 展开聚合目标 ->
        解析属性JSON -> 提取节点 -> 输出标准化数据

    Attributes:
        schema: 数据库模式（Schema）名称，从配置文件读取
    """

    def __init__(self):
        """
        初始化数据加载器，从配置文件读取数据库模式名。
        """
        self.schema = DM_DATABASE["schema"]

    def is_available(self) -> bool:
        """
        检查达梦数据库驱动是否可用。

        Returns:
            True 表示可用，False 表示不可用
        """
        return DM_AVAILABLE

    def load_from_edges(self, start_time: str = None, end_time: str = None) -> Dict[str, Any]:
        """
        从数据库边表加载网络数据。

        从 NETWORK_EDGES 表中查询边数据，并从中自动提取所有唯一节点。
        支持按时间范围过滤边数据。

        Args:
            start_time: 起始时间过滤条件，仅加载 RECEIVE_TIME >= start_time 的边，默认不限
            end_time: 结束时间过滤条件，仅加载 RECEIVE_TIME < end_time 的边，默认不限

        Returns:
            标准化网络数据字典，格式为：
            {
                "nodes": [{"id": ..., "type": ..., "label": ..., "attributes": ..., "source": ...}, ...],
                "edges": [{"source": ..., "target": ..., "type": ..., "weight": ..., ...}, ...]
            }

        Raises:
            RuntimeError: dmPython 未安装时抛出
        """
        if not DM_AVAILABLE:
            raise RuntimeError("dmPython未安装，无法从数据库加载")

        logger.info("从DM数据库边表加载网络数据...")
        if start_time or end_time:
            logger.info(f"时间范围过滤: {start_time or '不限'} ~ {end_time or '不限'}")

        # 第一步：加载边数据
        edges = self._load_edges(start_time=start_time, end_time=end_time)
        # 第二步：从边数据中提取所有唯一节点
        nodes = self._extract_nodes_from_edges(edges)
        logger.info(f"从边表提取 {len(nodes)} 个唯一节点, {len(edges)} 条边")

        return {
            "nodes": nodes,
            "edges": edges,
        }

    def _expand_targets(self, target_str: str) -> List[str]:
        """
        展开聚合目标节点。

        数据库中的 TARGET_NODE 字段可能包含聚合目标（如"各战区"），
        使用中文顿号（"、"）分隔。本方法将其拆分并展开为具体节点列表。

        例如：
            "指挥员_张三" -> ["指挥员_张三"]
            "各战区" -> ["中部战区", "北部战区", "东部战区", "南部战区", "西部战区"]
            "中部战区、北部战区" -> ["中部战区", "北部战区"]

        Args:
            target_str: 目标节点字符串，可能包含多个目标（顿号分隔）

        Returns:
            展开后的目标节点列表
        """
        # 按中文顿号（、）拆分，并去除空白项
        parts = [p.strip() for p in target_str.split("\u3001") if p.strip()]
        expanded = []
        for part in parts:
            if part == "各战区":
                # "各战区" 展开为五大战区
                expanded.extend(THEATER_COMMANDS)
            else:
                expanded.append(part)
        return expanded

    def _load_edges(self, start_time: str = None, end_time: str = None) -> List[Dict[str, Any]]:
        """
        从数据库 NETWORK_EDGES 表加载边数据。

        构建带可选时间过滤条件的 SQL 查询，执行后将每行结果转换为
        标准化的边数据字典。支持聚合目标的自动展开（如"各战区"）。

        Args:
            start_time: 可选的起始时间过滤条件
            end_time: 可选的结束时间过滤条件

        Returns:
            边数据字典列表，每条边包含 source, target, type, weight, attributes, source_type 等字段
        """
        # 构建带 schema 前缀的基础查询 SQL
        sql = f"""
            SELECT SOURCE_NODE, TARGET_NODE, EDGE_TYPE, WEIGHT, ATTRIBUTES, SOURCE_TYPE, RECEIVE_TIME
            FROM {self.schema}.NETWORK_EDGES
        """
        # 动态构建 WHERE 条件子句
        conditions = []
        params = []
        if start_time:
            conditions.append("RECEIVE_TIME >= :1")
            params.append(start_time)
        if end_time:
            # 参数索引根据已有的参数数量动态计算
            param_idx = len(params) + 1
            conditions.append(f"RECEIVE_TIME < :{param_idx}")
            params.append(end_time)

        # 拼接 WHERE 子句
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY EDGE_ID"

        # 执行查询，若带 schema 的查询失败则尝试不带 schema 的表名
        try:
            rows = db.execute_query(sql, tuple(params) if params else None)
        except Exception as e:
            logger.warning(f"查询边表失败(尝试无schema): {e}")
            # 回退方案：不带 schema 前缀的表名
            sql = ("SELECT SOURCE_NODE, TARGET_NODE, EDGE_TYPE, WEIGHT, "
                   "ATTRIBUTES, SOURCE_TYPE, RECEIVE_TIME FROM NETWORK_EDGES ORDER BY EDGE_ID")
            rows = db.execute_query(sql)

        # 将查询结果逐行转换为标准化边数据
        edges = []
        for row in rows:
            # 解析 ATTRIBUTES 字段（JSON 字符串 -> 字典）
            attrs = row.get("ATTRIBUTES", "{}")
            if isinstance(attrs, str):
                try:
                    attrs = json.loads(attrs)
                except Exception:
                    attrs = {}
            elif attrs is None:
                attrs = {}

            source = row["SOURCE_NODE"]
            raw_target = row["TARGET_NODE"]
            # 展开聚合目标（如 "各战区" -> 五个具体战区）
            targets = self._expand_targets(raw_target)

            # 处理接收时间字段
            receive_time = row.get("RECEIVE_TIME")
            if receive_time is not None:
                receive_time = str(receive_time)

            # 为每个目标节点生成一条边记录
            for tgt in targets:
                edge_dict = {
                    "source": source,
                    "target": tgt,
                    "type": row["EDGE_TYPE"],
                    "weight": float(row.get("WEIGHT", 1.0)),
                    "attributes": attrs,
                    "source_type": row.get("SOURCE_TYPE", "database"),
                }
                if receive_time:
                    edge_dict["receive_time"] = receive_time
                edges.append(edge_dict)
        return edges

    def _extract_nodes_from_edges(self, edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从边数据中提取所有唯一节点。

        遍历所有边的 source 和 target 字段，收集唯一节点，
        所有节点统一标记为"单位"类型。

        Args:
            edges: 边数据列表

        Returns:
            节点数据列表，每个节点包含 id, type, label, attributes, source 字段
        """
        seen_ids: Dict[str, Dict[str, Any]] = {}

        for edge in edges:
            src = edge["source"]
            tgt = edge["target"]

            if src and src not in seen_ids:
                seen_ids[src] = {
                    "id": src,
                    "type": "单位",
                    "label": self._make_label(src),
                    "attributes": {},
                    "source": "database",
                }

            if tgt and tgt not in seen_ids:
                seen_ids[tgt] = {
                    "id": tgt,
                    "type": "单位",
                    "label": self._make_label(tgt),
                    "attributes": {},
                    "source": "database",
                }

        return list(seen_ids.values())

    def _make_label(self, node_id: str) -> str:
        """
        根据节点ID生成显示标签。

        当前实现直接使用节点ID作为标签，后续可扩展为
        去除前缀等更友好的标签生成逻辑。

        Args:
            node_id: 节点ID字符串

        Returns:
            节点显示标签
        """
        return node_id

    def load_all_data(self, start_time: str = None, end_time: str = None) -> Dict[str, Any]:
        """
        加载全部网络数据（节点和边）。

        当前实现等同于 load_from_edges 方法，
        预留用于未来支持从多个表加载数据的场景。

        Args:
            start_time: 可选的起始时间过滤条件
            end_time: 可选的结束时间过滤条件

        Returns:
            标准化网络数据字典，包含 "nodes" 和 "edges" 键
        """
        return self.load_from_edges(start_time=start_time, end_time=end_time)

    def insert_edges(self, edges: List[Dict[str, Any]]):
        """
        批量插入边数据到数据库 NETWORK_EDGES 表。

        将边列表中的每条边转换为数据库参数格式，
        属性字段自动序列化为 JSON 字符串。

        Args:
            edges: 边数据列表，每条边为字典格式，
                   包含 source, target, type, weight, attributes, source_type 等字段
        """
        # 构建带 schema 前缀的 INSERT SQL
        sql = f"""
            INSERT INTO {self.schema}.NETWORK_EDGES
            (SOURCE_NODE, TARGET_NODE, EDGE_TYPE, WEIGHT, ATTRIBUTES, SOURCE_TYPE, RECEIVE_TIME)
            VALUES (:1, :2, :3, :4, :5, :6, :7)
        """
        # 将边数据转换为参数元组列表
        params_list = []
        for edge in edges:
            # 将属性字典序列化为 JSON 字符串
            attrs = edge.get("attributes", {})
            if isinstance(attrs, dict):
                attrs = json.dumps(attrs, ensure_ascii=False)
            # 处理接收时间（兼容大小写字段名）
            receive_time = edge.get("receive_time")
            if receive_time is None:
                receive_time = edge.get("RECEIVE_TIME")
            params_list.append((
                edge["source"],
                edge["target"],
                edge.get("type", "关联"),
                float(edge.get("weight", 1.0)),
                attrs,
                edge.get("source_type", "import"),
                receive_time,
            ))
        # 执行批量插入
        db.execute_many(sql, params_list)
        logger.info(f"插入 {len(params_list)} 条边")

    def clear_all_data(self):
        """
        清空 NETWORK_EDGES 表中的所有数据。

        执行 DELETE 操作删除全部边记录。
        若操作失败（如表不存在），仅记录警告日志，不抛出异常。
        """
        try:
            db.execute_update(f"DELETE FROM {self.schema}.NETWORK_EDGES")
            logger.info("清空表 NETWORK_EDGES")
        except Exception as e:
            logger.warning(f"清空表 NETWORK_EDGES 失败: {e}")

    def get_edge_count(self) -> int:
        """
        获取 NETWORK_EDGES 表中的边总数。

        Returns:
            边的总数量，若查询失败则返回 0
        """
        try:
            result = db.execute_query(f"SELECT COUNT(*) AS CNT FROM {self.schema}.NETWORK_EDGES")
            return result[0]["CNT"] if result else 0
        except Exception:
            return 0

    def get_time_range(self) -> Dict[str, Optional[str]]:
        """
        获取边数据的时间范围（最早和最晚的接收时间）。

        Returns:
            包含时间范围的字典：
            {
                "min_time": 最早的接收时间字符串，无数据时为 None,
                "max_time": 最晚的接收时间字符串，无数据时为 None
            }
        """
        try:
            sql = f"""
                SELECT MIN(RECEIVE_TIME) AS MIN_TIME, MAX(RECEIVE_TIME) AS MAX_TIME
                FROM {self.schema}.NETWORK_EDGES
            """
            result = db.execute_query(sql)
            if result and result[0].get("MIN_TIME"):
                return {
                    "min_time": str(result[0]["MIN_TIME"]),
                    "max_time": str(result[0]["MAX_TIME"]),
                }
        except Exception as e:
            logger.warning(f"查询时间范围失败: {e}")
        # 查询失败或无数据时返回 None
        return {"min_time": None, "max_time": None}
