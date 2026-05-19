"""
网络构建器模块。

本模块定义了 NetworkBuilder 类，负责将多种格式的数据源（文本、CSV、JSON、XML）
加载、验证、标准化后融合构建为统一的多源异构复杂网络图。

主要职责：
- 根据数据源路径自动推断数据格式
- 调用对应的 DataLoader 进行数据加载和标准化
- 将标准化后的数据注入到 HeterogeneousGraph 中
- 支持单源和多源数据融合构建
"""

from typing import Dict, Any, List, Optional
from .heterogeneous_graph import HeterogeneousGraph
from src.data_loader import (
    BaseDataLoader,
    TextDataLoader,
    CSVDataLoader,
    JSONDataLoader,
    XMLDataLoader,
)


class NetworkBuilder:
    """
    多源异构复杂网络构建器。

    将多源数据（文本、CSV、JSON、XML等格式）融合构建为统一的异构网络图。
    内部维护一个 HeterogeneousGraph 实例和数据源列表，
    支持从单个数据源或多个数据源逐步构建网络。

    数据源类型映射（LOADER_MAP）将文件格式关键字映射到对应的数据加载器类：
        - text/txt -> TextDataLoader
        - csv -> CSVDataLoader
        - json -> JSONDataLoader
        - xml -> XMLDataLoader

    Attributes:
        graph: 内部维护的异构图实例
        data_sources: 已添加的数据源信息列表，记录每个数据源的路径、类型和统计信息
    """

    # 数据源类型到加载器类的映射表
    LOADER_MAP = {
        "text": TextDataLoader,
        "txt": TextDataLoader,
        "csv": CSVDataLoader,
        "json": JSONDataLoader,
        "xml": XMLDataLoader,
    }

    def __init__(self, name: str = "multi_source_network"):
        """
        初始化网络构建器。

        Args:
            name: 构建的网络名称，默认为 "multi_source_network"
        """
        self.graph = HeterogeneousGraph(name=name)
        # 已添加的数据源记录列表，每项包含 path, type, node_count, edge_count
        self.data_sources: List[Dict[str, Any]] = []

    def add_data_source(self, source_path: str,
                        source_type: Optional[str] = None) -> Dict[str, Any]:
        """
        添加数据源并加载数据。

        流程：推断类型 -> 选择加载器 -> 加载原始数据 -> 验证 -> 标准化 -> 记录到数据源列表。

        Args:
            source_path: 数据源文件路径
            source_type: 数据源类型（如 "csv"、"json" 等），
                         若为 None 则根据文件扩展名自动推断

        Returns:
            标准化后的数据字典，包含 "nodes"、"edges" 等键

        Raises:
            ValueError: 不支持的数据源类型或数据验证失败
        """
        # 未指定类型时根据文件扩展名自动推断
        if source_type is None:
            source_type = self._infer_type(source_path)

        # 从映射表中获取对应的加载器类
        loader_class = self.LOADER_MAP.get(source_type)
        if loader_class is None:
            raise ValueError(f"不支持的数据源类型: {source_type}")

        # 实例化加载器并执行加载
        loader: BaseDataLoader = loader_class()
        raw_data = loader.load(source_path)

        # 验证原始数据格式是否正确
        if not loader.validate(raw_data):
            raise ValueError(f"数据源验证失败: {source_path}")

        # 将原始数据标准化为统一格式
        normalized_data = loader.normalize(raw_data)

        # 记录数据源信息
        self.data_sources.append({
            "path": source_path,
            "type": source_type,
            "node_count": len(normalized_data["nodes"]),
            "edge_count": len(normalized_data["edges"]),
        })

        return normalized_data

    def add_data_from_text(self, text: str) -> Dict[str, Any]:
        """
        直接从文本字符串加载网络数据。

        适用于直接传入文本内容而非文件路径的场景。

        Args:
            text: 包含网络数据的文本字符串

        Returns:
            标准化后的数据字典，包含 "nodes"、"edges" 等键
        """
        loader = TextDataLoader()
        # 使用 load_from_string 方法从文本字符串加载
        raw_data = loader.load_from_string(text)
        normalized_data = loader.normalize(raw_data)
        # 记录到数据源列表（路径标记为 "inline_text"）
        self.data_sources.append({
            "path": "inline_text",
            "type": "text",
            "node_count": len(normalized_data["nodes"]),
            "edge_count": len(normalized_data["edges"]),
        })
        return normalized_data

    def build(self) -> HeterogeneousGraph:
        """
        构建完整的多源异构网络。

        注意：当前实现中数据已在 add_data_source 时通过
        build_from_normalized_data 方法逐步注入到图中，
        此方法预留用于后续可能的额外处理逻辑。

        Returns:
            构建完成的 HeterogeneousGraph 实例
        """
        for source in self.data_sources:
            # 预留：可在此处添加额外的数据融合处理逻辑
            pass

        return self.graph

    def build_from_source(self, source_path: str,
                          source_type: Optional[str] = None) -> HeterogeneousGraph:
        """
        从单个数据源构建网络。

        便捷方法，一步完成数据源加载和网络构建。

        Args:
            source_path: 数据源文件路径
            source_type: 数据源类型，若为 None 则自动推断

        Returns:
            构建完成的 HeterogeneousGraph 实例
        """
        normalized_data = self.add_data_source(source_path, source_type)
        self.graph.build_from_normalized_data(normalized_data)
        return self.graph

    def build_from_multiple_sources(self,
                                     source_paths: List[str]) -> HeterogeneousGraph:
        """
        从多个数据源融合构建网络。

        依次加载每个数据源并将其合并到同一个网络图中，
        支持不同格式数据源的融合。

        Args:
            source_paths: 数据源文件路径列表

        Returns:
            融合构建后的 HeterogeneousGraph 实例
        """
        for path in source_paths:
            normalized_data = self.add_data_source(path)
            self.graph.build_from_normalized_data(normalized_data)
        return self.graph

    def build_from_text(self, text: str) -> HeterogeneousGraph:
        """
        从文本字符串构建网络。

        便捷方法，直接将文本内容解析并构建为网络图。

        Args:
            text: 包含网络数据的文本字符串

        Returns:
            构建完成的 HeterogeneousGraph 实例
        """
        normalized_data = self.add_data_from_text(text)
        self.graph.build_from_normalized_data(normalized_data)
        return self.graph

    def get_graph(self) -> HeterogeneousGraph:
        """
        获取当前构建的异构图实例。

        Returns:
            内部维护的 HeterogeneousGraph 实例
        """
        return self.graph

    def _infer_type(self, path: str) -> str:
        """
        根据文件扩展名推断数据源类型。

        支持的扩展名映射：
            - .csv -> "csv"
            - .json -> "json"
            - .xml -> "xml"
            - 其他 -> "text"（默认按文本处理）

        Args:
            path: 文件路径

        Returns:
            推断出的数据源类型字符串
        """
        if path.endswith(".csv"):
            return "csv"
        elif path.endswith(".json"):
            return "json"
        elif path.endswith(".xml"):
            return "xml"
        else:
            # 未识别的扩展名默认按文本格式处理
            return "text"
