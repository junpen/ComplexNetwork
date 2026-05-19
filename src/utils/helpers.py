"""
工具函数模块

本模块提供了一系列通用的辅助工具函数，包括：
    - 数据导出：将数据导出为 JSON 或 CSV 文件
    - 控制台输出格式化：打印分节标题和小节标题
    - 数值格式化：将浮点数格式化为指定精度的字符串
    - 列表截断：截取列表的前N个元素用于预览显示
"""

import json
import csv
from typing import Dict, Any, List


def export_to_json(data: Dict[str, Any], filepath: str) -> None:
    """
    将数据字典导出为JSON文件。

    使用 UTF-8 编码写入，保留中文字符（ensure_ascii=False），
    采用缩进格式化输出便于阅读。

    参数：
        data: 待导出的数据字典
        filepath: 输出文件路径
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def export_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """
    将数据列表导出为CSV文件。

    使用第一个元素的键作为表头列名，所有字典共享相同的字段结构。
    若数据列表为空则直接返回，不创建文件。

    参数：
        data: 待导出的字典列表，每个字典代表一行数据
        filepath: 输出文件路径
    """
    if not data:
        return
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def print_section(title: str, width: int = 60) -> None:
    """
    打印分节标题。

    在控制台输出带有等号分隔线的标题，用于区分不同的输出区域。

    示例输出：
        ============================================================
          数据分析报告
        ============================================================

    参数：
        title: 标题文本
        width: 分隔线宽度，默认60个字符
    """
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_subsection(title: str) -> None:
    """
    打印小节标题。

    在控制台输出带有短横线前缀的小节标题，用于在分节内部进一步细分。

    示例输出：
        --- 节点统计 ---

    参数：
        title: 小节标题文本
    """
    print(f"\n--- {title} ---")


def format_number(value: float, precision: int = 4) -> str:
    """
    将浮点数格式化为指定精度的字符串。

    使用 Python 的格式化字符串控制小数位数。

    参数：
        value: 待格式化的数值
        precision: 小数位数，默认4位

    返回：
        格式化后的字符串
    """
    return f"{value:.{precision}f}"


def truncate_list(lst: List[Any], max_items: int = 5) -> List[Any]:
    """
    截取列表的前N个元素。

    用于在控制台预览显示时，避免输出过长的列表内容。

    参数：
        lst: 待截取的列表
        max_items: 最大保留元素数，默认5个

    返回：
        截取后的列表
    """
    return lst[:max_items]
