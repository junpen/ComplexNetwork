<!-- 分析结论报告组件：基于网络分析数据自动生成九个维度的分析结论和综合改进建议，支持导出HTML/文本报告 -->
<template>
  <div class="conclusion-container">
    <!-- 报告头部：标题 + 导出按钮 -->
    <div class="conclusion-header">
      <h2 class="conclusion-main-title">📋 分析结论报告</h2>
      <div class="export-btns">
        <button class="btn btn-primary" @click="exportHTML">📄 导出HTML报告</button>
        <button class="btn btn-outline" @click="exportText">📝 导出文本报告</button>
      </div>
    </div>

    <!-- 报告元信息：数据概况 + 分析时间 -->
    <div class="report-meta" v-if="summary">
      <span>数据概况：{{ summary.node_count || 0 }} 个单位 | {{ summary.edge_count || 0 }} 条文书流转 | 连通分量: {{ features?.distance_analysis?.component_count || '-' }}</span>
      <span>分析时间：{{ reportTime }}（基于最近一次拓扑更新）</span>
    </div>

    <!-- 第一章：流转网络基本结构（网络密度、连通性、转发层级等） -->
    <div class="conclusion-section" v-if="basicConclusion">
      <div class="section-header">
        <span class="section-num">一</span>
        <span class="section-title">流转网络基本结构</span>
        <!-- 风险等级标签 -->
        <span :class="['severity-badge', basicConclusion.severity]">{{ basicConclusion.severityLabel }}</span>
      </div>
      <div class="conclusion-body">
        <p class="conclusion-text">{{ basicConclusion.text }}</p>
        <!-- 指标数据表格 -->
        <div class="data-table" v-if="basicConclusion.stats.length">
          <div class="table-row table-header">
            <span class="col">指标</span><span class="col">数值</span><span class="col">评价</span>
          </div>
          <div class="table-row" v-for="(s, i) in basicConclusion.stats" :key="i">
            <span class="col">{{ s.label }}</span>
            <span class="col highlight">{{ s.value }}</span>
            <!-- 根据评价等级（good/warn/danger）动态设置文字颜色 -->
            <span class="col" :class="s.level">{{ s.eval }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 第二章：文书流转负载均衡性（度分布分析） -->
    <div class="conclusion-section" v-if="degreeConclusion">
      <div class="section-header">
        <span class="section-num">二</span>
        <span class="section-title">文书流转负载均衡性</span>
        <span :class="['severity-badge', degreeConclusion.severity]">{{ degreeConclusion.severityLabel }}</span>
      </div>
      <div class="conclusion-body">
        <p class="conclusion-text">{{ degreeConclusion.text }}</p>
        <!-- 高频次往来单位 Top 5 列表 -->
        <div class="key-nodes" v-if="degreeConclusion.topNodes.length">
          <div class="key-node-title">高频次往来单位 Top 5：</div>
          <div class="key-node-list">
            <div class="key-node-item" v-for="(n, i) in degreeConclusion.topNodes" :key="i">
              <span class="rank">{{ i + 1 }}</span>
              <span class="node-name">{{ n.label }}</span>
              <span class="node-value">频次 {{ n.value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 第三章：核心枢纽与影响力分析（中心性分析） -->
    <div class="conclusion-section" v-if="centralityConclusion">
      <div class="section-header">
        <span class="section-num">三</span>
        <span class="section-title">核心枢纽与影响力分析</span>
        <span :class="['severity-badge', centralityConclusion.severity]">{{ centralityConclusion.severityLabel }}</span>
      </div>
      <div class="conclusion-body">
        <p class="conclusion-text">{{ centralityConclusion.text }}</p>
        <!-- 各维度枢纽单位的洞察卡片 -->
        <div class="insight-cards" v-if="centralityConclusion.insights.length">
          <div class="insight-card" v-for="(ins, i) in centralityConclusion.insights" :key="i">
            <div class="insight-icon">{{ ins.icon }}</div>
            <div class="insight-content">
              <div class="insight-title">{{ ins.title }}</div>
              <div class="insight-detail">{{ ins.detail }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 第四章：流转网络拓扑结构（聚集度、同质性、层级特征） -->
    <div class="conclusion-section" v-if="structureConclusion">
      <div class="section-header">
        <span class="section-num">四</span>
        <span class="section-title">流转网络拓扑结构</span>
        <span :class="['severity-badge', structureConclusion.severity]">{{ structureConclusion.severityLabel }}</span>
      </div>
      <div class="conclusion-body">
        <p class="conclusion-text">{{ structureConclusion.text }}</p>
      </div>
    </div>

    <!-- 第五章：关键单位识别与可替代性 -->
    <div class="conclusion-section" v-if="importanceConclusion">
      <div class="section-header">
        <span class="section-num">五</span>
        <span class="section-title">关键单位识别与可替代性</span>
        <span :class="['severity-badge', importanceConclusion.severity]">{{ importanceConclusion.severityLabel }}</span>
      </div>
      <div class="conclusion-body">
        <p class="conclusion-text">{{ importanceConclusion.text }}</p>
        <!-- 不可替代 / 可替代单位双列对比列表 -->
        <div class="dual-list" v-if="importanceConclusion.irreplaceable.length">
          <div class="dual-col">
            <div class="dual-col-title danger">⚠️ 最不可替代单位</div>
            <div class="dual-item" v-for="(n, i) in importanceConclusion.irreplaceable" :key="'ir'+i">
              <span class="rank danger">{{ i + 1 }}</span>
              <span class="node-name">{{ n.label }}</span>
              <span class="node-value">替代度 {{ n.value }}</span>
            </div>
          </div>
          <div class="dual-col">
            <div class="dual-col-title safe">✅ 最可替代单位</div>
            <div class="dual-item" v-for="(n, i) in importanceConclusion.replaceable" :key="'rp'+i">
              <span class="rank safe">{{ i + 1 }}</span>
              <span class="node-name">{{ n.label }}</span>
              <span class="node-value">替代度 {{ n.value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 第六章：文书流转瓶颈（结构洞）分析 -->
    <div class="conclusion-section" v-if="structuralHoleConclusion">
      <div class="section-header">
        <span class="section-num">六</span>
        <span class="section-title">文书流转瓶颈（结构洞）分析</span>
        <span :class="['severity-badge', structuralHoleConclusion.severity]">{{ structuralHoleConclusion.severityLabel }}</span>
      </div>
      <div class="conclusion-body">
        <p class="conclusion-text">{{ structuralHoleConclusion.text }}</p>
      </div>
    </div>

    <!-- 第七章：流转稳定性与脆弱性评估 -->
    <div class="conclusion-section" v-if="resilienceConclusion">
      <div class="section-header">
        <span class="section-num">七</span>
        <span class="section-title">流转稳定性与脆弱性评估</span>
        <span :class="['severity-badge', resilienceConclusion.severity]">{{ resilienceConclusion.severityLabel }}</span>
      </div>
      <div class="conclusion-body">
        <p class="conclusion-text">{{ resilienceConclusion.text }}</p>
        <!-- 稳定性指标数据表格 -->
        <div class="data-table" v-if="resilienceConclusion.stats.length">
          <div class="table-row table-header">
            <span class="col">指标</span><span class="col">数值</span><span class="col">评价</span>
          </div>
          <div class="table-row" v-for="(s, i) in resilienceConclusion.stats" :key="i">
            <span class="col">{{ s.label }}</span>
            <span class="col highlight">{{ s.value }}</span>
            <span class="col" :class="s.level">{{ s.eval }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 第八章：扰动模拟与抗毁性 -->
    <div class="conclusion-section" v-if="attackConclusion">
      <div class="section-header">
        <span class="section-num">八</span>
        <span class="section-title">扰动模拟与抗毁性</span>
        <span :class="['severity-badge', attackConclusion.severity]">{{ attackConclusion.severityLabel }}</span>
      </div>
      <div class="conclusion-body">
        <p class="conclusion-text">{{ attackConclusion.text }}</p>
      </div>
    </div>

    <!-- 第九章：连锁失效风险评估 -->
    <div class="conclusion-section" v-if="cascadeConclusion">
      <div class="section-header">
        <span class="section-num">九</span>
        <span class="section-title">连锁失效风险评估</span>
        <span :class="['severity-badge', cascadeConclusion.severity]">{{ cascadeConclusion.severityLabel }}</span>
      </div>
      <div class="conclusion-body">
        <p class="conclusion-text">{{ cascadeConclusion.text }}</p>
      </div>
    </div>

    <!-- 综合结论与改进建议（核心发现 + 改进建议） -->
    <div class="conclusion-section summary-section" v-if="summaryConclusion">
      <div class="section-header">
        <span class="section-num">★</span>
        <span class="section-title">综合结论与改进建议</span>
      </div>
      <div class="conclusion-body">
        <!-- 核心发现列表 -->
        <div class="findings" v-if="summaryConclusion.findings.length">
          <div class="finding-title">🔴 核心发现</div>
          <div class="finding-item" v-for="(f, i) in summaryConclusion.findings" :key="'f'+i">
            <span :class="['finding-severity', f.level]">{{ f.levelLabel }}</span>
            <span class="finding-text">{{ f.text }}</span>
          </div>
        </div>
        <!-- 改进建议列表 -->
        <div class="suggestions" v-if="summaryConclusion.suggestions.length">
          <div class="finding-title suggestion-title">🟢 改进建议</div>
          <div class="suggestion-item" v-for="(s, i) in summaryConclusion.suggestions" :key="'s'+i">
            <span class="suggestion-num">{{ i + 1 }}</span>
            <span class="suggestion-text">{{ s }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

// 接收父组件传入的四个数据源：网络摘要、特征指标、关键单位分析、稳定性/风险分析
const props = defineProps({
  summary: { type: Object, default: null },       // 网络基本统计（节点数、边数、密度等）
  features: { type: Object, default: null },       // 网络特征指标（度分布、中心性、聚集度等）
  importance: { type: Object, default: null },     // 关键单位分析（综合重要度、可替代性等）
  resilience: { type: Object, default: null },     // 稳定性/风险分析（韧性、脆弱性、扰动模拟等）
})

// 报告生成时间，用于展示和导出文件名
const reportTime = ref('')

// 监听任一数据源变化时更新报告时间戳
watch(
  () => [props.summary, props.features, props.importance, props.resilience],
  () => {
    if (props.summary) {
      const d = new Date()
      reportTime.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
    }
  }
)

/**
 * 数值格式化函数
 * @param {*} v - 待格式化的值
 * @param {number} d - 保留小数位数，默认4位
 * @returns {string} 格式化后的字符串，空值返回'--'
 */
function fmt(v, d = 4) {
  if (v == null || v === undefined) return '--'
  return typeof v === 'number' ? v.toFixed(d) : v
}

/**
 * 生成风险等级对象（包含等级标识和中文标签）
 * @param {string} level - 风险等级：high/mid/low/good
 * @returns {Object} { severity, severityLabel }
 */
function sev(level) {
  const map = { high: '高风险', mid: '中风险', low: '低风险', good: '良好' }
  return { severity: level, severityLabel: map[level] || level }
}

/**
 * 根据阈值数组判断值所属的评价等级
 * @param {number} val - 待评估的值
 * @param {number[]} thresholds - 阈值数组（升序）
 * @param {string[]} labels - 对应的等级标签数组
 * @returns {string} 评价标签
 */
function evalLevel(val, thresholds, labels) {
  for (let i = 0; i < thresholds.length; i++) {
    if (val < thresholds[i]) return labels[i]
  }
  return labels[labels.length - 1]
}

/**
 * 计算属性一：流转网络基本结构结论
 * 分析网络密度、连通性、平均转发层级等基本结构特征
 */
const basicConclusion = computed(() => {
  const s = props.summary
  const f = props.features
  if (!s || !f?.distance_analysis) return null
  const density = s.density || 0                    // 网络密度（0~1）
  const avgPath = f.distance_analysis.average_shortest_path_length || 0   // 平均最短路径长度
  const diameter = f.distance_analysis.diameter || 0                       // 网络直径
  const connected = f.distance_analysis.is_connected                       // 是否全连通
  const components = f.distance_analysis.component_count || 1              // 连通分量数

  let text = `当前文书流转网络包含 ${s.node_count} 个单位、${s.edge_count} 条文书流转。`
  if (connected) {
    text += `网络为全连通状态（单一连通分量），所有单位之间均可通过文书链路相互到达。`
  } else {
    text += `网络存在 ${components} 个连通分量，部分单位之间无法通过文书链路到达。`
  }
  text += `流转密集度为 ${fmt(density)}，`
  // 密度判断：<0.15 稀疏，0.15~0.3 中等，>0.3 密集
  if (density < 0.15) text += `属于稀疏网络，大部分单位对之间没有直接文书往来。`
  else if (density < 0.3) text += `属于中等密度网络。`
  else text += `属于密集网络，单位之间文书往来覆盖面较广。`
  text += `平均转发层级为 ${fmt(avgPath, 1)}，最大转发跨度为 ${diameter}。`

  return {
    text,
    // 密度低于0.15判定为中风险，否则为良好
    ...sev(density < 0.15 ? 'mid' : 'good'),
    stats: [
      { label: '流转密集度', value: fmt(density), eval: density < 0.15 ? '偏低' : density < 0.3 ? '适中' : '良好', level: density < 0.15 ? 'warn' : 'good' },
      // 平均转发层级：≤2 高效，≤3.5 适中，>3.5 偏长
      { label: '平均转发层级', value: fmt(avgPath, 1), eval: avgPath <= 2 ? '高效' : avgPath <= 3.5 ? '适中' : '偏长', level: avgPath > 3.5 ? 'warn' : 'good' },
      // 最大转发跨度：≤4 较浅，≤6 适中，>6 较深
      { label: '最大转发跨度', value: diameter, eval: diameter <= 4 ? '较浅' : diameter <= 6 ? '适中' : '较深', level: diameter > 6 ? 'warn' : 'good' },
      // 连通分量数：1 全连通，>1 存在孤岛
      { label: '连通分量数', value: components, eval: components === 1 ? '全连通' : `${components}个孤岛`, level: components > 1 ? 'danger' : 'good' },
    ]
  }
})

/**
 * 计算属性二：文书流转负载均衡性结论
 * 分析度分布的均值、标准差、变异系数，评估负载是否集中
 */
const degreeConclusion = computed(() => {
  const f = props.features
  if (!f?.degree_analysis) return null
  const da = f.degree_analysis
  const mean = da.degree_distribution?.mean || 0      // 加权平均往来频次
  const std = da.degree_distribution?.std || 0         // 标准差
  const maxD = da.max_degree || 0                       // 最高频次
  const minD = da.min_degree || 0                       // 最低频次
  const ratio = minD > 0 ? (maxD / minD).toFixed(1) : '∞'  // 最大/最小频次比
  const cv = mean > 0 ? (std / mean).toFixed(2) : 0    // 变异系数

  // 提取Top5高频次单位
  const topNodes = (da.top_nodes_by_degree || []).slice(0, 5).map(n => ({
    label: n.label, value: fmt(n.degree, 1)
  }))

  let text = `文书流转负载分布极不均衡。加权平均往来频次为 ${fmt(mean, 1)}，标准差高达 ${fmt(std, 1)}，变异系数为 ${cv}。`
  text += `最高频次单位（${topNodes[0]?.label || '--'}，${fmt(maxD, 1)}）与最低频次单位之间差距达 ${ratio} 倍。`
  // 变异系数超过0.7说明负载严重集中
  if (cv > 0.7) {
    text += `变异系数超过0.7，表明文书流转负载严重集中于少数核心单位，存在明显的"超级节点"现象。`
  }

  // 风险等级判定：变异系数>0.8 高风险，>0.5 中风险，否则低风险
  return { text, topNodes, ...sev(cv > 0.8 ? 'high' : cv > 0.5 ? 'mid' : 'low') }
})

/**
 * 计算属性三：核心枢纽与影响力分析结论
 * 综合中心性指标，识别各维度的枢纽单位
 */
const centralityConclusion = computed(() => {
  const f = props.features
  const imp = props.importance
  if (!f?.centrality_analysis || !imp?.comprehensive_importance) return null

  const ca = f.centrality_analysis
  // 各维度中心性排名第一的单位
  const topDC = ca.degree_centrality?.top_nodes?.[0]       // 往来活跃度最高
  const topBC = ca.betweenness_centrality?.top_nodes?.[0]   // 最大文书枢纽
  const topCC = ca.closeness_centrality?.top_nodes?.[0]     // 流转可达性最高
  const topPR = ca.pagerank?.top_nodes?.[0]                 // 文书影响力最强
  const topImp = imp.comprehensive_importance.top_important_nodes?.[0]    // 综合评分第一
  const secondImp = imp.comprehensive_importance.top_important_nodes?.[1] // 综合评分第二

  // 构建各维度枢纽单位的洞察卡片数据
  const insights = []
  if (topDC) insights.push({
    icon: '📡', title: `${topDC.label} — 往来活跃度最高`,
    detail: `活跃度 ${fmt(topDC.value)}，与 ${fmt(topDC.value * 100 / (props.summary?.node_count || 1), 1)}% 的单位有直接文书往来`
  })
  if (topBC) insights.push({
    icon: '🔀', title: `${topBC.label} — 最大文书枢纽`,
    detail: `枢纽度 ${fmt(topBC.value)}，${fmt(topBC.value * 100, 1)}% 的最短文书传递路径经过此单位`
  })
  if (topCC) insights.push({
    icon: '⚡', title: `${topCC.label} — 流转可达性最高`,
    detail: `可达性 ${fmt(topCC.value)}，文书传递效率最高`
  })
  if (topPR) insights.push({
    icon: '🏆', title: `${topPR.label} — 文书影响力最强`,
    detail: `PageRank值 ${fmt(topPR.value)}`
  })

  let text = ''
  if (topImp && secondImp) {
    // 计算第一名与第二名的综合评分差距百分比
    const gap = ((topImp.comprehensive_score - secondImp.comprehensive_score) / secondImp.comprehensive_score * 100).toFixed(1)
    text = `综合枢纽评分中，${topImp.label}（${fmt(topImp.comprehensive_score)}）排名第一，比第二名 ${secondImp.label}（${fmt(secondImp.comprehensive_score)}）高出 ${gap}%。`
    // 判断是否为"绝对核心枢纽"：活跃度、枢纽度、影响力三个维度均排名第一
    if (topImp.node === topBC?.node && topImp.node === topDC?.node) {
      text += `${topImp.label}在往来活跃度、枢纽度、影响力等多个维度均位列第一，构成了文书流转网络的绝对核心枢纽。`
    }
    // 可达性最高的单位与综合评分第一不同，说明最高效的信息分发节点另有其人
    if (topImp.node !== topCC?.node) {
      text += `值得注意的是，流转可达性最高的单位是 ${topCC.label}（${fmt(topCC.value)}），说明从该单位发出的文书可以最少的层级送达所有单位，是最高效的信息分发节点。`
    }
  }

  // 枢纽度>0.4判定为高风险（过度依赖单一枢纽），否则中风险
  return { text, insights, ...sev(topBC?.value > 0.4 ? 'high' : 'mid') }
})

/**
 * 计算属性四：流转网络拓扑结构结论
 * 分析聚集度、同质性、幂律特征，判断网络的层级结构和协作模式
 */
const structureConclusion = computed(() => {
  const f = props.features
  if (!f?.clustering_analysis || !f?.network_level_metrics) return null
  const avgClustering = f.clustering_analysis.average_clustering_coefficient || 0   // 平均聚集系数
  const assort = f.network_level_metrics.assortativity || 0                          // 度同质性系数
  const powerLaw = f.network_level_metrics.power_law_exponent || 0                   // 幂律指数
  const triangles = f.clustering_analysis.triangles_per_node?.total_triangles || 0   // 三角关系总数

  let text = `平均流转聚集度为 ${fmt(avgClustering)}，`
  // 聚集度判断：<0.1 几乎无横向协作，<0.3 较低，≥0.3 较高
  if (avgClustering < 0.1) text += `接近于零，说明几乎不存在"三角文书往来"（即A↔B、B↔C、A↔C三方互通的情况极少），文书流转严格遵循层级传递模式，横向直接沟通非常有限。`
  else if (avgClustering < 0.3) text += `处于较低水平，表明部分单位之间存在小范围的互通圈子。`
  else text += `较高，表明单位之间存在较为活跃的横向文书往来。`

  text += `往来同质性系数为 ${fmt(assort)}，`
  // 同质性判断：>0.1 强强互通，-0.1~0.1 无偏好，<-0.1 强弱互补
  if (assort > 0.1) text += `为正值，表示往来频繁的单位倾向于与其他频繁单位互通（"强强互通"）。`
  else if (assort > -0.1) text += `接近零，表示往来模式无明显偏好。`
  else text += `为负值，表示核心枢纽单位主要与边缘单位往来（"强弱互补"）。`

  // 幂律指数接近1表示无标度网络特征（典型的层级指挥结构）
  if (Math.abs(powerLaw - 1) < 0.5) {
    text += `幂律指数为 ${fmt(powerLaw, 2)}，接近1，网络呈现近似无标度特征，少数核心单位连接大量边缘单位，属于典型的层级指挥结构。`
  }
  text += `网络中共有 ${triangles} 个三角关系。`

  // 聚集度<0.1判定为中风险（横向协作不足），否则低风险
  return { text, ...sev(avgClustering < 0.1 ? 'mid' : 'low') }
})

/**
 * 计算属性五：关键单位识别与可替代性结论
 * 识别最不可替代/最可替代的单位，评估关键单位撤除影响
 */
const importanceConclusion = computed(() => {
  const imp = props.importance
  if (!imp?.substitutability || !imp?.key_player_analysis) return null

  // 最不可替代单位Top5（替代度最低）
  const irreplaceable = (imp.substitutability.top_irreplaceable_nodes || []).slice(0, 5).map(n => ({
    label: n.label, value: fmt(n.substitutability_score)
  }))
  // 最可替代单位Top5（替代度最高）
  const replaceable = (imp.substitutability.top_substitutable_nodes || []).slice(0, 5).map(n => ({
    label: n.label, value: fmt(n.substitutability_score)
  }))
  const topKP = imp.key_player_analysis.top_key_players?.[0]     // 撤除影响最大的单位
  const secondKP = imp.key_player_analysis.top_key_players?.[1]  // 撤除影响第二大的单位

  let text = ''
  if (irreplaceable.length > 0) {
    text += `可替代程度最低的单位为 ${irreplaceable.map(n => n.label).join('、')}，`
    text += `这些单位在网络中承担着不可替代的独特功能，一旦缺失将严重影响文书流转体系。`
  }
  if (topKP) {
    text += `关键单位移除影响分析显示，移除 ${topKP.label} 对网络的破坏最大（影响得分 ${fmt(topKP.impact_score)}）。`
    if (secondKP) {
      text += `其次是 ${secondKP.label}（${fmt(secondKP.impact_score)}）。`
    }
  }

  // 不可替代单位>3个判定为高风险，否则中风险
  return { text, irreplaceable, replaceable, ...sev(irreplaceable.length > 3 ? 'high' : 'mid') }
})

/**
 * 计算属性六：文书流转瓶颈（结构洞）分析结论
 * 识别占据不同群体之间"桥梁"位置的瓶颈单位
 */
const structuralHoleConclusion = computed(() => {
  const imp = props.importance
  if (!imp?.structural_holes?.top_structural_hole_nodes?.length) return null

  const sh = imp.structural_holes.top_structural_hole_nodes
  const top = sh[0]        // 最大结构洞位置
  const second = sh[1]     // 第二大结构洞位置
  const third = sh[2]      // 第三大结构洞位置

  let text = `${top.label} 占据了最大的结构洞位置（约束值 ${fmt(top.constraint)}，有效规模 ${fmt(top.effective_size, 1)}），`
  text += `连接了网络中最多元的不同群体，且这些群体之间缺乏直接联系。`
  if (second) {
    text += `${second.label} 排名第二（约束值 ${fmt(second.constraint)}），`
    text += `是跨越不同子系统的关键桥梁。`
  }
  if (third) {
    text += `${third.label} 排名第三（约束值 ${fmt(third.constraint)}），在文书流转中承担重要的信息中转角色。`
  }
  text += `这些瓶颈单位是维持全网文书互通的关键节点，一旦失效将导致多个群体之间失去联系。`

  return { text, ...sev('mid') }
})

/**
 * 计算属性七：流转稳定性与脆弱性评估结论
 * 综合韧性评分、边连通度、关键枢纽单位数等指标评估网络稳定性
 */
const resilienceConclusion = computed(() => {
  const r = props.resilience
  if (!r?.resilience_metrics || !r?.vulnerability_metrics) return null

  const rm = r.resilience_metrics
  const vm = r.vulnerability_metrics
  const score = rm.resilience_score || 0               // 综合稳定性评分（0~1）
  const nc = rm.natural_connectivity || 0               // 自然连通性
  const ac = rm.algebraic_connectivity || 0             // 代数连通度
  const edgeConn = rm.edge_connectivity || 0            // 边连通度
  const avgNodeConn = rm.average_node_connectivity || 0 // 平均节点连通度
  const apCount = vm.articulation_points_count || 0     // 关键枢纽单位（关节点）数量
  const bridgeCount = vm.bridges_count || 0             // 唯一文书通道（桥接边）数量

  let text = `综合流转稳定性评分为 ${fmt(score)}，`
  // 稳定性评分判断：<0.4 较差，<0.65 中等，≥0.65 良好
  if (score < 0.4) text += `属于较差水平，网络抗毁性薄弱。`
  else if (score < 0.65) text += `处于中等水平，尚可但存在明显短板。`
  else text += `属于良好水平，网络具备较强的抗毁能力。`

  text += `边连通度仅为 ${edgeConn}，意味着只需移除 ${edgeConn} 条关键文书通道即可导致网络分裂。`
  text += `网络中存在 ${apCount} 个关键枢纽单位和 ${bridgeCount} 条唯一文书通道。`

  // 关键枢纽单位>3时，列出具体名称
  if (apCount > 3) {
    const apNames = (vm.articulation_points || []).slice(0, 4).map(a => a.label).join('、')
    text += `关键枢纽单位包括：${apNames} 等。`
  }

  const stats = [
    // 综合稳定性评分评价：<0.4 较差，<0.65 中等，≥0.65 良好
    { label: '综合稳定性评分', value: fmt(score), eval: score < 0.4 ? '较差' : score < 0.65 ? '中等' : '良好', level: score < 0.4 ? 'danger' : score < 0.65 ? 'warn' : 'good' },
    // 边连通度评价：≤1 极低，≤2 偏低，>2 尚可
    { label: '边连通度', value: edgeConn, eval: edgeConn <= 1 ? '极低' : edgeConn <= 2 ? '偏低' : '尚可', level: edgeConn <= 1 ? 'danger' : edgeConn <= 2 ? 'warn' : 'good' },
    // 平均节点连通度评价：<2 低，<3 中等，≥3 良好
    { label: '平均节点连通度', value: fmt(avgNodeConn), eval: avgNodeConn < 2 ? '低' : avgNodeConn < 3 ? '中等' : '良好', level: avgNodeConn < 2 ? 'warn' : 'good' },
    // 关键枢纽单位数评价：>5 较多，>2 中等，≤2 较少
    { label: '关键枢纽单位数', value: apCount, eval: apCount > 5 ? '较多' : apCount > 2 ? '中等' : '较少', level: apCount > 5 ? 'danger' : apCount > 2 ? 'warn' : 'good' },
    // 唯一文书通道数评价：>5 较多，>2 中等，≤2 较少
    { label: '唯一文书通道数', value: bridgeCount, eval: bridgeCount > 5 ? '较多' : bridgeCount > 2 ? '中等' : '较少', level: bridgeCount > 5 ? 'danger' : bridgeCount > 2 ? 'warn' : 'good' },
  ]

  // 综合风险等级：<0.4 高风险，<0.65 中风险，≥0.65 良好
  return { text, stats, ...sev(score < 0.4 ? 'high' : score < 0.65 ? 'mid' : 'good') }
})

/**
 * 计算属性八：扰动模拟与抗毁性结论
 * 比较随机扰动与定向攻击对网络的影响，评估抗毁能力
 */
const attackConclusion = computed(() => {
  const r = props.resilience
  if (!r?.attack_simulation?.comparison || !r?.robustness_curves?.area_under_curve) return null

  const auc = r.robustness_curves.area_under_curve                     // 各策略AUC值
  const ranking = r.robustness_curves.robustness_ranking || []         // 鲁棒性排名
  const randomAuc = auc.random || 0                                     // 随机扰动AUC
  const targetedAucs = Object.entries(auc).filter(([k]) => k !== 'random').map(([, v]) => v)  // 定向攻击AUC
  const worstTargeted = Math.min(...targetedAucs)                       // 最脆弱的定向策略AUC
  const ratio = worstTargeted > 0 ? (randomAuc / worstTargeted).toFixed(1) : '∞'  // 定向/随机倍率

  let text = `鲁棒性测试中，随机撤除策略的AUC为 ${fmt(randomAuc)}，`
  const worstStrategy = ranking.length > 0 ? ranking[ranking.length - 1] : null
  if (worstStrategy) {
    text += `而最脆弱的定向策略（${worstStrategy[0]}）AUC仅为 ${fmt(worstStrategy[1])}。`
  }
  text += `定向攻击的破坏力约为随机扰动的 ${ratio} 倍，`
  text += `说明网络对精准打击极为脆弱，只需精准移除少数关键单位即可使文书流转体系大面积瘫痪。`

  // 各策略平均连通保持率对比
  const comp = r.attack_simulation.comparison
  const strategies = Object.entries(comp)
  if (strategies.length > 0) {
    text += ` 各策略平均连通保持率：${strategies.map(([k, v]) => `${k === 'random' ? '随机' : k}(${fmt(v.mean_lcc_ratio)})`).join('、')}。`
  }

  // 随机AUC<0.3判定为高风险，否则中风险
  return { text, ...sev(randomAuc < 0.3 ? 'high' : 'mid') }
})

/**
 * 计算属性九：连锁失效风险评估结论
 * 评估各单位触发连锁崩溃的风险程度和容量阈值分析
 */
const cascadeConclusion = computed(() => {
  const r = props.resilience
  if (!r?.cascading_failure_analysis?.detailed_cascades) return null

  const dc = r.cascading_failure_analysis.detailed_cascades || []     // 各单位的连锁失效详情
  const cap = r.cascading_failure_analysis.capacity_threshold_analysis || {}  // 容量阈值分析
  const n = props.summary?.node_count || 1                             // 网络总单位数

  // 找到影响范围最大的连锁失效触发点
  const worst = [...dc].sort((a, b) => b.affected_nodes - a.affected_nodes)[0]
  const worstRatio = worst ? (worst.affected_nodes / n * 100).toFixed(1) : 0

  // 按阈值数值升序排列容量阈值分析结果
  const capEntries = Object.entries(cap).sort((a, b) => {
    const ka = parseFloat(a[0].replace('threshold_', ''))
    const kb = parseFloat(b[0].replace('threshold_', ''))
    return ka - kb
  })

  let text = ''
  if (worst) {
    text += `连锁失效分析显示，以 ${worst.label} 为触发点将引发最大规模的连锁崩溃，波及 ${worst.affected_nodes} 个单位（占总数的 ${worstRatio}%）。`
  }
  if (dc.length > 1) {
    // 列出Top3高风险触发点
    const top3 = [...dc].sort((a, b) => b.affected_nodes - a.affected_nodes).slice(0, 3)
    text += `高风险触发点依次为：${top3.map(d => `${d.label}(${d.affected_nodes}个单位)`).join('、')}。`
  }
  if (capEntries.length > 0) {
    // 最低容量阈值（0.5倍）下的连锁规模
    const lowThreshold = capEntries[0][1]
    text += `当单位容量阈值仅为平均值0.5倍时，平均连锁规模达 ${fmt(lowThreshold.avg_cascade_size, 1)} 个单位（${fmt(lowThreshold.avg_cascade_size / n * 100, 1)}%）。`
  }

  // 波及比例>40% 高风险，>20% 中风险，≤20% 低风险
  return { text, ...sev(worstRatio > 40 ? 'high' : worstRatio > 20 ? 'mid' : 'low') }
})

/**
 * 计算属性★：综合结论与改进建议
 * 汇总所有分析的核心发现，并给出针对性改进建议
 */
const summaryConclusion = computed(() => {
  // 四个数据源必须齐全才能生成综合结论
  if (!props.summary || !props.features || !props.importance || !props.resilience) return null

  const findings = []       // 核心发现列表
  const suggestions = []    // 改进建议列表

  const f = props.features
  const imp = props.importance
  const r = props.resilience

  // 发现1：检查是否存在"超级节点"（综合评分比第二名高出20%以上）
  const topImp = imp.comprehensive_importance?.top_important_nodes?.[0]
  if (topImp) {
    const second = imp.comprehensive_importance?.top_important_nodes?.[1]
    const gap = second ? ((topImp.comprehensive_score - second.comprehensive_score) / second.comprehensive_score * 100).toFixed(0) : 0
    if (gap > 20) {
      findings.push({
        level: 'high', levelLabel: '高风险',
        text: `${topImp.label} 是文书流转的绝对核心超级节点，综合评分（${fmt(topImp.comprehensive_score)}）比第二名高出 ${gap}%，指挥信息高度集中`
      })
    }
  }

  // 发现2：边连通度≤1（移除1条关键通道即导致网络分裂）
  const edgeConn = r.resilience_metrics?.edge_connectivity || 0
  if (edgeConn <= 1) {
    findings.push({
      level: 'high', levelLabel: '极高风险',
      text: `网络边连通度仅为 ${edgeConn}，移除1条关键文书通道即可导致网络分裂`
    })
    suggestions.push('增加冗余文书通道，为关键桥接边建立替代路径，确保网络边连通度至少提升到2以上')
  }

  // 发现3：桥接边>3（过多"生命线"通道）
  const bridgeCount = r.vulnerability_metrics?.bridges_count || 0
  if (bridgeCount > 3) {
    findings.push({
      level: 'high', levelLabel: '高风险',
      text: `存在 ${bridgeCount} 条"生命线"文书通道（桥接边），任一中断将导致部分单位完全失联`
    })
  }

  // 发现4：关键单位撤除影响最大的单位
  const topKP = imp.key_player_analysis?.top_key_players?.[0]
  if (topKP) {
    findings.push({
      level: 'mid', levelLabel: '中风险',
      text: `${topKP.label} 的移除对网络破坏最大（影响得分 ${fmt(topKP.impact_score)}），需重点保障其文书通信稳定性`
    })
  }

  // 发现5：最大连锁失效风险评估
  const worstCascade = (r.cascading_failure_analysis?.detailed_cascades || []).sort((a, b) => b.affected_nodes - a.affected_nodes)[0]
  if (worstCascade) {
    const n = props.summary?.node_count || 1
    const pct = (worstCascade.affected_nodes / n * 100).toFixed(0)
    // 波及比例>40% 高风险，否则中风险
    findings.push({
      level: worstCascade.affected_nodes / n > 0.4 ? 'high' : 'mid',
      levelLabel: worstCascade.affected_nodes / n > 0.4 ? '高风险' : '中风险',
      text: `${worstCascade.label} 失效将引发最大连锁崩溃，波及 ${worstCascade.affected_nodes} 个单位（${pct}%）`
    })
  }

  // 发现6：聚集度极低（横向协作不足）
  const clustering = f.clustering_analysis?.average_clustering_coefficient || 0
  if (clustering < 0.1) {
    findings.push({
      level: 'mid', levelLabel: '中风险',
      text: '网络聚集度极低，横向协作通道几乎为零，文书流转严格呈树状层级结构'
    })
    suggestions.push('加强同级单位之间的直接文书通报机制，提高横向协作能力')
  }

  // 建议：网络密度低时增加流转覆盖面
  const density = props.summary?.density || 0
  if (density < 0.15) {
    suggestions.push('增加文书流转覆盖面，在关键单位之间建立更多直接通信渠道')
  }

  // 建议：分散核心枢纽单位的负载
  if (topImp) {
    suggestions.push(`分散 ${topImp.label} 的文书信息负载，将部分分发职能下放至次要枢纽单位`)
  }

  // 建议：定向攻击远比随机扰动致命时，建立应急预案
  const auc = r.robustness_curves?.area_under_curve || {}
  const targetedAucs = Object.entries(auc).filter(([k]) => k !== 'random')
  if (targetedAucs.length > 0) {
    const worstTarget = Math.min(...targetedAucs.map(([, v]) => v))
    const randomAuc = auc.random || 0
    // 定向/随机倍率>2时建议建立应急预案
    if (randomAuc / worstTarget > 2) {
      suggestions.push('建立应急预案，针对定向攻击场景预先设计文书流转的替代链路')
    }
  }

  // 通用建议：保护关键枢纽和唯一通道
  suggestions.push('对关键枢纽单位和唯一文书通道实施最高级别的通信保障')

  return { findings, suggestions }
})

/**
 * 获取所有分析结论章节（用于报告生成）
 * @returns {Array} 包含10个章节标题和数据的数组
 */
function getAllConclusions() {
  const sections = [
    { title: '一、流转网络基本结构', data: basicConclusion.value },
    { title: '二、文书流转负载均衡性', data: degreeConclusion.value },
    { title: '三、核心枢纽与影响力分析', data: centralityConclusion.value },
    { title: '四、流转网络拓扑结构', data: structureConclusion.value },
    { title: '五、关键单位识别与可替代性', data: importanceConclusion.value },
    { title: '六、文书流转瓶颈（结构洞）分析', data: structuralHoleConclusion.value },
    { title: '七、流转稳定性与脆弱性评估', data: resilienceConclusion.value },
    { title: '八、扰动模拟与抗毁性', data: attackConclusion.value },
    { title: '九、连锁失效风险评估', data: cascadeConclusion.value },
    { title: '★ 综合结论与改进建议', data: summaryConclusion.value },
  ]
  return sections
}

/**
 * 构建HTML格式的完整分析报告
 * 包含内联CSS样式，可直接在浏览器中打开查看或打印
 * @returns {string} 完整的HTML字符串
 */
function buildHTMLReport() {
  const sections = getAllConclusions()
  let html = `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>文书流转分析结论报告</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:960px;margin:0 auto;padding:32px;background:#f8faf8;color:#1e293b;line-height:1.7;}
h1{color:#15803d;border-bottom:3px solid #22c55e;padding-bottom:12px;font-size:24px;}
.meta{color:#64748b;font-size:13px;margin:12px 0 24px;}
.section{background:#fff;border:1px solid #bbf7d0;border-radius:10px;padding:20px;margin-bottom:16px;}
.section-title{font-size:16px;font-weight:700;color:#15803d;margin-bottom:8px;}
.severity{display:inline-block;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;margin-left:8px;}
.severity.high{background:#fef2f2;color:#dc2626;border:1px solid #fca5a5;}
.severity.mid{background:#fffbeb;color:#d97706;border:1px solid #fcd34d;}
.severity.low{background:#f0fdf4;color:#16a34a;border:1px solid #86efac;}
.severity.good{background:#f0fdf4;color:#16a34a;border:1px solid #86efac;}
.conclusion-text{font-size:14px;color:#334155;margin:8px 0;}
table{width:100%;border-collapse:collapse;margin:12px 0;}
th,td{padding:8px 12px;text-align:left;border-bottom:1px solid #e2e8f0;font-size:13px;}
th{background:#f0fdf4;color:#15803d;font-weight:600;}
.good{color:#16a34a;} .warn{color:#d97706;} .danger{color:#dc2626;}
.finding{display:flex;gap:8px;padding:8px 0;align-items:flex-start;}
.finding-sev{font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px;white-space:nowrap;}
.suggestion{display:flex;gap:8px;padding:6px 0;align-items:flex-start;}
.suggestion-num{background:#16a34a;color:#fff;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0;}
.insight{display:flex;gap:10px;padding:8px 0;}
.insight-icon{font-size:20px;}
.footer{text-align:center;color:#94a3b8;font-size:12px;margin-top:24px;padding-top:12px;border-top:1px solid #e2e8f0;}
</style></head><body>`
  html += `<h1>📋 多源异构文书流转分析结论报告</h1>`
  html += `<div class="meta">数据概况：${props.summary?.node_count || 0} 个单位 | ${props.summary?.edge_count || 0} 条文书流转 | 分析时间：${reportTime.value}（基于最近一次拓扑更新）</div>`

  // 遍历所有章节，生成HTML内容
  for (const sec of sections) {
    if (!sec.data) continue
    const d = sec.data
    html += `<div class="section">`
    html += `<div class="section-title">${sec.title}`
    if (d.severity) html += `<span class="severity ${d.severity}">${d.severityLabel || ''}</span>`
    html += `</div>`
    if (d.text) html += `<p class="conclusion-text">${d.text}</p>`

    // 指标数据表格
    if (d.stats?.length) {
      html += `<table><tr><th>指标</th><th>数值</th><th>评价</th></tr>`
      for (const s of d.stats) {
        html += `<tr><td>${s.label}</td><td><b>${s.value}</b></td><td class="${s.level}">${s.eval}</td></tr>`
      }
      html += `</table>`
    }
    // 洞察卡片
    if (d.insights?.length) {
      for (const ins of d.insights) {
        html += `<div class="insight"><div class="insight-icon">${ins.icon}</div><div><b>${ins.title}</b><br><span style="color:#64748b;font-size:13px;">${ins.detail}</span></div></div>`
      }
    }
    // 不可替代单位列表
    if (d.irreplaceable?.length) {
      html += `<p style="font-weight:600;color:#dc2626;margin-top:12px;">⚠️ 最不可替代单位：</p><ul>`
      for (const n of d.irreplaceable) html += `<li>${n.label}（替代度 ${n.value}）</li>`
      html += `</ul>`
    }
    // 可替代单位列表
    if (d.replaceable?.length) {
      html += `<p style="font-weight:600;color:#16a34a;margin-top:8px;">✅ 最可替代单位：</p><ul>`
      for (const n of d.replaceable) html += `<li>${n.label}（替代度 ${n.value}）</li>`
      html += `</ul>`
    }
    // 核心发现列表
    if (d.findings?.length) {
      html += `<p style="font-weight:600;font-size:15px;margin-top:12px;">🔴 核心发现</p>`
      for (const f of d.findings) {
        html += `<div class="finding"><span class="finding-sev severity ${f.level}">${f.levelLabel}</span><span>${f.text}</span></div>`
      }
    }
    // 改进建议列表
    if (d.suggestions?.length) {
      html += `<p style="font-weight:600;font-size:15px;margin-top:12px;">🟢 改进建议</p>`
      d.suggestions.forEach((s, i) => {
        html += `<div class="suggestion"><span class="suggestion-num">${i + 1}</span><span>${s}</span></div>`
      })
    }
    html += `</div>`
  }
  html += `<div class="footer">多源异构文书流转分析平台 — 自动生成报告</div></body></html>`
  return html
}

/**
 * 构建纯文本格式的分析报告
 * @returns {string} 纯文本报告字符串
 */
function buildTextReport() {
  const sections = getAllConclusions()
  let txt = '═══════════════════════════════════════════════════\n'
  txt += '        多源异构文书流转分析结论报告\n'
  txt += '═══════════════════════════════════════════════════\n\n'
  txt += `数据概况：${props.summary?.node_count || 0} 个单位 | ${props.summary?.edge_count || 0} 条文书流转\n`
  txt += `分析时间：${reportTime.value}（基于最近一次拓扑更新）\n\n`

  for (const sec of sections) {
    if (!sec.data) continue
    const d = sec.data
    txt += `───────────────────────────────────────────────────\n`
    txt += `${sec.title}${d.severityLabel ? ' 【' + d.severityLabel + '】' : ''}\n`
    txt += `───────────────────────────────────────────────────\n`
    if (d.text) txt += `${d.text}\n\n`
    if (d.stats?.length) {
      for (const s of d.stats) txt += `  ${s.label}：${s.value}（${s.eval}）\n`
      txt += '\n'
    }
    if (d.insights?.length) {
      for (const ins of d.insights) txt += `  ${ins.icon} ${ins.title}：${ins.detail}\n`
      txt += '\n'
    }
    if (d.irreplaceable?.length) {
      txt += '  最不可替代单位：\n'
      d.irreplaceable.forEach((n, i) => txt += `    ${i + 1}. ${n.label}（替代度 ${n.value}）\n`)
      txt += '\n'
    }
    if (d.findings?.length) {
      txt += '  核心发现：\n'
      d.findings.forEach(f => txt += `    [${f.levelLabel}] ${f.text}\n`)
      txt += '\n'
    }
    if (d.suggestions?.length) {
      txt += '  改进建议：\n'
      d.suggestions.forEach((s, i) => txt += `    ${i + 1}. ${s}\n`)
      txt += '\n'
    }
  }
  txt += '═══════════════════════════════════════════════════\n'
  txt += '多源异构文书流转分析平台 — 自动生成报告\n'
  return txt
}

/**
 * 通用文件下载函数
 * @param {string} content - 文件内容
 * @param {string} filename - 下载文件名
 * @param {string} type - MIME类型
 */
function downloadFile(content, filename, type) {
  const blob = new Blob([content], { type: `${type};charset=utf-8` })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/** 导出HTML报告（带完整样式的网页文件） */
function exportHTML() {
  const html = buildHTMLReport()
  downloadFile(html, `文书流转分析结论报告_${reportTime.value.replace(/[:\s]/g, '_')}.html`, 'text/html')
}

/** 导出纯文本报告 */
function exportText() {
  const txt = buildTextReport()
  downloadFile(txt, `文书流转分析结论报告_${reportTime.value.replace(/[:\s]/g, '_')}.txt`, 'text/plain')
}
</script>

<style scoped>
.conclusion-container { display: flex; flex-direction: column; gap: 16px; max-width: 1100px; margin: 0 auto; }

.conclusion-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
.conclusion-main-title { font-size: 20px; font-weight: 700; color: #15803d; }
.export-btns { display: flex; gap: 8px; }
.btn { padding: 8px 16px; border: none; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; }
.btn-primary { background: #16a34a; color: #fff; }
.btn-primary:hover { background: #15803d; }
.btn-outline { background: transparent; color: #475569; border: 1px solid #22c55e; }
.btn-outline:hover { background: #f0fdf4; color: #15803d; }

.report-meta { font-size: 12px; color: #64748b; display: flex; justify-content: space-between; padding: 8px 16px; background: #f0fdf4; border-radius: 8px; border: 1px solid #bbf7d0; }

.conclusion-section { background: #ffffff; border: 1px solid #22c55e; border-radius: 10px; overflow: hidden; }
.section-header { display: flex; align-items: center; gap: 10px; padding: 12px 20px; background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%); border-bottom: 1px solid #dcfce7; }
.section-num { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; background: #16a34a; color: #fff; border-radius: 50%; font-size: 13px; font-weight: 700; flex-shrink: 0; }
.section-title { font-size: 15px; font-weight: 600; color: #1e293b; flex: 1; }
.severity-badge { padding: 3px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; }
.severity-badge.high { background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }
.severity-badge.mid { background: #fffbeb; color: #d97706; border: 1px solid #fcd34d; }
.severity-badge.low { background: #f0fdf4; color: #16a34a; border: 1px solid #86efac; }
.severity-badge.good { background: #f0fdf4; color: #16a34a; border: 1px solid #86efac; }

.conclusion-body { padding: 16px 20px; }
.conclusion-text { font-size: 14px; color: #334155; line-height: 1.8; margin: 0 0 12px 0; }

.data-table { width: 100%; border-collapse: collapse; margin-top: 8px; }
.table-row { display: flex; border-bottom: 1px solid #f1f5f9; padding: 8px 0; }
.table-row.table-header { background: #f0fdf4; border-radius: 6px; font-weight: 600; color: #15803d; padding: 8px 12px; margin-bottom: 4px; }
.table-row .col { flex: 1; font-size: 13px; padding: 0 8px; }
.table-row .col.highlight { font-weight: 700; color: #16a34a; }
.col.good { color: #16a34a; font-weight: 500; }
.col.warn { color: #d97706; font-weight: 500; }
.col.danger { color: #dc2626; font-weight: 500; }

.key-nodes { margin-top: 12px; }
.key-node-title { font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 8px; }
.key-node-list { display: flex; flex-direction: column; gap: 6px; }
.key-node-item { display: flex; align-items: center; gap: 8px; padding: 6px 12px; background: #f8faf8; border-radius: 6px; }
.key-node-item .rank { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; background: #16a34a; color: #fff; border-radius: 50%; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.key-node-item .node-name { font-size: 13px; font-weight: 600; color: #1e293b; }
.key-node-item .node-value { font-size: 12px; color: #16a34a; font-weight: 500; margin-left: auto; }

.insight-cards { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
.insight-card { display: flex; gap: 12px; padding: 12px 16px; background: #f0fdf4; border-radius: 8px; border-left: 3px solid #22c55e; }
.insight-icon { font-size: 22px; flex-shrink: 0; }
.insight-title { font-size: 13px; font-weight: 600; color: #1e293b; }
.insight-detail { font-size: 12px; color: #64748b; margin-top: 2px; }

.dual-list { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 12px; }
.dual-col { background: #f8faf8; border-radius: 8px; padding: 12px; }
.dual-col-title { font-size: 13px; font-weight: 600; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #e2e8f0; }
.dual-col-title.danger { color: #dc2626; }
.dual-col-title.safe { color: #16a34a; }
.dual-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
.dual-item .rank { display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 50%; font-size: 10px; font-weight: 700; flex-shrink: 0; }
.dual-item .rank.danger { background: #fef2f2; color: #dc2626; }
.dual-item .rank.safe { background: #f0fdf4; color: #16a34a; }
.dual-item .node-name { font-size: 13px; font-weight: 500; color: #1e293b; }
.dual-item .node-value { font-size: 12px; color: #64748b; margin-left: auto; }

.summary-section { border: 2px solid #16a34a; }
.summary-section .section-header { background: linear-gradient(135deg, #dcfce7 0%, #f0fdf4 100%); }

.findings { margin-bottom: 16px; }
.finding-title { font-size: 14px; font-weight: 600; color: #1e293b; margin-bottom: 8px; }
.suggestion-title { color: #15803d; }
.finding-item { display: flex; gap: 10px; align-items: flex-start; padding: 6px 0; }
.finding-severity { padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; white-space: nowrap; flex-shrink: 0; }
.finding-severity.high { background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }
.finding-severity.mid { background: #fffbeb; color: #d97706; border: 1px solid #fcd34d; }
.finding-severity.low { background: #f0fdf4; color: #16a34a; border: 1px solid #86efac; }
.finding-text { font-size: 13px; color: #334155; line-height: 1.6; }

.suggestions { margin-top: 8px; }
.suggestion-item { display: flex; gap: 10px; align-items: flex-start; padding: 6px 0; }
.suggestion-num { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; background: #16a34a; color: #fff; border-radius: 50%; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.suggestion-text { font-size: 13px; color: #334155; line-height: 1.6; }

@media (max-width: 768px) {
  .conclusion-header { flex-direction: column; align-items: flex-start; }
  .dual-list { grid-template-columns: 1fr; }
}
</style>
