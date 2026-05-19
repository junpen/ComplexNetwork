<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-left">
        <h1 class="app-title">多源异构文书流转分析平台</h1>
        <span class="app-subtitle">Multi-Source Document Flow Analysis System</span>
      </div>
      <div class="header-right">
        <div class="time-filter">
          <label class="time-label">接收时间</label>
          <input
            type="datetime-local"
            class="time-input"
            v-model="startTime"
            :min="timeRange.min"
            :max="timeRange.max"
          />
          <span class="time-sep">~</span>
          <input
            type="datetime-local"
            class="time-input"
            v-model="endTime"
            :min="timeRange.min"
            :max="timeRange.max"
          />
          <button class="btn btn-sm btn-primary" @click="refreshAll" :disabled="loading">查询</button>
          <button class="btn btn-sm btn-outline" @click="resetTimeFilter" :disabled="loading">重置</button>
        </div>
        <button class="btn btn-primary" @click="refreshAll" :disabled="loading">
          {{ loading ? '分析中...' : '刷新分析' }}
        </button>
      </div>
    </header>

    <div class="tab-nav">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        {{ tab.label }}
      </button>
    </div>

    <main class="main-content">
      <div v-if="loading" class="loading-overlay" @click.self="loading = false">
        <div class="spinner"></div>
        <p>正在分析文书流转数据...</p>
      </div>

      <NetworkGraph
        v-if="activeTab === 'graph'"
        :graph-data="graphData"
        :summary="summary"
        :deleted-node-ids="deletedNodeIds"
        @delete-node="onDeleteNode"
        @restore-nodes="onRestoreNodes"
      />
      <NetworkOverview v-if="activeTab === 'overview'" :summary="summary" :features="features" />
      <FeatureAnalysis v-if="activeTab === 'features'" :features="features" />
      <ImportanceAnalysis v-if="activeTab === 'importance'" :importance="importance" />
      <ResilienceAnalysis v-if="activeTab === 'resilience'" :resilience="resilience" />
      <AnalysisConclusion v-if="activeTab === 'conclusion'" :summary="summary" :features="features" :importance="importance" :resilience="resilience" />
      <ProjectDocumentation v-if="activeTab === 'docs'" />
    </main>

    <footer class="app-footer">
      <span>NetworkX &copy; 2025</span>
      <span v-if="summary">单位: {{ summary.node_count }} | 文书流转: {{ summary.edge_count }}<span v-if="deletedNodeIds.length" style="color:#ef4444;margin-left:8px">| 已移除: {{ deletedNodeIds.length }}</span></span>
    </footer>
  </div>
</template>

<script setup>
// ==================== Vue 核心依赖 ====================
import { ref, onMounted } from 'vue'

// ==================== API 接口导入 ====================
// 导入后端数据接口函数，用于获取网络摘要、图数据、特征分析等
import {
  getNetworkSummary, getGraphData, getFeatureAnalysis,
  getImportanceAnalysis, getResilienceAnalysis,
  getTimeRange
} from './api/index.js'

// ==================== 子组件导入 ====================
import NetworkGraph from './components/NetworkGraph.vue'
import NetworkOverview from './components/NetworkOverview.vue'
import FeatureAnalysis from './components/FeatureAnalysis.vue'
import ImportanceAnalysis from './components/ImportanceAnalysis.vue'
import ResilienceAnalysis from './components/ResilienceAnalysis.vue'
import AnalysisConclusion from './components/AnalysisConclusion.vue'
import ProjectDocumentation from './components/ProjectDocumentation.vue'

// ==================== 标签页配置 ====================
// 定义各个功能模块的标签页，key用于标识当前激活页，label为显示名称，icon为图标
const tabs = [
  { key: 'overview', label: '流转概览', icon: '📊' },
  { key: 'graph', label: '文书流转图', icon: '🔗' },
  { key: 'features', label: '流转特征指标', icon: '📈' },
  { key: 'importance', label: '关键单位分析', icon: '⭐' },
  { key: 'resilience', label: '流转稳定性/风险', icon: '🛡' },
  { key: 'conclusion', label: '分析结论', icon: '📋' },
  { key: 'docs', label: '使用说明', icon: '📖' },
]

// ==================== 响应式状态变量 ====================
const activeTab = ref('overview')       // 当前激活的标签页key，默认为"流转概览"
const loading = ref(false)              // 全局加载状态标志，控制加载动画和按钮禁用
const summary = ref(null)              // 网络摘要数据（节点数、边数等基本统计信息）
const graphData = ref(null)            // 网络图数据（节点列表、边列表，用于力导向图渲染）
const features = ref(null)             // 网络特征分析数据（度分布、聚类系数、连通分量等）
const importance = ref(null)           // 节点重要性分析数据（PageRank、介数中心性排名等）
const resilience = ref(null)           // 网络韧性分析数据（模拟攻击结果、级联失效评估等）

// ==================== 时间筛选相关状态 ====================
const timeRange = ref({ min: '', max: '' })  // 数据时间范围（从后端获取），用于限制时间输入框的可选范围
const startTime = ref('')                    // 用户选择的起始时间
const endTime = ref('')                      // 用户选择的结束时间
const deletedNodeIds = ref([])               // 用户在网络图中删除的节点ID列表，用于模拟节点移除场景

/**
 * 构建时间筛选参数对象
 * 将当前的时间范围和已删除节点信息组装为API请求的查询参数
 * @returns {Object} 包含 start_time、end_time、deleted_nodes 的参数对象
 */
function buildTimeParams() {
  const params = {}
  if (startTime.value) params.start_time = startTime.value
  if (endTime.value) params.end_time = endTime.value
  if (deletedNodeIds.value.length) params.deleted_nodes = deletedNodeIds.value.join(',')
  return params
}

/**
 * 处理节点删除事件
 * 当用户在网络图中点击删除某个节点时触发，将该节点ID加入已删除列表并刷新数据
 * @param {string|number} nodeId - 被删除的节点ID
 */
function onDeleteNode(nodeId) {
  if (!deletedNodeIds.value.includes(nodeId)) {
    deletedNodeIds.value = [...deletedNodeIds.value, nodeId]
    refreshAll()
  }
}

/**
 * 处理节点恢复事件
 * 当用户在网络图中点击恢复所有已删除节点时触发，清空删除列表并刷新数据
 */
function onRestoreNodes() {
  deletedNodeIds.value = []
  refreshAll()
}

/**
 * 从后端加载数据的时间范围
 * 获取文书的最早和最晚接收时间，用于设置时间选择器的上下限
 */
async function loadTimeRange() {
  try {
    const tr = await getTimeRange()
    // 截取前16位以匹配 datetime-local 输入框格式（YYYY-MM-DDTHH:mm）
    if (tr.min_time) {
      timeRange.value.min = tr.min_time.slice(0, 16)
      timeRange.value.max = tr.max_time.slice(0, 16)
    }
  } catch {
    timeRange.value = { min: '', max: '' }
  }
}

/**
 * 重置时间筛选条件
 * 清空起止时间和已删除节点列表，然后重新加载全部数据
 */
function resetTimeFilter() {
  startTime.value = ''
  endTime.value = ''
  deletedNodeIds.value = []
  refreshAll()
}

/**
 * 刷新所有分析数据（核心数据加载函数）
 * 并行请求后端5个API接口，分别获取网络摘要、图数据、特征分析、重要性分析和韧性分析
 * 使用 Promise.allSettled 确保单个请求失败不影响其他请求的结果
 */
async function refreshAll() {
  loading.value = true
  try {
    // 构建当前筛选条件参数
    const tp = buildTimeParams()
    // 并行发起5个API请求，allSettled保证全部请求完成后统一处理
    const results = await Promise.allSettled([
      getNetworkSummary(tp),           // 获取网络基本统计摘要
      getGraphData(tp),                // 获取网络图节点和边数据
      getFeatureAnalysis(tp),          // 获取网络拓扑特征分析
      getImportanceAnalysis(15, tp),   // 获取Top15节点重要性排名
      getResilienceAnalysis(100, tp),  // 获取100次迭代的韧性分析
    ])
    // 逐个处理请求结果：成功则更新对应响应式数据，失败则输出错误日志
    if (results[0].status === 'fulfilled') summary.value = results[0].value
    else console.error('summary失败:', results[0].reason)
    if (results[1].status === 'fulfilled') graphData.value = results[1].value
    else console.error('graph失败:', results[1].reason)
    if (results[2].status === 'fulfilled') features.value = results[2].value
    else console.error('features失败:', results[2].reason)
    if (results[3].status === 'fulfilled') importance.value = results[3].value
    else console.error('importance失败:', results[3].reason)
    if (results[4].status === 'fulfilled') resilience.value = results[4].value
    else console.error('resilience失败:', results[4].reason)
  } catch (e) {
    console.error('refreshAll异常:', e)
  } finally {
    loading.value = false
  }
}

// ==================== 生命周期钩子 ====================
// 组件挂载后立即加载数据时间范围和全部分析数据
onMounted(() => {
  loadTimeRange()
  refreshAll()
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f0f4f0; color: #1e293b; min-height: 100vh; }

.app-container { display: flex; flex-direction: column; min-height: 100vh; }

.app-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 28px; background: #ffffff; border-bottom: 2px solid #22c55e; }
.header-left { display: flex; align-items: baseline; gap: 16px; }
.app-title { font-size: 22px; font-weight: 700; color: #15803d; letter-spacing: -0.5px; }
.app-subtitle { font-size: 13px; color: #64748b; letter-spacing: 1px; }
.header-right { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

.time-filter { display: flex; align-items: center; gap: 6px; background: #f8faf8; padding: 4px 10px; border-radius: 8px; border: 1px solid #22c55e; }
.time-label { font-size: 12px; color: #475569; white-space: nowrap; }
.time-input { padding: 4px 8px; background: #ffffff; border: 1px solid #bbf7d0; border-radius: 6px; color: #1e293b; font-size: 12px; width: 170px; }
.time-input::-webkit-calendar-picker-indicator { filter: none; }
.time-sep { color: #64748b; font-size: 14px; }
.btn-sm { padding: 4px 10px; font-size: 12px; }

.btn { padding: 8px 18px; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: #16a34a; color: #fff; }
.btn-primary:hover:not(:disabled) { background: #15803d; }
.btn-outline { background: transparent; color: #475569; border: 1px solid #22c55e; }
.btn-outline:hover { background: #f0fdf4; color: #15803d; }
.btn-full { width: 100%; margin-top: 12px; padding: 10px; }

.tab-nav { display: flex; gap: 0; padding: 0 28px; background: #ffffff; border-bottom: 2px solid #22c55e; overflow-x: auto; }
.tab-btn { display: flex; align-items: center; gap: 6px; padding: 14px 20px; border: none; background: transparent; color: #475569; font-size: 14px; font-weight: 500; cursor: pointer; border-bottom: 2px solid transparent; transition: all 0.2s; white-space: nowrap; }
.tab-btn:hover { color: #15803d; background: rgba(34,197,94,0.05); }
.tab-btn.active { color: #16a34a; border-bottom-color: #16a34a; }
.tab-icon { font-size: 16px; }

.main-content { flex: 1; padding: 24px 28px; position: relative; }

.loading-overlay { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(255,255,255,0.85); z-index: 10; gap: 16px; }
.spinner { width: 40px; height: 40px; border: 3px solid #bbf7d0; border-top-color: #16a34a; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.app-footer { padding: 10px 28px; background: #ffffff; border-top: 2px solid #22c55e; display: flex; justify-content: space-between; font-size: 12px; color: #64748b; }
</style>