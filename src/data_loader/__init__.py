"""
数据加载器包（data_loader）

本包提供了多种格式的数据加载器，用于从不同数据源中解析和加载
网络图的节点与边数据。所有加载器均继承自 BaseDataLoader 基类，
遵循统一的加载-验证-标准化流程。

可用的加载器：
    - BaseDataLoader: 抽象基类，定义统一接口
    - TextDataLoader: 纯文本数据加载器
    - CSVDataLoader: CSV格式数据加载器
    - JSONDataLoader: JSON格式数据加载器
    - XMLDataLoader: XML格式数据加载器
"""

from .base_loader import BaseDataLoader
from .text_loader import TextDataLoader
from .csv_loader import CSVDataLoader
from .json_loader import JSONDataLoader
from .xml_loader import XMLDataLoader

__all__ = [
    "BaseDataLoader",
    "TextDataLoader",
    "CSVDataLoader",
    "JSONDataLoader",
    "XMLDataLoader",
]
