<!-- 文书流转图组件：基于 ECharts 力导向图展示文书在各单位间的流转关系（网络拓扑图可视化） -->
<template>
  <!-- 整个流转图容器的最外层，点击任意位置时关闭右键菜单 -->
  <div class="network-graph-container" @click="closeContextMenu">
    <!-- 顶部工具栏：显示统计信息和筛选控件 -->
    <div class="graph-toolbar">
      <!-- 左侧：显示当前可见的单位数量、流转边数量以及已移除单位的提示 -->
      <span class="graph-info">
        单位: <strong>{{ displayNodeCount }}</strong>
        文书流转: <strong>{{ displayEdgeCount }}</strong>
        <span v-if="deletedNodeIds.length" class="deleted-info">(已移除 {{ deletedNodeIds.length }} 个单位)</span>
      </span>
      <!-- 右侧：操作按钮 -->
      <div class="graph-controls">
        <button class="btn btn-sm" @click="resetView">重置视图</button>
        <button v-if="deletedNodeIds.length" class="btn btn-sm btn-restore" @click="handleRestore">恢复已移除</button>
      </div>
    </div>
    <!-- ECharts 图表挂载的 DOM 容器 -->
    <div ref="chartRef" class="graph-chart"></div>
    <!-- 右键上下文菜单：仅在右键点击节点时显示，提供"移除单位"操作 -->
    <div
      v-if="ctxMenu.visible"
      class="ctx-menu"
      :style="{ left: ctxMenu.x + 'px', top: ctxMenu.y + 'px' }"
    >
      <!-- 菜单标题：显示被右键点击的节点名称 -->
      <div class="ctx-menu-item ctx-menu-title">{{ ctxMenu.nodeLabel }}</div>
      <div class="ctx-menu-divider"></div>
      <!-- 危险操作：从流转图中移除该节点（点击时阻止事件冒泡以免触发容器关闭菜单） -->
      <div class="ctx-menu-item ctx-menu-danger" @click.stop="handleDelete(ctxMenu.nodeId)">移除单位</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

// ==================== Props 定义 ====================
// graphData: 图谱数据，包含 nodes（节点/单位列表）和 edges（边/流转关系列表）
// summary: 流转概要统计信息（可选）
// deletedNodeIds: 已被用户移除的节点 ID 列表，由父组件维护
const props = defineProps({
  graphData: { type: Object, default: null },
  summary: { type: Object, default: null },
  deletedNodeIds: { type: Array, default: () => [] },
})

// ==================== 事件定义 ====================
// delete-node: 用户右键移除节点时触发，传递节点 ID 给父组件
// restore-nodes: 用户点击"恢复已移除"按钮时触发
const emit = defineEmits(['delete-node', 'restore-nodes'])

// ==================== 响应式变量 ====================
// ECharts 图表的 DOM 引用
const chartRef = ref(null)
// ECharts 实例对象（非响应式，使用 let 声明）
let chart = null

// ==================== 响应式变量（续） ====================
const deletedSet = computed(() => new Set(props.deletedNodeIds))

// ctxMenu: 右键菜单的状态对象，包含是否可见、位置坐标、目标节点 ID 和名称
const ctxMenu = ref({ visible: false, x: 0, y: 0, nodeId: null, nodeLabel: '' })

// displayNodeCount: 当前可见的节点（单位）数量（排除已删除的节点）
const displayNodeCount = computed(() => {
  if (!props.graphData?.nodes) return 0
  return props.graphData.nodes.filter(n => !deletedSet.value.has(n.id)).length
})

// displayEdgeCount: 当前可见的边（流转关系）数量（仅统计两端节点均可见的边）
const displayEdgeCount = computed(() => {
  if (!props.graphData?.edges) return 0
  const validIds = new Set(
    props.graphData.nodes
      .filter(n => !deletedSet.value.has(n.id))
      .map(n => n.id)
  )
  return props.graphData.edges.filter(e => validIds.has(e.source) && validIds.has(e.target)).length
})

// ==================== 交互函数 ====================
// resetView: 重置视图 —— 恢复图表初始缩放状态
function resetView() {
  if (chart) chart.dispatchAction({ type: 'restore' })
  renderChart()
}

// closeContextMenu: 关闭右键上下文菜单
function closeContextMenu() {
  ctxMenu.value.visible = false
}

// handleDelete: 处理移除节点操作，关闭菜单并通知父组件
function handleDelete(nodeId) {
  ctxMenu.value.visible = false
  emit('delete-node', nodeId)
}

// handleRestore: 处理恢复已移除节点操作，通知父组件
function handleRestore() {
  emit('restore-nodes')
}

// ==================== 核心渲染函数 ====================
// renderChart: 根据当前筛选条件渲染/更新 ECharts 力导向图
function renderChart() {
  if (!chart || !props.graphData) return

  const filteredNodes = props.graphData.nodes.filter(
    n => !deletedSet.value.has(n.id)
  )
  const filteredIds = new Set(filteredNodes.map(n => n.id))
  const filteredEdges = props.graphData.edges.filter(
    e => filteredIds.has(e.source) && filteredIds.has(e.target)
  )

  const nodeIdIndex = {}
  filteredNodes.forEach((n, i) => { nodeIdIndex[n.id] = i })

  const nodes = filteredNodes.map((n, i) => ({
    id: n.id,
    name: n.label || n.id,
    symbolSize: Math.max(8, Math.min(40, (n.degree || 1) * 3 + 5)),
    itemStyle: { color: '#16a34a' },
    label: { show: filteredNodes.length <= 50, fontSize: 11, color: '#334155' },
  }))

  const edges = filteredEdges.map(e => ({
    source: nodeIdIndex[e.source],
    target: nodeIdIndex[e.target],
    lineStyle: {
      color: '#bbf7d0',
      width: Math.max(0.5, Math.min(3, (e.weight || 1) * 0.6)),
      curveness: 0.2,
    },
    symbol: ['none', 'arrow'],
    symbolSize: [4, 10],
  }))

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      formatter: (p) => {
        if (p.dataType === 'node') {
          const n = filteredNodes.find(x => x.id === p.data.id)
          return n ? `<b>${n.label || n.id}</b><br/>往来频次: ${n.degree}` : p.name
        }
        const e = filteredEdges[p.dataIndex]
        if (!e) return ''
        const srcLabel = filteredNodes[e.source]?.label || ''
        const tgtLabel = filteredNodes[e.target]?.label || ''
        let tip = `${srcLabel} → ${tgtLabel}`
        if (e.receiveTime) tip += `<br/>接收时间: ${e.receiveTime}`
        return tip
      },
    },
    animationDuration: 800,
    animationEasingUpdate: 'quinticInOut',
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      links: edges,
      roam: true,
      draggable: true,
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: [4, 10],
      force: {
        repulsion: filteredNodes.length > 30 ? 300 : 500,
        gravity: 0.1,
        edgeLength: [50, 200],
        layoutAnimation: true,
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 4 },
      },
      lineStyle: { color: '#86efac', curveness: 0.2, opacity: 0.6 },
    }],
  }

  chart.setOption(option, true)
}

// ==================== 图表初始化函数 ====================
// initChart: 创建 ECharts 实例并绑定交互事件
function initChart() {
  if (!chartRef.value) return
  // 使用 Canvas 渲染器初始化 ECharts 实例
  chart = echarts.init(chartRef.value, null, { renderer: 'canvas' })

  // 禁用浏览器默认的右键菜单（在 echarts canvas 区域内）
  chart.getZr().on('contextmenu', (e) => {
    e.event.preventDefault()
  })

  // 监听 ECharts 的右键事件：仅在右键点击节点时弹出上下文菜单
  chart.on('contextmenu', (params) => {
    if (params.dataType === 'node') {
      ctxMenu.value = {
        visible: true,
        x: params.event.offsetX,
        y: params.event.offsetY,
        nodeId: params.data.id,
        nodeLabel: params.data.name,
      }
    }
  })

  // 监听左键点击事件：若右键菜单已打开，点击时关闭菜单
  chart.on('click', () => {
    if (ctxMenu.value.visible) {
      ctxMenu.value.visible = false
    }
  })

  // 使用 ResizeObserver 监听容器尺寸变化，自动调整图表大小
  const resizeObserver = new ResizeObserver(() => chart?.resize())
  resizeObserver.observe(chartRef.value)
  // 将 observer 挂载到 DOM 元素上，以便组件销毁时能断开连接
  chartRef.value._ro = resizeObserver
}

// ==================== 生命周期钩子 ====================
// onMounted: 组件挂载后初始化图表并执行首次渲染
onMounted(() => {
  nextTick(() => {
    initChart()
    if (props.graphData && chart) {
      renderChart()
    }
  })
})

watch(() => props.graphData, () => {
  if (props.graphData && chart) {
    renderChart()
  }
})

// 监听 deletedNodeIds 变化：当已移除节点列表发生变化时，重新渲染图表
watch(() => props.deletedNodeIds, () => {
  renderChart()
}, { deep: true })

// onUnmounted: 组件销毁时断开 ResizeObserver 并释放 ECharts 实例
onUnmounted(() => {
  chartRef.value?._ro?.disconnect()
  chart?.dispose()
})
</script>

<style scoped>
.network-graph-container { display: flex; flex-direction: column; height: calc(100vh - 200px); position: relative; }
.graph-toolbar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; padding: 10px 16px; background: #ffffff; border-radius: 10px; margin-bottom: 12px; border: 1px solid #22c55e; }
.graph-info { font-size: 13px; color: #475569; }
.graph-info strong { color: #15803d; }
.deleted-info { color: #ef4444; font-size: 12px; margin-left: 6px; }
.graph-controls { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.btn-sm { padding: 4px 10px; font-size: 12px; background: #f0fdf4; color: #15803d; border: 1px solid #22c55e; border-radius: 6px; cursor: pointer; }
.btn-sm:hover { background: #dcfce7; }
.btn-restore { background: #fef2f2; color: #dc2626; border-color: #fca5a5; }
.btn-restore:hover { background: #fee2e2; }
.graph-chart { flex: 1; border-radius: 10px; border: 1px solid #22c55e; background: #ffffff; }

.ctx-menu {
  position: absolute;
  z-index: 50;
  min-width: 140px;
  background: #ffffff;
  border: 1px solid #22c55e;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  padding: 4px 0;
  overflow: hidden;
}
.ctx-menu-item {
  padding: 8px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}
.ctx-menu-title {
  font-weight: 600;
  color: #1e293b;
  cursor: default;
  font-size: 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e2e8f0;
}
.ctx-menu-danger {
  color: #dc2626;
  font-weight: 500;
}
.ctx-menu-danger:hover {
  background: #fef2f2;
}
.ctx-menu-divider {
  height: 1px;
  background: #e2e8f0;
  margin: 2px 0;
}
</style>
