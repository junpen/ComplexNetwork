<!-- 流转概览组件：展示文书流转网络的汇总统计指标、概念说明以及分布图表 -->
<template>
  <div class="overview-container">
    <!-- ==================== 第一部分：核心统计卡片 ==================== -->
    <!-- 使用网格布局展示 6 个关键流转指标，每个卡片可通过 title 属性悬浮查看详细概念说明 -->
    <div class="stat-cards">
      <!-- 统计卡片1：单位总数 —— 参与文书流转的独立节点数 -->
      <div class="stat-card" :title="conceptMap.unit_count">
        <div class="stat-value">{{ summary?.node_count || 0 }}</div>
        <div class="stat-label">单位总数</div>
        <div class="stat-desc">参与文书流转的单位数</div>
      </div>
      <!-- 统计卡片2：文书流转总数 —— 所有有向边的总数量 -->
      <div class="stat-card" :title="conceptMap.flow_count">
        <div class="stat-value">{{ summary?.edge_count || 0 }}</div>
        <div class="stat-label">文书流转总数</div>
        <div class="stat-desc">各单位间收发文书总次数</div>
      </div>
      <!-- 统计卡片3：流转密集度 —— 实际边数占最大可能边数的比例 -->
      <div class="stat-card" :title="conceptMap.density">
        <div class="stat-value">{{ fmt(summary?.density) }}</div>
        <div class="stat-label">流转密集度</div>
        <div class="stat-desc">实际流转占可能组合比例</div>
      </div>
      <!-- 统计卡片4：往来同质性 —— 度同配性系数，衡量活跃单位是否互相连通 -->
      <div class="stat-card" :title="conceptMap.assortativity">
        <div class="stat-value">{{ fmt(features?.network_level_metrics?.assortativity) }}</div>
        <div class="stat-label">往来同质性</div>
        <div class="stat-desc">频繁单位是否倾向互通</div>
      </div>
      <!-- 统计卡片5：平均转发层级 —— 网络中任意两节点间的平均最短路径长度 -->
      <div class="stat-card" :title="conceptMap.avg_path">
        <div class="stat-value">{{ fmt(features?.distance_analysis?.average_shortest_path_length) }}</div>
        <div class="stat-label">平均转发层级</div>
        <div class="stat-desc">文书送达任意单位平均中转数</div>
      </div>
      <!-- 统计卡片6：最大转发跨度 —— 网络直径，即最远两节点间的最短路径长度 -->
      <div class="stat-card" :title="conceptMap.diameter">
        <div class="stat-value">{{ features?.distance_analysis?.diameter || 0 }}</div>
        <div class="stat-label">最大转发跨度</div>
        <div class="stat-desc">最远两单位间的转发层级数</div>
      </div>
    </div>

    <!-- ==================== 第二部分：指标概念说明面板 ==================== -->
    <!-- 以网格卡片形式展示各指标的详细概念解释，方便用户理解每项指标的含义 -->
    <div class="concept-panel">
      <div class="concept-title">💡 指标概念说明</div>
      <div class="concept-grid">
        <!-- 遍历 conceptMap，每项显示指标名称（conceptLabelMap）和详细说明文字 -->
        <div class="concept-item" v-for="(text, key) in conceptMap" :key="key">
          <span class="concept-key">{{ conceptLabelMap[key] }}</span>
          <span class="concept-text">{{ text }}</span>
        </div>
      </div>
    </div>

    <!-- ==================== 第三部分：分布图表区域 ==================== -->
    <div class="overview-grid">
      <!-- 图表1：文书往来频次分布（柱状图）—— 显示 Min/P25/P50/P75/Max 五个百分位值 -->
      <div class="overview-panel">
        <h3 class="panel-title">文书往来频次分布</h3>
        <div class="panel-desc">各单位收发文书的频次统计分布（最小值、P25、中位数、P75、最大值）</div>
        <div ref="degreeChart" class="chart-box"></div>
      </div>
      <!-- 图表2：文书往来频次 Top 10（水平柱状图）—— 收发最频繁的10个单位 -->
      <div class="overview-panel">
        <h3 class="panel-title">文书往来频次 Top 10</h3>
        <div class="panel-desc">收发文书最频繁的前10个单位，反映文书流转的核心参与者</div>
        <div ref="topDegreeChart" class="chart-box"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

// ==================== Props 定义 ====================
// summary: 流转概要统计数据（节点/边数量、类型分布等）
// features: 流转特征指标数据（核心地位分析、聚集度分析、距离分析等）
const props = defineProps({
  summary: { type: Object, default: null },
  features: { type: Object, default: null },
})

// ==================== 指标概念说明数据 ====================
// conceptMap: 各统计指标的详细概念解释，作为卡片的 title 属性和概念面板的文本
const conceptMap = {
  unit_count: '参与文书流转的各单位（如战区、指挥部、部队、阵地、设施等）的总数，每个单位在流转网络中作为一个独立节点。',
  flow_count: '各单位之间文书收发的总次数（具有方向性：发送方→接收方），反映文书流转的总体规模。',
  density: '实际发生的文书流转数占所有可能流转组合的比例。值越高表示各单位之间文书往来覆盖面越广，信息传递渠道越丰富。',
  assortativity: '文书往来同质性，衡量文书往来频繁的单位是否倾向于与其他同样频繁的单位互通。正值表示"强强互通"，负值表示"强弱互补"。',
  avg_path: '一份文书从某个单位发出，平均需要经过多少次中转才能送达任意目标单位。层级越少，说明文书传递效率越高。',
  diameter: '整个文书流转网络中，最远的两个单位之间的转发层级数，反映流转网络的覆盖深度。',
}

// conceptLabelMap: 概念面板中各指标对应的中文标签名称
const conceptLabelMap = {
  unit_count: '单位总数',
  flow_count: '文书流转总数',
  density: '流转密集度',
  assortativity: '往来同质性',
  avg_path: '平均转发层级',
  diameter: '最大转发跨度',
}

// ==================== 图表 DOM 引用 ====================
const degreeChart = ref(null)     // 往来频次分布图
const topDegreeChart = ref(null)  // 往来频次 Top10 图
// charts: 存储所有已创建的 ECharts 实例及其 ResizeObserver，用于统一销毁
const charts = []

// ==================== 工具函数 ====================
// fmt: 格式化数值显示，空值显示 '--'，数字保留4位小数
function fmt(v) {
  if (v == null || v === undefined) return '--'
  return typeof v === 'number' ? v.toFixed(4) : v
}

// ==================== ECharts 配置生成函数 ====================
// pieOption: 生成环形饼图的通用配置（用于单位类型分布和文书类型分布）
function pieOption(data, nameKey, valueKey) {
  return {
    backgroundColor: 'transparent',
    // 提示框触发方式：鼠标悬浮在数据项上
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],   // 内半径40%、外半径70%，形成环形图
      center: ['50%', '55%'],   // 圆心位置稍微下移，给图例留空间
      // 将原始数据映射为 ECharts 饼图数据格式
      data: data.map(d => ({ name: d[nameKey], value: d[valueKey] })),
      // 标签样式
      label: { color: '#475569', fontSize: 11 },
      // 高亮效果：放大标签并添加阴影
      emphasis: {
        label: { fontSize: 14, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.2)' },
      },
    }],
    // 饼图配色方案：绿色为主色调，搭配暖色和冷色辅助色
    color: ['#16a34a', '#f59e0b', '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316', '#84cc16'],
  }
}

// barOption: 生成水平柱状图的通用配置（用于 Top 10 等排名图表）
// 注意：数据会先倒序排列，使排名第一的显示在最上方
function barOption(data, nameKey, valueKey, xName, color = '#16a34a') {
  data = [...data].reverse()
  return {
    backgroundColor: 'transparent',
    // 提示框触发方式：坐标轴触发，配合阴影指示器
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    // 图表边距：左侧留 100px 显示较长的标签名称
    grid: { left: 100, right: 30, top: 10, bottom: 20 },
    // X 轴：数值轴
    xAxis: { type: 'value', axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#e2e8f0' } } },
    // Y 轴：类目轴，显示单位名称，过长时截断
    yAxis: { type: 'category', data: data.map(d => d[nameKey]), axisLabel: { color: '#475569', fontSize: 11, width: 90, overflow: 'truncate' } },
    series: [{
      type: 'bar', data: data.map(d => d[valueKey]),
      // 柱体样式：圆角仅右侧
      itemStyle: { color, borderRadius: [0, 4, 4, 0] },
      // 柱体最大宽度，防止数据量少时柱子过宽
      barMaxWidth: 24,
    }],
  }
}

// ==================== 图表初始化辅助函数 ====================
// initChart: 在指定 DOM 容器上创建 ECharts 实例，设置配置项，并监听容器尺寸变化
function initChart(refVal, option) {
  if (!refVal.value) return
  const c = echarts.init(refVal.value)
  c.setOption(option)
  // 监听容器尺寸变化，自动调整图表大小
  const ro = new ResizeObserver(() => c.resize())
  ro.observe(refVal.value)
  // 保存实例和 observer 引用，便于后续销毁
  charts.push({ chart: c, observer: ro })
}

// ==================== 批量渲染函数 ====================
// renderAll: 销毁旧图表后重新渲染所有图表
function renderAll() {
  // 先销毁所有旧图表并断开 ResizeObserver
  charts.forEach(({ chart, observer }) => {
    observer?.disconnect()
    chart?.dispose()
  })
  charts.length = 0

  // 使用 nextTick 确保 DOM 已更新后再创建图表
  nextTick(() => {
    if (props.features?.degree_analysis) {
      const dist = props.features.degree_analysis.degree_distribution
      if (dist) {
        initChart(degreeChart, {
          backgroundColor: 'transparent',
          tooltip: { trigger: 'axis' },
          grid: { left: 50, right: 20, top: 10, bottom: 30 },
          // X 轴：五个百分位标签
          xAxis: { type: 'category', data: ['Min', 'P25', 'P50', 'P75', 'Max'], axisLabel: { color: '#64748b' } },
          // Y 轴：频次数值
          yAxis: { type: 'value', axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#e2e8f0' } } },
          series: [{
            type: 'bar',
            // 五个百分位对应的频次值
            data: [dist.min, dist.p25, dist.p50, dist.p75, dist.max],
            itemStyle: { color: '#16a34a', borderRadius: 4 },
            barMaxWidth: 30,
            // 标记线：显示均值参考线（黄色）
            markLine: { data: [{ type: 'average', name: '均值', label: { color: '#f59e0b' } }], lineStyle: { color: '#f59e0b' } },
          }],
        })
      }
    }
    // 渲染往来频次 Top 10 水平柱状图
    if (props.features?.degree_analysis?.top_nodes_by_degree) {
      const td = props.features.degree_analysis.top_nodes_by_degree.slice(0, 10)
      initChart(topDegreeChart, barOption(td, 'label', 'degree', '往来频次', '#16a34a'))
    }
  })
}

// ==================== 生命周期钩子 ====================
// 组件挂载时立即执行首次渲染
onMounted(() => renderAll())
// 监听 summary 和 features 变化，任一变化时重新渲染所有图表
watch(() => [props.summary, props.features], renderAll)
// 组件销毁时释放所有 ECharts 实例和 ResizeObserver
onUnmounted(() => {
  charts.forEach(({ chart, observer }) => {
    observer?.disconnect()
    chart?.dispose()
  })
})
</script>

<style scoped>
.overview-container { display: flex; flex-direction: column; gap: 20px; }
.stat-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
.stat-card { background: #ffffff; border: 1px solid #22c55e; border-radius: 10px; padding: 16px; text-align: center; cursor: help; }
.stat-value { font-size: 28px; font-weight: 700; color: #16a34a; }
.stat-label { font-size: 12px; color: #475569; margin-top: 4px; }
.stat-desc { font-size: 10px; color: #94a3b8; margin-top: 2px; }

.concept-panel { background: #ffffff; border: 1px solid #22c55e; border-radius: 10px; padding: 16px; }
.concept-title { font-size: 14px; font-weight: 600; color: #15803d; margin-bottom: 12px; }
.concept-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 10px; }
.concept-item { display: flex; gap: 8px; padding: 8px 12px; background: #f0fdf4; border-radius: 8px; align-items: flex-start; }
.concept-key { font-size: 12px; font-weight: 600; color: #16a34a; white-space: nowrap; min-width: 80px; }
.concept-text { font-size: 12px; color: #475569; line-height: 1.5; }

.overview-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(500px, 1fr)); gap: 16px; }
.overview-panel { background: #ffffff; border: 1px solid #22c55e; border-radius: 10px; padding: 16px; }
.panel-title { font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 4px; }
.panel-desc { font-size: 11px; color: #64748b; margin-bottom: 12px; line-height: 1.4; }
.chart-box { width: 100%; height: 280px; }
</style>
