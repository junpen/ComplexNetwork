/**
 * API 接口层
 * 封装所有与后端通信的 HTTP 请求函数
 * 基于 axios 实例统一管理基础配置（ baseURL、超时时间、响应拦截器 ）
 */

import axios from 'axios'

// 创建 axios 实例，统一配置请求基础路径和超时时间
const api = axios.create({
  baseURL: '/api',   // 所有请求的基础路径，对应后端 /api 路由前缀
  timeout: 60000,    // 请求超时时间：60秒（网络分析计算可能耗时较长）
})

// 响应拦截器：自动解包响应数据，统一错误处理
api.interceptors.response.use(
  // 成功响应：直接返回 response.data，省去每次手动解包
  (response) => response.data,
  // 请求失败：打印错误信息并将错误继续抛出，由调用方处理
  (error) => {
    console.error('API请求失败:', error.message)
    return Promise.reject(error)
  }
)

/**
 * 获取网络摘要信息
 * 返回节点数量、边数量等网络基本统计指标
 * @param {Object} params - 可选查询参数（start_time、end_time、deleted_nodes）
 * @returns {Promise} 网络摘要数据
 */
export function getNetworkSummary(params = {}) {
  return api.get('/network/summary', { params })
}

/**
 * 获取网络图数据
 * 返回节点列表和边列表，用于前端力导向图渲染
 * @param {Object} params - 可选查询参数（start_time、end_time、deleted_nodes）
 * @returns {Promise} 图数据（nodes 和 edges 数组）
 */
export function getGraphData(params = {}) {
  return api.get('/network/graph-data', { params })
}

/**
 * 获取数据时间范围
 * 返回文书的最早和最晚接收时间，用于设置时间筛选器的上下限
 * @returns {Promise} 包含 min_time 和 max_time 的对象
 */
export function getTimeRange() {
  return api.get('/network/time-range')
}

/**
 * 获取网络特征分析数据
 * 返回度分布、聚类系数、平均路径长度等网络拓扑特征指标
 * @param {Object} params - 可选查询参数（start_time、end_time、deleted_nodes）
 * @returns {Promise} 网络特征分析结果
 */
export function getFeatureAnalysis(params = {}) {
  return api.get('/analysis/features', { params })
}

/**
 * 获取节点重要性分析数据
 * 返回 Top-N 节点的重要性排名（PageRank、介数中心性、接近中心性等指标）
 * @param {number} topN - 获取排名前N个节点，默认为10
 * @param {Object} params - 可选查询参数（start_time、end_time、deleted_nodes）
 * @returns {Promise} 节点重要性排名数据
 */
export function getImportanceAnalysis(topN = 10, params = {}) {
  return api.get('/analysis/importance', { params: { top_n: topN, ...params } })
}

/**
 * 获取网络韧性分析数据
 * 通过模拟攻击（随机失效、蓄意攻击）评估网络的鲁棒性和级联失效风险
 * @param {number} iterations - 模拟攻击的迭代次数，默认为100
 * @param {Object} params - 可选查询参数（start_time、end_time、deleted_nodes）
 * @returns {Promise} 韧性分析结果（连通性变化曲线等）
 */
export function getResilienceAnalysis(iterations = 100, params = {}) {
  return api.get('/analysis/resilience', { params: { iterations, ...params } })
}

/**
 * 获取全量分析数据
 * 一次性返回所有分析结果（摘要、特征、重要性、韧性）
 * @param {Object} params - 可选查询参数（start_time、end_time、deleted_nodes）
 * @returns {Promise} 综合分析结果
 */
export function getAllAnalysis(params = {}) {
  return api.get('/analysis/all', { params })
}

/**
 * 导出分析结果
 * 触发后端将当前分析结果导出为文件并返回下载
 * @returns {Promise} 导出文件数据
 */
export function exportResults() {
  return api.get('/network/export')
}
