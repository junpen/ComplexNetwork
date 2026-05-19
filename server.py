#!/usr/bin/env python3
"""
多源异构文书流转分析模型 - FastAPI后端服务
============================================

本模块是整个分析平台的Web后端核心，基于FastAPI框架构建。
提供以下主要功能：
  1. 网络数据的加载（支持DM达梦数据库、JSON/CSV/XML文件、文本输入）
  2. 网络概览与图数据查询API
  3. 网络特征分析、重要度分析、韧性分析等RESTful接口
  4. 数据上传与导入功能
  5. 前端静态文件托管

数据源: DM达梦数据库 / 文件（JSON、CSV、XML、纯文本）
"""

import os
import sys
import json
import logging
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 将当前脚本所在目录加入系统路径，确保可以正确引用本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.network import NetworkBuilder, HeterogeneousGraph
from src.analysis import FeatureAnalyzer, ImportanceAnalyzer, ResilienceAnalyzer
from config import DATA_SOURCE, DM_DATABASE

# 初始化日志记录器，设置日志级别为INFO
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 创建FastAPI应用实例
app = FastAPI(title="多源异构文书流转分析平台", version="1.0.0")

# 配置CORS（跨域资源共享）中间件，允许前端跨域访问后端接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 允许所有来源域名
    allow_credentials=True,     # 允许携带凭证（Cookie等）
    allow_methods=["*"],        # 允许所有HTTP方法
    allow_headers=["*"],        # 允许所有请求头
)

# 全局变量：缓存当前加载的异构图对象和时间范围键，避免重复加载
_current_graph: Optional[HeterogeneousGraph] = None
_current_time_key: Optional[str] = None


class TextInput(BaseModel):
    """文本输入数据模型，用于接收前端提交的纯文本数据。

    Attributes:
        text: 用户输入的文本内容，用于从中解析网络关系
        name: 网络名称标识，默认为 'text_network'
    """
    text: str
    name: str = "text_network"


def _filter_deleted_nodes(graph: HeterogeneousGraph, deleted_nodes: str) -> HeterogeneousGraph:
    """从图中过滤掉被删除的节点，返回一个新的子图。

    该函数用于前端交互中的节点删除功能，根据用户指定的节点列表，
    生成不包含这些节点的新子图。

    Args:
        graph: 原始异构图对象
        deleted_nodes: 逗号分隔的待删除节点ID字符串，例如 "节点A,节点B"

    Returns:
        过滤后的新异构图对象。如果没有需要删除的节点，则返回原图。
    """
    if not deleted_nodes:
        return graph
    del_set = set(n.strip() for n in deleted_nodes.split(",") if n.strip())
    if not del_set:
        return graph
    keep_nodes = [n for n in graph.graph.nodes() if n not in del_set]
    if len(keep_nodes) == graph.graph.number_of_nodes():
        return graph
    sub_nx = graph.graph.subgraph(keep_nodes).copy()
    new_hg = HeterogeneousGraph(name=graph.name)
    new_hg.graph = sub_nx
    logger.info(f"已过滤 {len(del_set)} 个删除节点，剩余 {len(keep_nodes)} 节点")
    return new_hg


def _load_from_database(start_time: str = None, end_time: str = None) -> HeterogeneousGraph:
    """从DM达梦数据库加载网络数据并构建异构图。

    通过DMDataLoader连接数据库，加载指定时间范围内的边数据，
    然后通过NetworkBuilder构建异构图。

    Args:
        start_time: 数据起始时间（可选），用于时间范围过滤
        end_time: 数据截止时间（可选），用于时间范围过滤

    Returns:
        从数据库数据构建的异构图对象

    Raises:
        RuntimeError: 当dmPython驱动未安装时抛出
    """
    from src.database import DMDataLoader, DM_AVAILABLE

    # 检查dmPython驱动是否可用
    if not DM_AVAILABLE:
        raise RuntimeError("dmPython未安装，无法连接DM数据库。请执行: pip install dmPython")

    # 创建数据加载器并加载数据
    loader = DMDataLoader()
    data = loader.load_all_data(start_time=start_time, end_time=end_time)

    # 使用网络构建器从标准化数据构建图
    builder = NetworkBuilder(name="dm_database_network")
    graph = builder.get_graph()
    graph.build_from_normalized_data(data)
    return graph


def _load_from_file(source_path: str) -> HeterogeneousGraph:
    """从文件加载网络数据并构建异构图。

    根据文件扩展名自动识别文件类型（JSON、CSV、XML、纯文本），
    并调用对应的解析器进行数据加载。

    Args:
        source_path: 数据文件的绝对或相对路径

    Returns:
        从文件数据构建的异构图对象
    """
    builder = NetworkBuilder(name="file_network")
    # 根据文件扩展名选择对应的解析方式
    if source_path.endswith(".json"):
        return builder.build_from_source(source_path, "json")
    elif source_path.endswith(".csv"):
        return builder.build_from_source(source_path, "csv")
    elif source_path.endswith(".xml"):
        return builder.build_from_source(source_path, "xml")
    else:
        return builder.build_from_source(source_path, "text")


def _get_or_load_graph(source: str = None, start_time: str = None, end_time: str = None) -> HeterogeneousGraph:
    """获取或加载异构图（带缓存机制）。

    该函数实现了智能的图数据加载策略：
      1. 如果指定了数据源（database/file），则直接从该源加载
      2. 如果未指定数据源但存在缓存且时间范围未变，则使用缓存
      3. 如果指定了时间范围，优先从数据库加载
      4. 如果配置中数据源为database，尝试从数据库加载，失败则回退到JSON文件
      5. 最终回退到本地示例数据文件

    Args:
        source: 数据源标识，可选值: "database"、文件路径、"dm://" 前缀等
        start_time: 数据起始时间（可选）
        end_time: 数据截止时间（可选）

    Returns:
        加载完成的异构图对象
    """
    global _current_graph, _current_time_key

    # 生成时间范围的缓存键，用于判断是否需要重新加载
    time_key = f"{start_time or ''}|{end_time or ''}"

    # 策略1: 显式指定从数据库加载
    if source == "database":
        logger.info("从DM数据库加载网络数据...")
        _current_graph = _load_from_database(start_time=start_time, end_time=end_time)
        _current_time_key = time_key
        return _current_graph

    # 策略2: 指定了特定的数据源（文件路径或dm://前缀）
    if source and source not in ("database", "file"):
        if source.startswith("dm://") or source == "dm":
            # dm:// 前缀视为数据库源
            _current_graph = _load_from_database(start_time=start_time, end_time=end_time)
            _current_time_key = time_key
            return _current_graph
        # 否则视为文件路径
        _current_graph = _load_from_file(source)
        _current_time_key = time_key
        return _current_graph

    # 策略3: 未指定数据源，检查缓存是否可用
    if _current_graph is not None and _current_time_key == time_key:
        return _current_graph

    # 策略4: 有时间范围参数，优先从数据库加载
    if start_time or end_time:
        logger.info("时间范围过滤，从DM数据库加载...")
        try:
            _current_graph = _load_from_database(start_time=start_time, end_time=end_time)
            _current_time_key = time_key
            return _current_graph
        except Exception as e:
            logger.warning(f"数据库加载失败: {e}，回退到JSON文件")

    # 策略5: 配置文件中指定了database作为默认数据源
    if DATA_SOURCE == "database":
        try:
            logger.info("从DM数据库加载网络数据...")
            _current_graph = _load_from_database(start_time=start_time, end_time=end_time)
            _current_time_key = time_key
            return _current_graph
        except Exception as e:
            logger.warning(f"数据库加载失败: {e}，回退到JSON文件")

    # 策略6: 最终回退，加载本地示例数据文件
    sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_data.json")
    _current_graph = _load_from_file(sample_path)
    _current_time_key = time_key

    return _current_graph


@app.get("/api/health")
async def health_check():
    """健康检查接口。

    返回服务运行状态、版本号、当前配置的数据源类型，
    以及DM达梦数据库的连接信息（用于前端诊断）。
    """
    from src.database import DM_AVAILABLE
    return {
        "status": "ok",
        "version": "1.0.0",
        "data_source": DATA_SOURCE,
        "dm_database_available": DM_AVAILABLE,
        "dm_host": DM_DATABASE["host"],
        "dm_port": DM_DATABASE["port"],
    }


@app.get("/api/network/summary")
async def get_network_summary(
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    deleted_nodes: Optional[str] = None,
):
    """获取网络概览摘要信息。

    返回当前网络的节点数量、边数量、密度、节点类型分布、边类型分布等统计信息。

    Args:
        source: 数据源标识
        start_time: 起始时间过滤
        end_time: 截止时间过滤
        deleted_nodes: 逗号分隔的待排除节点ID

    Returns:
        包含网络概览统计信息的字典
    """
    graph = _get_or_load_graph(source=source, start_time=start_time, end_time=end_time)
    graph = _filter_deleted_nodes(graph, deleted_nodes)
    return graph.summary()


@app.get("/api/network/time-range")
async def get_time_range():
    """获取网络数据的时间范围。

    从DM达梦数据库中查询边数据的时间范围（最早和最晚时间），
    用于前端时间选择器的时间范围设定。

    Returns:
        包含 min_time 和 max_time 的字典，数据库不可用时返回 None
    """
    from src.database import DMDataLoader, DM_AVAILABLE
    if not DM_AVAILABLE:
        return {"min_time": None, "max_time": None}
    loader = DMDataLoader()
    return loader.get_time_range()


@app.get("/api/network/graph-data")
async def get_graph_data(
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    deleted_nodes: Optional[str] = None,
):
    """获取完整的图数据（节点和边），用于前端可视化渲染。

    将异构图转换为前端可视化组件所需的格式，包含节点列表（含标签、度数）
    和边列表（含源节点、目标节点、权重、时间等）。

    Args:
        source: 数据源标识
        start_time: 起始时间过滤
        end_time: 截止时间过滤
        deleted_nodes: 逗号分隔的待排除节点ID

    Returns:
        包含 nodes、edges、nodeCount、edgeCount 的字典
    """
    graph = _get_or_load_graph(source=source, start_time=start_time, end_time=end_time)
    graph = _filter_deleted_nodes(graph, deleted_nodes)
    nodes_data = []
    for node_id in graph.graph.nodes():
        info = graph.get_node_info(node_id)
        nodes_data.append({
            "id": node_id,
            "label": info.get("label", node_id),
            "source": info.get("source", ""),
            "degree": graph.graph.degree(node_id),
        })

    edges_data = []
    for u, v, data in graph.graph.edges(data=True):
        edge_item = {
            "source": u,
            "target": v,
            "weight": data.get("weight", 1.0),
            "sourceType": data.get("source_type", ""),
        }
        receive_time = data.get("receive_time")
        if receive_time:
            edge_item["receiveTime"] = str(receive_time)
        edges_data.append(edge_item)

    return {
        "nodes": nodes_data,
        "edges": edges_data,
        "nodeCount": len(nodes_data),
        "edgeCount": len(edges_data),
    }


@app.get("/api/analysis/features")
async def get_feature_analysis(
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    deleted_nodes: Optional[str] = None,
):
    """获取网络特征指标分析结果。

    包括度分析、距离分析、中心性分析、聚集系数分析和网络级指标等。

    Args:
        source: 数据源标识
        start_time: 起始时间过滤
        end_time: 截止时间过滤
        deleted_nodes: 逗号分隔的待排除节点ID

    Returns:
        包含完整特征分析结果的字典
    """
    graph = _get_or_load_graph(source=source, start_time=start_time, end_time=end_time)
    graph = _filter_deleted_nodes(graph, deleted_nodes)
    analyzer = FeatureAnalyzer(graph)
    return analyzer.analyze_all()


@app.get("/api/analysis/importance")
async def get_importance_analysis(
    source: Optional[str] = None,
    top_n: int = Query(default=10, le=50),
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    deleted_nodes: Optional[str] = None,
):
    """获取节点重要度与可替代程度分析结果。

    包括综合重要度排序、可替代程度分析、结构洞分析和关键参与者分析。

    Args:
        source: 数据源标识
        top_n: 返回排名前N的节点数量，最大不超过50
        start_time: 起始时间过滤
        end_time: 截止时间过滤
        deleted_nodes: 逗号分隔的待排除节点ID

    Returns:
        包含完整重要度分析结果的字典
    """
    graph = _get_or_load_graph(source=source, start_time=start_time, end_time=end_time)
    graph = _filter_deleted_nodes(graph, deleted_nodes)
    analyzer = ImportanceAnalyzer(graph)
    return analyzer.analyze_all(top_n=top_n)


@app.get("/api/analysis/resilience")
async def get_resilience_analysis(
    source: Optional[str] = None,
    iterations: int = Query(default=100, le=500),
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    deleted_nodes: Optional[str] = None,
):
    """获取网络韧性与脆弱性分析结果。

    包括韧性指标、脆弱性指标、攻击模拟和鲁棒性曲线等。

    Args:
        source: 数据源标识
        iterations: 攻击模拟的迭代次数，最大不超过500
        start_time: 起始时间过滤
        end_time: 截止时间过滤
        deleted_nodes: 逗号分隔的待排除节点ID

    Returns:
        包含完整韧性分析结果的字典
    """
    graph = _get_or_load_graph(source=source, start_time=start_time, end_time=end_time)
    graph = _filter_deleted_nodes(graph, deleted_nodes)
    analyzer = ResilienceAnalyzer(graph)
    return analyzer.analyze_all(simulation_iterations=iterations)


@app.get("/api/analysis/all")
async def get_all_analysis(
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    deleted_nodes: Optional[str] = None,
):
    """一次性获取所有分析结果（网络概览 + 特征 + 重要度 + 韧性）。

    这是一个聚合接口，适合前端初始化时一次性获取所有数据，
    减少多次请求的网络开销。

    Args:
        source: 数据源标识
        start_time: 起始时间过滤
        end_time: 截止时间过滤
        deleted_nodes: 逗号分隔的待排除节点ID

    Returns:
        包含 summary、features、importance、resilience 四个分析模块结果的字典
    """
    graph = _get_or_load_graph(source=source, start_time=start_time, end_time=end_time)
    graph = _filter_deleted_nodes(graph, deleted_nodes)
    return {
        "summary": graph.summary(),
        "features": FeatureAnalyzer(graph).analyze_all(),
        "importance": ImportanceAnalyzer(graph).analyze_all(),
        "resilience": ResilienceAnalyzer(graph).analyze_all(simulation_iterations=100),
    }


@app.post("/api/data/upload")
async def upload_data(file: UploadFile = File(...)):
    """上传数据文件并构建网络图。

    支持JSON、CSV、XML等格式的文件上传，上传后自动解析并构建网络图，
    同时更新全局缓存。

    Args:
        file: 用户上传的文件对象

    Returns:
        包含成功消息和文件名的字典
    """
    # 确保上传目录存在
    os.makedirs("uploads", exist_ok=True)
    filepath = os.path.join("uploads", file.filename)
    # 读取上传文件的二进制内容
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # 从上传的文件构建网络图并更新全局缓存
    global _current_graph
    _current_graph = _load_from_file(filepath)
    return {"message": "数据加载成功", "filename": file.filename}


@app.post("/api/data/text")
async def load_text(data: TextInput):
    """从纯文本解析并构建网络图。

    接收用户输入的结构化文本，通过NetworkBuilder解析文本中的
    实体和关系，构建异构图。

    Args:
        data: TextInput模型，包含文本内容和网络名称

    Returns:
        包含成功消息和网络摘要的字典
    """
    builder = NetworkBuilder(name=data.name)
    global _current_graph
    _current_graph = builder.build_from_text(data.text)
    return {
        "message": "文本数据解析成功",
        "summary": _current_graph.summary(),
    }


@app.post("/api/data/database/reload")
async def reload_from_database():
    """从DM达梦数据库重新加载网络数据。

    强制从数据库重新加载数据，忽略现有缓存，用于数据更新后的刷新。

    Returns:
        包含成功消息和网络摘要的字典
    """
    global _current_graph
    _current_graph = _load_from_database()
    return {
        "message": "数据库数据重新加载成功",
        "summary": _current_graph.summary(),
    }


@app.post("/api/data/database/import-json")
async def import_json_to_database(file: UploadFile = File(...)):
    """将JSON文件中的边数据导入DM达梦数据库。

    上传一个JSON文件，将其中的边数据清空旧数据后批量写入数据库，
    然后重新加载构建网络图。

    Args:
        file: 包含边数据的JSON文件

    Returns:
        包含成功消息和导入边数量的字典
    """
    from src.database import DMDataLoader, DM_AVAILABLE

    # 检查数据库驱动是否可用
    if not DM_AVAILABLE:
        return {"error": "dmPython未安装"}

    # 解析上传的JSON文件
    content = await file.read()
    data = json.loads(content)

    # 清空旧数据并导入新边数据
    loader = DMDataLoader()
    loader.clear_all_data()
    loader.insert_edges(data.get("edges", []))

    # 重新从数据库加载网络图
    global _current_graph
    _current_graph = _load_from_database()

    return {
        "message": "JSON数据已导入数据库并重新加载",
        "edges": len(data.get("edges", [])),
    }


@app.get("/api/network/export")
async def export_results(
    deleted_nodes: Optional[str] = None,
):
    """导出完整的分析结果（网络概览 + 特征 + 重要度 + 韧性）。

    以JSON格式返回所有分析模块的结果，用于前端下载或进一步处理。

    Args:
        deleted_nodes: 逗号分隔的待排除节点ID

    Returns:
        包含 summary、features、importance、resilience 的完整分析结果字典
    """
    graph = _get_or_load_graph()
    graph = _filter_deleted_nodes(graph, deleted_nodes)
    return {
        "summary": graph.summary(),
        "features": FeatureAnalyzer(graph).analyze_all(),
        "importance": ImportanceAnalyzer(graph).analyze_all(),
        "resilience": ResilienceAnalyzer(graph).analyze_all(),
    }


# 检测前端构建产物目录是否存在，如果存在则挂载为静态文件服务
# 这样部署时前后端可以共用同一个端口
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


if __name__ == "__main__":
    # 直接运行此文件时，启动uvicorn服务器
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
