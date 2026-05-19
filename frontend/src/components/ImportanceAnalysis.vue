<!-- 关键单位分析组件：展示文书流转网络中各单位的核心枢纽地位、可替代程度、结构洞瓶颈和关键单位撤除影响 -->
<template>
  <!-- 整体容器 -->
  <div class="importance-container">
    <!-- 第一部分：综合枢纽评分（多维度加权评估各单位的核心地位） -->
    <div class="section" v-if="importance?.comprehensive_importance">
      <h3 class="section-title">综合枢纽评分</h3>
      <div class="section-desc">
        综合往来活跃度、文书枢纽度、流转可达性、文书影响力等多个维度，评估各单位在文书流转中的核心枢纽地位。评分越高，说明该单位在文书流转体系中越不可或缺。
      </div>
      <div class="formula-section">
        <div class="formula-header" @click="toggleFormula('comprehensive')">
          <span>📐 计算公式与计算过程</span>
          <span class="formula-arrow">{{ expandedFormulas.has('comprehensive') ? '▲ 收起' : '▼ 展开' }}</span>
        </div>
        <div class="formula-body" v-if="expandedFormulas.has('comprehensive')">
          <div class="formula-block">
            <div class="formula-name">综合枢纽评分公式</div>
            <div class="formula-expr">S(v) = 0.20×C_D(v) + 0.25×C_B(v) + 0.15×C_C(v) + 0.20×C_E(v) + 0.20×PR(v)</div>
            <div class="formula-desc">五种中心性指标的加权融合，各指标均归一化到[0,1]区间后按权重求和。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">各维度权重说明</div>
            <div class="formula-expr">• 度中心性 C_D(v) — 权重 0.20: 直接连接的广泛性
  C_D(v) = deg(v) / (n-1)
• 介数中心性 C_B(v) — 权重 0.25（最高）: 作为文书中转枢纽的重要性
  C_B(v) = Σ_{s≠v≠t} σ(s,t|v) / σ(s,t)
• 接近中心性 C_C(v) — 权重 0.15: 文书传递的便捷程度
  C_C(v) = (n-1) / Σ_u d(v,u)
• 特征向量中心性 C_E(v) — 权重 0.20: 与核心单位关联的紧密程度
  求解 A·x = λ·x 的主特征向量
• PageRank PR(v) — 权重 0.20: 全局流转链路影响力
  PR(v) = (1-d)/n + d × Σ PR(u)/|out(u)|</div>
            <div class="formula-desc">介数中心性权重最高(0.25)，强调节点作为信息桥梁的作用。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">计算步骤</div>
            <div class="formula-expr">1. 将多重有向图投影为无向加权图
2. 分别计算五种中心性指标（均归一化到[0,1]）
3. 按权重加权求和得到综合评分
4. 按综合评分降序排列</div>
          </div>
        </div>
      </div>
      <!-- 双列图表布局 -->
      <div class="charts-row">
        <!-- 左侧：综合枢纽评分条形图 -->
        <div class="chart-panel">
          <div ref="compImpChart" class="chart-box-lg"></div>
        </div>
        <!-- 右侧：雷达图说明 + Top3单位雷达图对比 -->
        <div class="chart-panel">
          <div class="chart-concept-panel">
            <div class="concept-title">📊 雷达图说明</div>
            <div class="concept-text">展示排名前3的单位在六个维度上的表现对比。各维度含义：<br/>
              <b>综合得分</b>：多维度加权总分<br/>
              <b>往来活跃度</b>：直接收发文书覆盖面<br/>
              <b>文书枢纽度</b>：作为文书中转枢纽的重要程度<br/>
              <b>流转可达性</b>：文书传递到各单位的便捷程度<br/>
              <b>特征向量</b>：与核心单位关联的紧密程度<br/>
              <b>文书影响力</b>：在流转链路中的全局影响力
            </div>
          </div>
          <div ref="compImpRadar" class="chart-box-lg"></div>
        </div>
      </div>
    </div>

    <!-- 第二部分：单位可替代程度分析（评估单位缺失时流转网络的受影响程度） -->
    <div class="section" v-if="importance?.substitutability">
      <h3 class="section-title">单位可替代程度</h3>
      <div class="section-desc">
        若某单位暂时无法处理文书（如人员调动、设备故障等），其他单位能否替代其流转功能。可替代性高表示该单位缺失时流转网络影响较小；不可替代的单位一旦缺失，将导致文书流转出现明显中断。
      </div>
      <div class="formula-section">
        <div class="formula-header" @click="toggleFormula('subst')">
          <span>📐 计算公式与计算过程</span>
          <span class="formula-arrow">{{ expandedFormulas.has('subst') ? '▲ 收起' : '▼ 展开' }}</span>
        </div>
        <div class="formula-body" v-if="expandedFormulas.has('subst')">
          <div class="formula-block">
            <div class="formula-name">可替代性综合公式</div>
            <div class="formula-expr">Sub(v) = 0.35×Similarity + 0.25×DegreeRatio + 0.15×ConnPenalty + 0.25×EffRetention</div>
            <div class="formula-desc">四个评估维度的加权融合，值越高表示越容易被替代。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">维度1: 邻居相似度（权重0.35）</div>
            <div class="formula-expr">sim(v) = avg( 1 - |BC(u) - BC(v)| / max(BC(u), BC(v)) )
其中 u ∈ neighbors(v)，BC为介数中心性</div>
            <div class="formula-desc">基于介数中心性计算节点与每个邻居的相似度。邻居的枢纽功能与该节点越接近，说明邻居越能承担类似的中转功能。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">维度2: 度比率（权重0.25）</div>
            <div class="formula-expr">ratio(v) = min(deg(v), avg_deg_nbr) / max(deg(v), avg_deg_nbr)</div>
            <div class="formula-desc">节点度与邻居平均度的接近程度，越接近1越容易替代。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">维度3: 连通性惩罚（权重0.15）</div>
            <div class="formula-expr">penalty = 0.5（若移除后网络分裂为多个连通分量）
penalty = 1.0（若移除后网络仍连通）</div>
            <div class="formula-desc">若节点是割点（移除导致网络不连通），降低可替代性。</div>
          </div>
          <div class="formula-block">
            <div class="formula-name">维度4: 效率保持率（权重0.25）</div>
            <div class="formula-expr">retention = E(G\{v}) / E(G)
E(G) = (1/(n(n-1))) × Σ_{i≠j} 1/d(i,j)</div>
            <div class="formula-desc">移除节点后全局效率的保持比例。全局效率是所有节点对之间效率倒数的平均值。</div>
          </div>
        </div>
      </div>
      <div class="charts-row">
        <!-- 左侧：最易被替代的单位（替代度高，缺失影响小） -->
        <div class="chart-panel">
          <h4 class="chart-subtitle">最易被替代（文书可转交其他单位处理）</h4>
          <div class="chart-concept">这些单位的文书流转功能可由相邻单位替代，其缺失对整体流转网络影响较小。</div>
          <div ref="substHighChart" class="chart-box"></div>
        </div>
        <!-- 右侧：最难被替代的单位（替代度低，缺失影响大） -->
        <div class="chart-panel">
          <h4 class="chart-subtitle">最难被替代（文书流转不可替代枢纽）</h4>
          <div class="chart-concept">这些单位一旦缺失，文书流转将出现明显中断，没有其他单位能替代其流转功能。</div>
          <div ref="substLowChart" class="chart-box"></div>
        </div>
      </div>
    </div>

    <!-- 第三部分：结构洞瓶颈分析 + 关键单位撤除影响评估（两者并排展示） -->
    <div class="charts-row" v-if="importance?.structural_holes || importance?.key_player_analysis">
      <!-- 结构洞分析：识别处于不同群体之间"桥梁"位置的单位 -->
      <div class="chart-panel" v-if="importance?.structural_holes">
        <h3 class="section-title">文书流转瓶颈分析</h3>
        <div class="section-desc">
          识别处于不同文书流转群体之间"桥梁"位置的单位。这些单位一旦缺失，将导致原本互通的文书流转群体之间出现断层，信息无法跨群体传递。约束值越低，表示该单位的桥梁作用越明显。
        </div>
        <div class="formula-section">
          <div class="formula-header" @click="toggleFormula('structhole')">
            <span>📐 计算公式与计算过程</span>
            <span class="formula-arrow">{{ expandedFormulas.has('structhole') ? '▲ 收起' : '▼ 展开' }}</span>
          </div>
          <div class="formula-body" v-if="expandedFormulas.has('structhole')">
            <div class="formula-block">
              <div class="formula-name">约束度（Constraint）</div>
              <div class="formula-expr">C(v) = Σ_j [ p(v,j) + Σ_q p(v,q)×p(q,j) ]²
其中 p(v,j) = 1/deg(v)，表示节点v分配给邻居j的关系比例</div>
              <div class="formula-desc">约束度越低表示节点的社交网络越多样化，占据越多的结构洞。按升序排列，约束度最低的排在最前。</div>
            </div>
            <div class="formula-block">
              <div class="formula-name">有效规模（Effective Size）</div>
              <div class="formula-expr">ES(v) = Σ_j [ 1 - Σ_q p(v,q)×m(q,j) ]
其中 m(q,j) 为节点q与j之间的边际连接强度</div>
              <div class="formula-desc">有效规模越大表示节点的非冗余联系越多，结构洞优势越大。按降序排列。</div>
            </div>
          </div>
        </div>
        <div ref="structHoleChart" class="chart-box"></div>
      </div>
      <!-- 关键单位撤除影响评估：模拟移除某单位后对整个网络的影响 -->
      <div class="chart-panel" v-if="importance?.key_player_analysis">
        <h3 class="section-title">关键单位（撤除影响评估）</h3>
        <div class="section-desc">
          模拟移除某单位后对整个文书流转网络的影响程度。影响越大表示该单位越关键，其缺失将导致文书流转效率大幅下降或部分单位完全无法收发文书。
        </div>
        <div class="formula-section">
          <div class="formula-header" @click="toggleFormula('keyplayer')">
            <span>📐 计算公式与计算过程</span>
            <span class="formula-arrow">{{ expandedFormulas.has('keyplayer') ? '▲ 收起' : '▼ 展开' }}</span>
          </div>
          <div class="formula-body" v-if="expandedFormulas.has('keyplayer')">
            <div class="formula-block">
              <div class="formula-name">关键单位影响评分公式</div>
              <div class="formula-expr">Impact(v) = 0.30×Fragmentation + 0.40×EffLoss + 0.20×IsolatedRatio + 0.10×BC(v)</div>
              <div class="formula-desc">四个维度的加权融合，模拟移除节点后对网络的破坏程度。</div>
            </div>
            <div class="formula-block">
              <div class="formula-name">维度1: 碎片化程度（权重0.30）</div>
              <div class="formula-expr">frag = (components_after - components_before) / n</div>
              <div class="formula-desc">移除节点后增加的连通分量数量，归一化为节点总数的比率。</div>
            </div>
            <div class="formula-block">
              <div class="formula-name">维度2: 效率损失（权重0.40）</div>
              <div class="formula-expr">eff_loss = max(0, E(G) - E(G\{v})) / E(G)</div>
              <div class="formula-desc">移除节点后全局效率的相对下降量。效率损失权重最高(0.40)。</div>
            </div>
            <div class="formula-block">
              <div class="formula-name">维度3: 孤立节点比率（权重0.20）</div>
              <div class="formula-expr">isolated = isolated_count / max(deg(v), 1)</div>
              <div class="formula-desc">移除节点后变为孤立节点（度变为0）的邻居数量占原度数的比例。</div>
            </div>
            <div class="formula-block">
              <div class="formula-name">维度4: 原始介数（权重0.10）</div>
              <div class="formula-expr">BC(v) = Σ_{s≠v≠t} σ(s,t|v) / σ(s,t)</div>
              <div class="formula-desc">节点自身的介数中心性值，反映其天然的中转枢纽属性。</div>
            </div>
          </div>
        </div>
        <div ref="keyPlayerChart" class="chart-box"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

// 接收父组件传入的关键单位分析数据
const props = defineProps({ importance: { type: Object, default: null } })

// 各图表的DOM引用
const compImpChart = ref(null)     // 综合枢纽评分条形图
const compImpRadar = ref(null)     // Top3单位雷达图
const substHighChart = ref(null)   // 最易被替代单位图
const substLowChart = ref(null)    // 最难被替代单位图
const structHoleChart = ref(null)  // 结构洞瓶颈分析图
const keyPlayerChart = ref(null)   // 关键单位撤除影响图

// 所有已初始化的图表实例及对应的ResizeObserver，用于统一管理和销毁
const allCharts = []

const expandedFormulas = ref(new Set())
function toggleFormula(key) {
  const s = new Set(expandedFormulas.value)
  if (s.has(key)) s.delete(key)
  else s.add(key)
  expandedFormulas.value = s
}

/**
 * 初始化ECharts图表实例
 * @param {Object} refVal - 模板ref引用，指向图表容器DOM元素
 * @param {Object} option - ECharts配置项
 */
function initChart(refVal, option) {
  if (!refVal?.value) return
  const c = echarts.init(refVal.value)
  c.setOption(option)
  // 监听容器尺寸变化，自动调整图表大小
  const ro = new ResizeObserver(() => c.resize())
  ro.observe(refVal.value)
  allCharts.push({ chart: c, observer: ro })
}

/**
 * 生成通用水平条形图的ECharts配置项
 * @param {Array} data - 数据数组
 * @param {string} nameKey - 名称字段名
 * @param {string} valueKey - 数值字段名
 * @param {string} color - 柱条颜色（十六进制）
 * @returns {Object} ECharts配置对象
 */
function barH(data, nameKey, valueKey, color = '#16a34a') {
  // 反转数组使最大值显示在顶部
  data = [...data].reverse()
  return {
    backgroundColor: 'transparent',                                 // 透明背景
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },  // 鼠标悬停提示：坐标轴触发，阴影指示器
    grid: { left: 90, right: 40, top: 5, bottom: 15 },              // 图表边距（左侧留出单位名称空间）
    xAxis: {
      type: 'value',                                                // 数值轴
      axisLabel: { color: '#64748b', fontSize: 10 },                // 轴标签样式
      splitLine: { lineStyle: { color: '#e2e8f0' } },               // 分隔线颜色
    },
    yAxis: {
      type: 'category',                                             // 类目轴（显示单位名称）
      data: data.map(d => d[nameKey]),                              // Y轴类目数据
      axisLabel: { color: '#475569', fontSize: 10, width: 80, overflow: 'truncate' }, // 标签超长截断
    },
    series: [{
      type: 'bar',                                                  // 条形图
      data: data.map(d => d[valueKey]),                             // 数值数据
      itemStyle: { color, borderRadius: [0, 3, 3, 0] },            // 柱条颜色和右侧圆角
      barMaxWidth: 18,                                              // 最大柱宽
    }],
  }
}

/**
 * 渲染所有图表：先销毁旧实例，再根据props数据重新初始化
 */
function renderAll() {
  // 销毁所有旧图表实例并断开ResizeObserver监听，防止内存泄漏
  allCharts.forEach(({ chart, observer }) => { observer?.disconnect(); chart?.dispose() })
  allCharts.length = 0
  // 数据为空时不渲染
  if (!props.importance) return

  nextTick(() => {
    const ci = props.importance.comprehensive_importance
    if (ci?.top_important_nodes) {
      // 取排名前8的单位用于条形图展示
      const nodes = ci.top_important_nodes.slice(0, 8)
      const labels = nodes.map(n => n.label)

      // 综合枢纽评分多维条形图：展示综合得分、活跃度、枢纽度、影响力四个指标
      initChart(compImpChart, {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis' },                                // 坐标轴触发提示
        legend: {
          data: ['综合得分', '往来活跃度', '文书枢纽度', '文书影响力'],
          bottom: 0,                                                  // 图例位于底部
          textStyle: { color: '#475569', fontSize: 10 },
        },
        grid: { left: 90, right: 30, top: 10, bottom: 35 },
        xAxis: {
          type: 'value',
          axisLabel: { color: '#64748b' },
          splitLine: { lineStyle: { color: '#e2e8f0' } },
        },
        yAxis: {
          type: 'category',
          data: labels,                                               // Y轴显示单位名称
          axisLabel: { color: '#475569', fontSize: 10 },
        },
        series: [
          { name: '综合得分', type: 'bar', data: nodes.map(n => n.comprehensive_score), itemStyle: { color: '#16a34a', borderRadius: 2 }, barMaxWidth: 12 },
          { name: '往来活跃度', type: 'bar', data: nodes.map(n => n.degree_centrality), itemStyle: { color: '#3b82f6' }, barMaxWidth: 12 },
          { name: '文书枢纽度', type: 'bar', data: nodes.map(n => n.betweenness_centrality), itemStyle: { color: '#f59e0b' }, barMaxWidth: 12 },
          { name: '文书影响力', type: 'bar', data: nodes.map(n => n.pagerank), itemStyle: { color: '#ec4899' }, barMaxWidth: 12 },
        ],
      })

      // 取排名前3的单位用于雷达图多维度对比
      const top3 = nodes.slice(0, 3)
      // 雷达图：对比Top3单位在六个维度上的表现
      initChart(compImpRadar, {
        backgroundColor: 'transparent',
        tooltip: {},
        legend: { data: top3.map(n => n.label), bottom: 0, textStyle: { color: '#475569', fontSize: 10 } },
        radar: {
          center: ['50%', '45%'],                                     // 雷达图中心位置
          radius: '65%',                                              // 雷达图半径
          indicator: [                                                // 六个维度指标，最大值均为1（归一化后的值）
            { name: '综合得分', max: 1 },
            { name: '往来活跃度', max: 1 },
            { name: '文书枢纽度', max: 1 },
            { name: '流转可达性', max: 1 },
            { name: '特征向量', max: 1 },
            { name: '文书影响力', max: 1 },
          ],
          axisName: { color: '#475569', fontSize: 10 },
        },
        series: [{
          type: 'radar',
          // 每个Top3单位对应一条雷达数据线
          data: top3.map((n, i) => ({
            name: n.label,
            value: [n.comprehensive_score, n.degree_centrality, n.betweenness_centrality,
                    n.closeness_centrality, n.eigenvector_centrality, n.pagerank],
          })),
        }],
        color: ['#16a34a', '#f59e0b', '#3b82f6'],                    // 三条线的颜色
      })
    }

    // 可替代程度分析
    const sub = props.importance.substitutability
    // 渲染最易被替代单位（蓝色柱条，取前8名）
    if (sub?.top_substitutable_nodes) {
      initChart(substHighChart, barH(sub.top_substitutable_nodes.slice(0, 8), 'label', 'substitutability_score', '#3b82f6'))
    }
    // 渲染最难被替代单位（红色柱条，取前8名）
    if (sub?.top_irreplaceable_nodes) {
      initChart(substLowChart, barH(sub.top_irreplaceable_nodes.slice(0, 8), 'label', 'substitutability_score', '#ef4444'))
    }

    // 结构洞瓶颈分析：约束值越低，桥梁作用越明显
    const sh = props.importance.structural_holes
    if (sh?.top_structural_hole_nodes) {
      initChart(structHoleChart, barH(sh.top_structural_hole_nodes.slice(0, 8), 'label', 'constraint', '#22c55e'))
    }

    // 关键单位撤除影响评估：影响得分越高，移除后破坏越大
    const kp = props.importance.key_player_analysis
    if (kp?.top_key_players) {
      initChart(keyPlayerChart, barH(kp.top_key_players.slice(0, 8), 'label', 'impact_score', '#f97316'))
    }
  })
}

// 组件挂载时首次渲染所有图表
onMounted(() => renderAll())
// 监听props.importance变化，数据更新时重新渲染图表
watch(() => props.importance, renderAll)
// 组件卸载时销毁所有图表实例和ResizeObserver，防止内存泄漏
onUnmounted(() => {
  allCharts.forEach(({ chart, observer }) => { observer?.disconnect(); chart?.dispose() })
})
</script>

<style scoped>
.importance-container { display: flex; flex-direction: column; gap: 20px; }
.section { }
.section-title { font-size: 16px; font-weight: 600; color: #1e293b; margin-bottom: 6px; padding-bottom: 8px; border-bottom: 1px solid #22c55e; }
.section-desc { font-size: 12px; color: #64748b; line-height: 1.6; margin-bottom: 12px; padding: 8px 12px; background: #f0fdf4; border-radius: 8px; }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.chart-panel { background: #ffffff; border: 1px solid #22c55e; border-radius: 10px; padding: 14px; }
.chart-subtitle { font-size: 12px; color: #475569; margin-bottom: 4px; font-weight: 500; }
.chart-concept { font-size: 11px; color: #94a3b8; margin-bottom: 8px; line-height: 1.4; }
.chart-box { width: 100%; height: 280px; }
.chart-box-lg { width: 100%; height: 380px; }
.concept-panel { margin-bottom: 8px; }
.concept-title { font-size: 12px; font-weight: 600; color: #15803d; margin-bottom: 6px; }
.concept-text { font-size: 11px; color: #64748b; line-height: 1.5; }
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
