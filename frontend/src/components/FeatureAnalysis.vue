<!-- 流转特征指标组件：从多维度分析文书流转网络的特征，包括往来频次、核心地位、聚集度等 -->
<template>
  <div class="features-container">
    <!-- ==================== 第一板块：文书往来频次分析 ==================== -->
    <div class="section" v-if="features">
      <h3 class="section-title">文书往来频次分析</h3>
      <div class="section-desc">
        统计各单位的文书收发总次数（入度+出度之和），反映单位在文书流转中的活跃程度。频次越高，说明该单位参与的文书流转越频繁，是文书流转网络中的核心参与者。
      </div>
      <div class="formula-section">
        <div class="formula-header" @click="toggleFormula('degree')">
          <span>📐 计算公式与计算过程</span>
          <span class="formula-arrow">{{ expandedFormulas.has('degree') ? '▲ 收起' : '▼ 展开' }}</span>
        </div>
        <div class="formula-body" v-if="expandedFormulas.has('degree')">
          <div class="formula-block">
            <div class="formula-name">1. 加权度（往来频次）</div>
            <div class="formula-expr">d_w(v) = Σ w(eᵢ)，eᵢ ∈ adj(v)</div>
            <div class="formula-desc">对节点v的所有相邻边的权重求和。在投影图（无向加权图）上计算，合并了双向文书流转次数。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">2. 入度（接收频次）</div>
            <div class="formula-expr">d_in(v) = Σ w(eᵢ)，eᵢ ∈ in_edges(v)</div>
            <div class="formula-desc">在有向图上统计指向节点v的所有边权重之和，即该单位接收文书的总次数。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">3. 出度（发送频次）</div>
            <div class="formula-expr">d_out(v) = Σ w(eᵢ)，eᵢ ∈ out_edges(v)</div>
            <div class="formula-desc">在有向图上统计从节点v出发的所有边权重之和，即该单位发送文书的总次数。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">4. 分布统计量</div>
            <div class="formula-expr">均值: μ = (1/n) × Σ d(vᵢ)
标准差: σ = √((1/n) × Σ (d(vᵢ) - μ)²)
百分位数: P_k = 第k百分位的度值 (k=25, 50, 75)</div>
            <div class="formula-desc">对所有节点的度值进行统计分析，计算均值、标准差和四分位数。</div>
          </div>
        </div>
      </div>
      <!-- 两列布局：左侧为 Top 排名，右侧为统计分布 -->
      <div class="charts-row">
        <!-- 左侧面板：文书往来最频繁的单位 Top 排名（水平柱状图） -->
        <div class="chart-panel">
          <h4 class="chart-subtitle">文书往来最频繁的单位</h4>
          <div class="chart-concept">直接收发文书最多的单位，即文书流转中最活跃的参与者。</div>
          <div ref="topDegreeChart" class="chart-box"></div>
        </div>
        <!-- 右侧面板：往来频次的统计分布（柱状图，含 Min/P25/均值/P50/P75/Max） -->
        <div class="chart-panel">
          <h4 class="chart-subtitle">往来频次分布统计</h4>
          <div class="chart-concept">所有单位文书往来频次的统计分布（最小值、P25、均值、中位数、P75、最大值），反映频次的集中和分散趋势。</div>
          <div ref="degreeDistChart" class="chart-box"></div>
        </div>
      </div>
    </div>

    <!-- ==================== 第二板块：核心地位分析对比 ==================== -->
    <!-- 横向对比多个单位在四种核心地位指标上的表现（分组柱状图） -->
    <div class="section" v-if="features">
      <h3 class="section-title">核心地位分析对比</h3>
      <div class="section-desc">
        从多个维度衡量各单位在文书流转网络中的核心地位：往来活跃度、文书枢纽度、流转可达性、文书影响力。不同维度揭示单位在流转中的不同角色。
      </div>
      <div class="formula-section">
        <div class="formula-header" @click="toggleFormula('centrality')">
          <span>📐 计算公式与计算过程</span>
          <span class="formula-arrow">{{ expandedFormulas.has('centrality') ? '▲ 收起' : '▼ 展开' }}</span>
        </div>
        <div class="formula-body" v-if="expandedFormulas.has('centrality')">
          <div class="formula-block">
            <div class="formula-name">1. 度中心性（往来活跃度）</div>
            <div class="formula-expr">C_D(v) = deg(v) / (n - 1)</div>
            <div class="formula-desc">节点v的度除以最大可能度数(n-1)，归一化到[0,1]。值越高表示与越多单位有直接文书往来。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">2. 介数中心性（文书枢纽度）</div>
            <div class="formula-expr">C_B(v) = Σ_{s≠v≠t} σ(s,t|v) / σ(s,t)</div>
            <div class="formula-desc">σ(s,t)为节点s到t的最短路径数量，σ(s,t|v)为经过节点v的最短路径数量。使用边权重归一化。衡量节点作为"文书中转站"的重要程度。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">3. 接近中心性（流转可达性）</div>
            <div class="formula-expr">C_C(v) = (n - 1) / Σ_u d(v, u)</div>
            <div class="formula-desc">d(v,u)为节点v到u的最短路径长度。值越高表示到所有其他单位的平均距离越短，文书传递越便捷。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">4. PageRank（文书影响力）</div>
            <div class="formula-expr">PR(v) = (1-d)/n + d × Σ_{u∈in(v)} PR(u) / |out(u)|
其中 d = 0.85（阻尼系数），n = 节点总数</div>
            <div class="formula-desc">基于随机游走模型，被高影响力单位频繁连接的节点自身也具有更高影响力。</div>
          </div>
        </div>
      </div>
      <div class="chart-panel">
        <!-- 较大的图表区域，展示四个核心地位指标的横向对比 -->
        <div ref="centralityChart" class="chart-box-lg"></div>
      </div>
    </div>

    <!-- ==================== 第三板块：核心地位 Top 单位详情 ==================== -->
    <!-- 四列布局，分别展示每种核心地位指标排名靠前的单位 -->
    <div class="section" v-if="features">
      <h3 class="section-title">核心地位 Top 单位详情</h3>
      <div class="section-desc">
        分别展示各核心地位指标排名靠前的单位，便于从不同视角识别文书流转中的关键角色。
      </div>
      <div class="formula-section">
        <div class="formula-header" @click="toggleFormula('centTop')">
          <span>📐 计算公式与计算过程</span>
          <span class="formula-arrow">{{ expandedFormulas.has('centTop') ? '▲ 收起' : '▼ 展开' }}</span>
        </div>
        <div class="formula-body" v-if="expandedFormulas.has('centTop')">
          <div class="formula-block">
            <div class="formula-name">计算步骤</div>
            <div class="formula-expr">1. 将多重有向图投影为无向加权图
2. 分别计算四种中心性指标:
   - 往来活跃度: C_D(v) = deg(v) / (n-1)
   - 文书枢纽度: C_B(v) = Σ σ(s,t|v) / σ(s,t)
   - 流转可达性: C_C(v) = (n-1) / Σ d(v,u)
   - 文书影响力: PR(v) = (1-d)/n + d×Σ PR(u)/|out(u)|
3. 各指标按值降序排列，取排名前N的单位</div>
            <div class="formula-desc">投影过程：将多重有向图中相同节点对之间的所有边合并为一条无向边，权重取所有平行边的权重之和。</div>
          </div>
        </div>
      </div>
      <!-- 四列网格，每种核心地位指标一列 -->
      <div class="charts-row charts-row-4">
        <div class="chart-panel" v-for="ck in centralityKeys" :key="ck.key">
          <!-- 指标名称 -->
          <h4 class="chart-subtitle">{{ ck.label }}</h4>
          <!-- 指标概念解释 -->
          <div class="chart-concept">{{ ck.desc }}</div>
          <!-- 动态绑定 ref，通过 setChartRef 函数收集各图表的 DOM 引用 -->
          <div :ref="el => setChartRef(ck.key, el)" class="chart-box"></div>
        </div>
      </div>
    </div>

    <!-- ==================== 第四板块：文书流转聚集度分析 ==================== -->
    <div class="section" v-if="features">
      <h3 class="section-title">文书流转聚集度分析</h3>
      <div class="section-desc">
        衡量与某单位有文书往来的各单位之间是否也互相收发文书。聚集度高表示形成了紧密的文书互通小组，聚集度低表示该单位连接了不同的文书流转群体。
      </div>
      <div class="formula-section">
        <div class="formula-header" @click="toggleFormula('clustering')">
          <span>📐 计算公式与计算过程</span>
          <span class="formula-arrow">{{ expandedFormulas.has('clustering') ? '▲ 收起' : '▼ 展开' }}</span>
        </div>
        <div class="formula-body" v-if="expandedFormulas.has('clustering')">
          <div class="formula-block">
            <div class="formula-name">1. 局部聚集系数</div>
            <div class="formula-expr">C(v) = 2×T(v) / (k_v × (k_v - 1))</div>
            <div class="formula-desc">T(v)为节点v的邻居之间实际存在的边数（三角形数），k_v为节点v的度。分母是邻居之间最大可能的边数。衡量"与该单位有文书往来的单位之间是否也互相往来"。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">2. 全局平均聚集系数</div>
            <div class="formula-expr">C_avg = (1/n) × Σ C(v)</div>
            <div class="formula-desc">所有节点局部聚集系数的算术平均值。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">3. 三角形计数</div>
            <div class="formula-expr">T_total = Σ T(v) / 3</div>
            <div class="formula-desc">每个三角形被3个节点各计数一次，因此总三角形数需除以3。三角形是最基本的闭合结构，反映局部凝聚程度。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">4. 密度（流转密集度）</div>
            <div class="formula-expr">D = 2m / (n × (n - 1))</div>
            <div class="formula-desc">m为实际边数，n为节点数。反映网络中实际连接占所有可能连接的比例。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">5. 同配性（往来同质性）</div>
            <div class="formula-expr">r = Σ(eᵢⱼ×aᵢ×aⱼ) - Σ(eᵢⱼ×bᵢ×bⱼ) / ...（度-度Pearson相关系数）</div>
            <div class="formula-desc">r&gt;0表示频繁单位倾向互相往来（同配），r&lt;0表示频繁单位倾向与不频繁单位往来（异配），r≈0无偏好。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">6. 幂律指数（流转集中度指数）</div>
            <div class="formula-expr">log P(k) = -γ × log(k) + c
γ = -slope（对数坐标线性回归斜率的负值）</div>
            <div class="formula-desc">通过对数坐标系中线性回归估计。若度分布P(k)∝k^(-γ)，γ接近1表示无标度特征，少数核心单位连接大量边缘单位。</div>
          </div>
        </div>
      </div>
      <div class="charts-row">
        <!-- 左侧面板：聚集度最高的单位 Top 排名（水平柱状图） -->
        <div class="chart-panel">
          <h4 class="chart-subtitle">流转聚集度最高的单位</h4>
          <div class="chart-concept">这些单位与其文书往来对象之间形成了紧密的互文关系，属于高度互通的文书流转小组。</div>
          <div ref="clusteringChart" class="chart-box"></div>
        </div>
        <!-- 右侧面板：流转网络级全局指标（列表形式展示） -->
        <div class="chart-panel">
          <h4 class="chart-subtitle">流转网络级指标</h4>
          <div class="chart-concept">整个文书流转网络的全局统计指标，反映网络整体的流转特征。</div>
          <div class="metric-list">
            <!-- 遍历 networkMetrics 计算属性，逐项展示指标名、说明和数值 -->
            <div class="metric-item" v-for="m in networkMetrics" :key="m.label">
              <div class="metric-left">
                <span class="metric-label">{{ m.label }}</span>
                <span class="metric-desc">{{ m.desc }}</span>
              </div>
              <span class="metric-value">{{ m.value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

// ==================== Props 定义 ====================
// features: 流转特征分析数据，包含度分析、核心地位分析、聚集度分析等
const props = defineProps({ features: { type: Object, default: null } })

// ==================== 图表 DOM 引用 ====================
// 固定引用的图表容器（模板中通过 ref 直接绑定）
const topDegreeChart = ref(null)    // 往来频次 Top 单位图
const degreeDistChart = ref(null)   // 往来频次分布统计图
const centralityChart = ref(null)   // 核心地位综合对比图
const clusteringChart = ref(null)   // 聚集度 Top 单位图

// centralityCharts: 动态收集的四类核心地位指标的图表 DOM 引用（key → DOM 元素）
const centralityCharts = {}
// allCharts: 存储所有 ECharts 实例及其 ResizeObserver，统一管理生命周期
const allCharts = []
const expandedFormulas = ref(new Set())
function toggleFormula(key) {
  const s = new Set(expandedFormulas.value)
  if (s.has(key)) s.delete(key)
  else s.add(key)
  expandedFormulas.value = s
}

// setChartRef: 用于 v-for 中动态 :ref 的回调函数，收集每种核心地位指标的 DOM 引用
function setChartRef(key, el) {
  if (el) centralityCharts[key] = el
}

// ==================== 核心地位指标配置 ====================
// centralityKeys: 四种核心地位指标的元数据，包含 key（后端字段名）、label（中文标签）、desc（概念说明）
const centralityKeys = [
  { key: 'degree_centrality', label: '往来活跃度', desc: '某单位直接收发文书的单位数量占比，值越高表示该单位与越多单位有直接文书往来。' },
  { key: 'betweenness_centrality', label: '文书枢纽度', desc: '某单位作为其他单位之间文书传递中间环节的概率，值越高表示该单位是重要的文书中转枢纽。' },
  { key: 'closeness_centrality', label: '流转可达性', desc: '某单位通过最少的转发层级即可将文书送达所有其他单位的能力，值越高表示文书传递越便捷。' },
  { key: 'pagerank', label: '文书影响力', desc: '基于文书流转链路评估的单位影响力，被高影响力单位频繁发送文书的单位自身影响力也更高。' },
]

// ==================== 网络级指标 Computed ====================
// networkMetrics: 从 features 数据中提取并格式化流转网络的全局统计指标列表
const networkMetrics = computed(() => {
  const m = props.features?.network_level_metrics
  const c = props.features?.clustering_analysis
  if (!m) return []
  return [
    { label: '平均转发层级', value: m.average_shortest_path_length?.toFixed(4) || '--', desc: '文书送达任意单位平均需中转次数' },
    { label: '往来同质性', value: m.assortativity?.toFixed(4) || '--', desc: '频繁单位是否倾向互相收发文书' },
    { label: '流转集中度指数', value: m.power_law_exponent?.toFixed(4) || '--', desc: '文书流转是否集中于少数核心单位' },
    { label: '平均流转聚集度', value: c?.average_clustering_coefficient?.toFixed(4) || '--', desc: '各单位间形成互文小组的平均程度' },
    { label: '三方互文总数', value: c?.triangles_per_node?.total_triangles || '--', desc: '三个单位间两两互相收发文书的组合数' },
    { label: '流转密集度', value: m.density?.toFixed(4) || '--', desc: '实际流转占所有可能组合的比例' },
  ]
})

// ==================== 图表初始化辅助函数 ====================
// initChart: 在指定 DOM 容器上创建 ECharts 实例，设置配置项，并监听容器尺寸变化
function initChart(refVal, option) {
  if (!refVal?.value) return
  const c = echarts.init(refVal.value)
  c.setOption(option)
  // 监听容器尺寸变化，自动调整图表大小
  const ro = new ResizeObserver(() => c.resize())
  ro.observe(refVal.value)
  // 保存实例和 observer 引用，便于后续销毁
  allCharts.push({ chart: c, observer: ro })
  return c
}

// ==================== 通用图表配置生成函数 ====================
// barH: 生成水平柱状图的通用配置（数据倒序，使排名第一的显示在最上方）
function barH(data, nameKey, valueKey, color = '#16a34a') {
  data = [...data].reverse()
  return {
    backgroundColor: 'transparent',
    // 提示框：坐标轴触发，配合阴影指示器
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    // 图表边距：左侧 90px 显示单位标签
    grid: { left: 90, right: 40, top: 5, bottom: 15 },
    // X 轴：数值轴，用于显示频次/指标值
    xAxis: { type: 'value', axisLabel: { color: '#64748b', fontSize: 10 }, splitLine: { lineStyle: { color: '#e2e8f0' } } },
    // Y 轴：类目轴，显示单位名称，超长截断
    yAxis: { type: 'category', data: data.map(d => d[nameKey]), axisLabel: { color: '#475569', fontSize: 10, width: 80, overflow: 'truncate' } },
    series: [{
      type: 'bar', data: data.map(d => d[valueKey]),
      // 柱体样式：右侧圆角，最大宽度 18px
      itemStyle: { color, borderRadius: [0, 3, 3, 0] }, barMaxWidth: 18,
    }],
  }
}

// ==================== 批量渲染函数 ====================
// renderAll: 销毁所有旧图表后，根据最新 features 数据重新渲染全部图表
function renderAll() {
  // 销毁所有旧图表并断开 ResizeObserver
  allCharts.forEach(({ chart, observer }) => { observer?.disconnect(); chart?.dispose() })
  allCharts.length = 0

  // 若无 features 数据，不进行渲染
  if (!props.features) return

  nextTick(() => {
    // ---- 第一板块：往来频次分析图表 ----
    const da = props.features.degree_analysis
    // 渲染往来最频繁单位 Top 10 水平柱状图
    if (da?.top_nodes_by_degree) {
      initChart(topDegreeChart, barH(da.top_nodes_by_degree.slice(0, 10), 'label', 'degree', '#16a34a'))
    }
    // 渲染往来频次分布统计柱状图（Min/P25/均值/P50/P75/Max）
    if (da?.degree_distribution) {
      const d = da.degree_distribution
      initChart(degreeDistChart, {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis' },
        grid: { left: 45, right: 20, top: 10, bottom: 25 },
        // X 轴：六个统计量标签
        xAxis: { type: 'category', data: ['Min', 'P25', '均值', 'P50', 'P75', 'Max'], axisLabel: { color: '#64748b', fontSize: 10 } },
        // Y 轴：频次数值
        yAxis: { type: 'value', axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#e2e8f0' } } },
        series: [{
          type: 'bar',
          // 六个统计量对应的频次值
          data: [d.min, d.p25, d.mean, d.p50, d.p75, d.max],
          itemStyle: { color: '#22c55e', borderRadius: 4 },
          barMaxWidth: 28,
        }],
      })
    }

    // ---- 第二、三板块：核心地位分析图表 ----
    const ca = props.features.centrality_analysis
    if (ca) {
      // 收集所有在核心地位 Top 排名中出现过的单位名称（去重），最多取前 8 个用于综合对比图
      const allNodes = new Set()
      Object.values(ca).forEach(c => c?.top_nodes?.forEach(n => allNodes.add(n.label)))
      const nodeLabels = [...allNodes].slice(0, 8)

      // 四种核心地位指标的系列配置（名称、后端字段 key、颜色）
      const series = [
        { name: '往来活跃度', key: 'degree_centrality', color: '#16a34a' },
        { name: '文书枢纽度', key: 'betweenness_centrality', color: '#f59e0b' },
        { name: '流转可达性', key: 'closeness_centrality', color: '#3b82f6' },
        { name: '文书影响力', key: 'pagerank', color: '#ec4899' },
      ]

      // 渲染核心地位综合对比图（分组水平柱状图）
      initChart(centralityChart, {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis' },
        // 图例：显示四种核心地位指标名称
        legend: { data: series.map(s => s.name), bottom: 0, textStyle: { color: '#475569', fontSize: 11 } },
        grid: { left: 90, right: 30, top: 10, bottom: 35 },
        // X 轴：数值轴
        xAxis: { type: 'value', axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#e2e8f0' } } },
        // Y 轴：类目轴，显示单位名称
        yAxis: { type: 'category', data: nodeLabels, axisLabel: { color: '#475569', fontSize: 10 } },
        // 四个系列，分别对应四种核心地位指标
        series: series.map(s => ({
          name: s.name, type: 'bar',
          // 根据单位名称查找对应的核心地位指标值
          data: nodeLabels.map(label => {
            const node = ca[s.key]?.top_nodes?.find(n => n.label === label)
            return node?.value || 0
          }),
          itemStyle: { color: s.color, borderRadius: 2 },
          barMaxWidth: 14,
        })),
      })

      // 渲染四类核心地位指标各自的 Top 单位详情图（水平柱状图）
      centralityKeys.forEach(ck => {
        const nodes = ca[ck.key]?.top_nodes?.slice(0, 8)
        if (nodes && centralityCharts[ck.key]) {
          // 使用 { value: el } 包装以兼容 initChart 的 refVal.value 取值方式
          initChart({ value: centralityCharts[ck.key] }, barH(nodes, 'label', 'value', '#16a34a'))
        }
      })
    }

    // ---- 第四板块：聚集度分析图表 ----
    const cl = props.features.clustering_analysis
    // 渲染聚集度最高的单位 Top 10 水平柱状图
    if (cl?.top_nodes_by_clustering) {
      initChart(clusteringChart, barH(cl.top_nodes_by_clustering.slice(0, 10), 'label', 'clustering', '#22c55e'))
    }
  })
}

// ==================== 生命周期钩子 ====================
// 组件挂载时立即执行首次渲染
onMounted(() => renderAll())
// 监听 features 变化，数据更新时重新渲染所有图表
watch(() => props.features, renderAll)
// 组件销毁时释放所有 ECharts 实例和 ResizeObserver
onUnmounted(() => {
  allCharts.forEach(({ chart, observer }) => { observer?.disconnect(); chart?.dispose() })
})
</script>

<style scoped>
.features-container { display: flex; flex-direction: column; gap: 24px; }
.section { }
.section-title { font-size: 16px; font-weight: 600; color: #1e293b; margin-bottom: 6px; padding-bottom: 8px; border-bottom: 1px solid #22c55e; }
.section-desc { font-size: 12px; color: #64748b; line-height: 1.6; margin-bottom: 12px; padding: 8px 12px; background: #f0fdf4; border-radius: 8px; }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.charts-row-4 { grid-template-columns: repeat(4, 1fr); }
.chart-panel { background: #ffffff; border: 1px solid #22c55e; border-radius: 10px; padding: 14px; }
.chart-subtitle { font-size: 12px; color: #475569; margin-bottom: 4px; font-weight: 500; }
.chart-concept { font-size: 11px; color: #94a3b8; margin-bottom: 8px; line-height: 1.4; }
.chart-box { width: 100%; height: 240px; }
.chart-box-lg { width: 100%; height: 350px; }
.metric-list { display: grid; gap: 10px; }
.metric-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: #f0fdf4; border-radius: 8px; }
.metric-left { display: flex; flex-direction: column; gap: 2px; }
.metric-label { font-size: 13px; color: #475569; font-weight: 500; }
.metric-desc { font-size: 10px; color: #94a3b8; }
.metric-value { font-size: 14px; font-weight: 600; color: #16a34a; }
.formula-section { margin-bottom: 10px; border: 1px dashed #86efac; border-radius: 8px; overflow: hidden; }
.formula-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 14px; background: #f0fdf4; cursor: pointer; font-size: 12px; color: #15803d; font-weight: 500; user-select: none; }
.formula-header:hover { background: #dcfce7; }
.formula-arrow { font-size: 11px; color: #16a34a; }
.formula-body { padding: 12px 14px; background: #fff; border-top: 1px dashed #86efac; }
.formula-block { margin-bottom: 10px; }
.formula-block:last-child { margin-bottom: 0; }
.formula-name { font-size: 12px; font-weight: 600; color: #15803d; margin-bottom: 3px; }
.formula-expr { font-family: 'Courier New', Consolas, monospace; font-size: 12px; color: #1e293b; background: #f8faf8; padding: 6px 10px; border-radius: 4px; margin: 4px 0; line-height: 1.6; white-space: pre-wrap; }
.formula-desc { font-size: 11px; color: #64748b; line-height: 1.5; }
</style>
