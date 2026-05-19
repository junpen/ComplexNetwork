<!-- 流转稳定性/风险分析组件：评估文书流转网络的抗毁能力、脆弱性和连锁失效风险 -->
<template>
  <div class="resilience-container">
    <!-- 概念说明面板：解释各稳定性与风险评估指标的含义 -->
    <div class="concept-panel">
      <div class="concept-title">💡 流转稳定性与风险评估概念说明</div>
      <div class="concept-grid">
        <div class="concept-item">
          <span class="concept-key">综合稳定性评分</span>
          <span class="concept-text">综合评估文书流转网络在面临单位缺失、通道中断等突发情况时保持正常运转的能力。评分越高表示网络越健壮。</span>
        </div>
        <div class="concept-item">
          <span class="concept-key">文书连通稳定度</span>
          <span class="concept-text">基于邻接矩阵特征值计算的连通稳定性指标，值越高表示文书流转路径的冗余性越好，即使部分通道中断也能找到替代路径。</span>
        </div>
        <div class="concept-item">
          <span class="concept-key">结构连通强度</span>
          <span class="concept-text">代数连通度（Fiedler值），反映文书流转网络的紧密程度。值越高表示各单位之间文书联系越紧密，网络越不容易分裂。</span>
        </div>
        <div class="concept-item">
          <span class="concept-key">总体流转风险评分</span>
          <span class="concept-text">综合各单位缺失后对文书流转网络造成的风险程度，值越高表示网络越脆弱，需要重点关注。</span>
        </div>
        <div class="concept-item">
          <span class="concept-key">关键枢纽单位数</span>
          <span class="concept-text">一旦缺失将导致文书流转网络分裂成不连通部分的单位数量（即"关节点"）。这些单位是维持全网文书互通的关键。</span>
        </div>
        <div class="concept-item">
          <span class="concept-key">唯一文书通道数</span>
          <span class="concept-text">一旦中断将导致部分单位完全无法收发文书的流转通道数量（即"桥接边"）。这些通道是文书流转的关键瓶颈。</span>
        </div>
      </div>
    </div>

    <div class="formula-section" v-if="resilience?.resilience_metrics">
      <div class="formula-header" @click="toggleFormula('resilience')">
        <span>📐 韧性指标计算公式与计算过程</span>
        <span class="formula-arrow">{{ expandedFormulas.has('resilience') ? '▲ 收起' : '▼ 展开' }}</span>
      </div>
      <div class="formula-body" v-if="expandedFormulas.has('resilience')">
        <div class="formula-block">
          <div class="formula-name">1. 自然连通度（文书连通稳定度）</div>
          <div class="formula-expr">NC = ln( (1/n) × Σᵢ e^(λᵢ) )
其中 λᵢ 为邻接矩阵 A 的第 i 个特征值，n 为节点数</div>
          <div class="formula-desc">基于邻接矩阵特征值的 e^λ 加权平均。反映网络的冗余连接程度，值越大表示替代路径越丰富，韧性越强。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">2. 代数连通度（结构连通强度）</div>
          <div class="formula-expr">μ₂ = 拉普拉斯矩阵 L 的第二小特征值
L = D - A（D为度矩阵，A为邻接矩阵）</div>
          <div class="formula-desc">即Fiedler值。仅在图连通时有意义，值越大表示网络连通性越强，越不容易被分裂。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">3. 谱半径</div>
          <div class="formula-expr">ρ(A) = max|λᵢ|，λᵢ ∈ 特征值集合 of A</div>
          <div class="formula-desc">邻接矩阵最大特征值的绝对值，反映网络中信息/影响的传播速度。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">4. 度同配性</div>
          <div class="formula-expr">r = 度-度 Pearson 相关系数
对每条边 (u,v) 计算 deg(u) 与 deg(v) 的相关系数</div>
          <div class="formula-desc">r&gt;0表示高度节点倾向连接高度节点（同配），r&lt;0表示高度节点倾向连接低度节点（异配）。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">5. 边连通度</div>
          <div class="formula-expr">λ(G) = min over all edge cuts |C|
使网络不连通所需移除的最少边数</div>
          <div class="formula-desc">衡量网络对边移除的抵抗能力。边连通度越高，网络越不容易因通道中断而分裂。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">6. 度异质性</div>
          <div class="formula-expr">H = σ(deg) / μ(deg)
即度分布的变异系数（标准差/均值）</div>
          <div class="formula-desc">值越大表示网络度分布越不均匀，存在高度集线器节点。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">7. 综合韧性评分</div>
          <div class="formula-expr">R = 0.30×NC_norm + 0.25×AC_norm + 0.25×ANC_norm + 0.20×ED_norm
归一化方式:
  NC_norm = min(NC/5.0, 1.0)
  AC_norm = min(AC/5.0, 1.0)
  ANC_norm = min(ANC/3.0, 1.0)
  ED_norm = min(ED×5, 1.0)</div>
          <div class="formula-desc">将四个关键韧性指标归一化到[0,1]后加权融合。评分越高表示网络抗毁能力越强。</div>
        </div>
      </div>
    </div>

    <!-- 核心指标卡片：展示6个关键数值指标 -->
    <div class="stat-cards" v-if="resilience?.resilience_metrics">
      <!-- 综合流转稳定性评分（0~1，越高越好） -->
      <div class="stat-card" :title="'综合评估文书流转网络在突发情况下保持正常运转的能力'">
        <div class="stat-value">{{ fmt(resilience.resilience_metrics.resilience_score) }}</div>
        <div class="stat-label">综合流转稳定性评分</div>
      </div>
      <!-- 文书连通稳定度（基于邻接矩阵特征值） -->
      <div class="stat-card" :title="'基于邻接矩阵特征值计算的连通稳定性，值越高路径冗余性越好'">
        <div class="stat-value">{{ fmt(resilience.resilience_metrics.natural_connectivity) }}</div>
        <div class="stat-label">文书连通稳定度</div>
      </div>
      <!-- 结构连通强度（Fiedler值，代数连通度） -->
      <div class="stat-card" :title="'代数连通度（Fiedler值），反映各单位之间文书联系的紧密程度'">
        <div class="stat-value">{{ fmt(resilience.resilience_metrics.algebraic_connectivity) }}</div>
        <div class="stat-label">结构连通强度</div>
      </div>
      <!-- 总体流转风险评分（超过0.1时显示红色警告样式） -->
      <div class="stat-card" :class="{ warning: resilience.vulnerability_metrics?.overall_vulnerability_score > 0.1 }" :title="'综合各单位缺失后造成的风险程度，值越高网络越脆弱'">
        <div class="stat-value">{{ fmt(resilience.vulnerability_metrics?.overall_vulnerability_score) }}</div>
        <div class="stat-label">总体流转风险评分</div>
      </div>
      <!-- 关键枢纽单位数（关节点数量） -->
      <div class="stat-card" :title="'一旦缺失将导致文书流转网络分裂的单位数量'">
        <div class="stat-value">{{ resilience.vulnerability_metrics?.articulation_points_count || 0 }}</div>
        <div class="stat-label">关键枢纽单位数</div>
      </div>
      <!-- 唯一文书通道数（桥接边数量） -->
      <div class="stat-card" :title="'一旦中断将导致部分单位无法收发文书的通道数量'">
        <div class="stat-value">{{ resilience.vulnerability_metrics?.bridges_count || 0 }}</div>
        <div class="stat-label">唯一文书通道数</div>
      </div>
    </div>

    <div class="formula-section" v-if="resilience?.attack_simulation">
      <div class="formula-header" @click="toggleFormula('attack')">
        <span>📐 扰动模拟计算公式与计算过程</span>
        <span class="formula-arrow">{{ expandedFormulas.has('attack') ? '▲ 收起' : '▼ 展开' }}</span>
      </div>
      <div class="formula-body" v-if="expandedFormulas.has('attack')">
        <div class="formula-block">
          <div class="formula-name">全局效率</div>
          <div class="formula-expr">E(G) = (1 / (n×(n-1))) × Σ_{i≠j} 1/d(i,j)
d(i,j) = 节点i到j的最短路径长度</div>
          <div class="formula-desc">所有节点对之间效率倒数的平均值。d(i,j)越小，1/d(i,j)越大，效率越高。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">攻击策略</div>
          <div class="formula-expr">• 介数中心性攻击: 按C_B(v)降序移除节点
• 度攻击: 按deg(v)降序移除节点
• PageRank攻击: 按PR(v)降序移除节点
• 随机攻击: 随机顺序移除节点</div>
          <div class="formula-desc">对每种策略，按比例从5%到100%逐步移除节点，记录每次移除后的LCC占比和全局效率。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">最大连通分量占比（LCC Ratio）</div>
          <div class="formula-expr">LCC(f) = |Largest Connected Component| / n
在移除比例 f 下的剩余网络中计算</div>
          <div class="formula-desc">最大连通分量占原始网络节点数的比例，是衡量网络连通性的核心指标。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">AUC（曲线下面积）</div>
          <div class="formula-expr">AUC = ∫₀¹ LCC(f) df ≈ 梯形法则求和
  = Σ (f_{i+1}-fᵢ) × (LCC(fᵢ)+LCC(f_{i+1}))/2</div>
          <div class="formula-desc">鲁棒性曲线下面积。AUC越大表示网络在该攻击策略下越鲁棒。</div>
        </div>
      </div>
    </div>

    <!-- 扰动模拟图表区域：连通保持率 + 流转效率（双列布局） -->
    <div class="charts-row" v-if="resilience?.attack_simulation">
      <!-- 左侧：连通保持率折线图 -->
      <div class="chart-panel">
        <h3 class="section-title">扰动模拟 — 文书连通保持率</h3>
        <div class="section-desc">模拟按不同策略逐步移除单位（如随机撤除、按往来频次撤除、按枢纽度撤除等），观察文书流转网络的连通性变化趋势。连通保持率越高，说明网络越能承受单位缺失的影响。</div>
        <div ref="attackLccChart" class="chart-box-lg"></div>
      </div>
      <!-- 右侧：流转效率折线图 -->
      <div class="chart-panel">
        <h3 class="section-title">扰动模拟 — 文书流转效率</h3>
        <div class="section-desc">在逐步移除单位的过程中，观察文书流转效率的变化。效率下降越慢，说明流转网络的抗扰动能力越强。</div>
        <div ref="attackEffChart" class="chart-box-lg"></div>
      </div>
    </div>

    <!-- 稳定性AUC对比 + 核心流转层分解（双列布局） -->
    <div class="charts-row" v-if="resilience?.robustness_curves || resilience?.resilience_metrics">
      <!-- 左侧：不同扰动策略下AUC值对比 -->
      <div class="chart-panel" v-if="resilience?.robustness_curves?.area_under_curve">
        <h3 class="section-title">稳定性 AUC 对比</h3>
        <div class="section-desc">不同扰动策略下连通保持率曲线下面积（AUC）的对比，AUC值越大表示该策略下网络越稳定。</div>
        <div ref="robustAucChart" class="chart-box"></div>
      </div>
      <!-- 右侧：K核分解图（按参与度逐层剥离） -->
      <div class="chart-panel" v-if="resilience?.vulnerability_metrics?.k_core_decomposition">
        <h3 class="section-title">核心流转层分解</h3>
        <div class="section-desc">按单位的文书流转参与度逐层剥离，k值越大表示该层的单位参与文书流转越深入。核心层（高k值）的单位是文书流转的中坚力量。</div>
        <div ref="kcoreChart" class="chart-box"></div>
      </div>
    </div>

    <div class="formula-section" v-if="resilience?.vulnerability_metrics">
      <div class="formula-header" @click="toggleFormula('vuln')">
        <span>📐 脆弱性指标计算公式与计算过程</span>
        <span class="formula-arrow">{{ expandedFormulas.has('vuln') ? '▲ 收起' : '▼ 展开' }}</span>
      </div>
      <div class="formula-body" v-if="expandedFormulas.has('vuln')">
        <div class="formula-block">
          <div class="formula-name">1. 割点（关键枢纽单位）</div>
          <div class="formula-expr">定义: 移除节点v后，连通分量数量增加
即: |CC(G\{v})| &gt; |CC(G)|</div>
          <div class="formula-desc">这些节点是网络的"瓶颈"，其故障会导致网络分裂成多个不连通的部分。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">2. 桥（唯一文书通道）</div>
          <div class="formula-expr">定义: 移除边e后，连通分量数量增加
即: |CC(G\{e})| &gt; |CC(G)|</div>
          <div class="formula-desc">这些边是网络中关键的"连接线"，一旦中断会导致部分单位完全无法收发文书。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">3. K-Core分解（核心流转层）</div>
          <div class="formula-expr">k-core: 最大子图，其中每个节点度 ≥ k
core_number(v) = max k，使得v属于k-core</div>
          <div class="formula-desc">按核心度逐层剥离分析网络的层次结构。核心度越高表示节点处于网络越核心位置。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">4. 节点脆弱性评分</div>
          <div class="formula-expr">V(v) = 0.6 × eff_drop + 0.4 × frag_increase
其中:
  eff_drop = 1 - E(G\{v}) / E(G)
  frag_increase = (components_after - components_before) / n</div>
          <div class="formula-desc">综合考量移除节点后效率下降和碎片化加剧两个维度。</div>
        </div>
      </div>
    </div>

    <!-- 单位流转风险贡献：各单位的缺失对整体风险的影响程度 -->
    <div class="section" v-if="resilience?.vulnerability_metrics?.node_vulnerability">
      <h3 class="section-title">单位流转风险贡献</h3>
      <div class="section-desc">各单位的缺失对整体文书流转风险的影响程度。贡献值越高的单位，其缺失将导致越严重的文书流转中断，需要优先保障其正常运转。</div>
      <div class="chart-panel">
        <div ref="nodeVulnChart" class="chart-box-lg"></div>
      </div>
    </div>

    <div class="formula-section" v-if="resilience?.cascading_failure_analysis?.capacity_threshold_analysis">
      <div class="formula-header" @click="toggleFormula('cascade')">
        <span>📐 连锁失效计算公式与计算过程</span>
        <span class="formula-arrow">{{ expandedFormulas.has('cascade') ? '▲ 收起' : '▼ 展开' }}</span>
      </div>
      <div class="formula-body" v-if="expandedFormulas.has('cascade')">
        <div class="formula-block">
          <div class="formula-name">级联失效模型</div>
          <div class="formula-expr">1. 初始负载: L(v) = deg(v)（以节点度值作为负载代理）
2. 容量阈值: Cap(v) = multiplier × avg_degree
   multiplier 取值: 0.5, 0.75, 1.0, 1.25, 1.5
3. 失效判定: 若 L(v) &gt; Cap(v)，则节点v失效
4. 负载转移: 失效节点被移除，其邻居的度值（负载）发生变化
5. 迭代传播: 重复步骤3-4，直到不再有新节点失效</div>
          <div class="formula-desc">模拟节点超负荷引发的连锁崩溃。multiplier越小表示容量越小，网络越容易发生大规模级联失效。</div>
        </div>
        <div class="formula-block">
          <div class="formula-name">级联路径追踪</div>
          <div class="formula-expr">失效条件: deg(v) &lt; avg_degree × 0.5
即节点剩余度低于平均度的一半时被视为失效</div>
          <div class="formula-desc">对特定触发节点追踪级联传播的路径和范围，记录波及的节点数量和传播深度。</div>
        </div>
      </div>
    </div>

    <!-- 连锁失效分析：模拟单位超负荷引发的级联崩溃 -->
    <div class="section" v-if="resilience?.cascading_failure_analysis?.capacity_threshold_analysis">
      <h3 class="section-title">连锁失效分析</h3>
      <div class="section-desc">当一个单位无法处理文书时（如超负荷），文书负载会转移到相邻单位，可能导致相邻单位也超负荷，形成连锁式的流转失效。阈值越高表示单位承受超载的能力越强，连锁失效范围越小。</div>
      <div class="chart-panel">
        <div ref="cascadeChart" class="chart-box"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

// 接收父组件传入的稳定性/风险分析数据
const props = defineProps({ resilience: { type: Object, default: null } })

// 各图表的DOM引用
const attackLccChart = ref(null)  // 扰动模拟-连通保持率折线图
const attackEffChart = ref(null)  // 扰动模拟-流转效率折线图
const robustAucChart = ref(null)  // 稳定性AUC对比条形图
const kcoreChart = ref(null)      // K核分解条形图
const nodeVulnChart = ref(null)   // 单位流转风险贡献条形图
const cascadeChart = ref(null)    // 连锁失效分析图

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
 * 数值格式化函数
 * @param {*} v - 待格式化的值
 * @returns {string} 格式化后的字符串（保留4位小数），空值返回'--'
 */
function fmt(v) {
  if (v == null) return '--'
  return typeof v === 'number' ? v.toFixed(4) : v
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

// 扰动模拟策略对应的颜色映射
const strategyColors = { random: '#3b82f6', degree: '#ef4444', betweenness: '#f59e0b', pagerank: '#22c55e',
  degree_targeted: '#ef4444', betweenness_targeted: '#f59e0b' }

// 扰动模拟策略对应的中文名称映射
const strategyLabels = { random: '随机撤除', degree: '按往来频次', betweenness: '按枢纽度', pagerank: '按影响力',
  degree_targeted: '按往来频次(定向)', betweenness_targeted: '按枢纽度(定向)' }

/**
 * 渲染所有图表：先销毁旧实例，再根据props数据重新初始化
 */
function renderAll() {
  // 销毁所有旧图表实例并断开ResizeObserver监听，防止内存泄漏
  allCharts.forEach(({ chart, observer }) => { observer?.disconnect(); chart?.dispose() })
  allCharts.length = 0
  // 数据为空时不渲染
  if (!props.resilience) return

  nextTick(() => {
    // ========== 扰动模拟折线图 ==========
    const attack = props.resilience.attack_simulation
    if (attack?.results && attack?.remove_fractions) {
      const fractions = attack.remove_fractions                         // 扰动比例数组（X轴数据）
      const lccSeries = []                                              // 连通保持率数据系列
      const effSeries = []                                              // 流转效率数据系列

      // 遍历每种扰动策略，构建对应的折线数据
      Object.entries(attack.results).forEach(([strategy, data]) => {
        const label = strategyLabels[strategy] || strategy
        // 提取各扰动比例下的平均连通保持率
        const lccData = fractions.map(f => data[f]?.avg_lcc_ratio || 0)
        // 提取各扰动比例下的平均流转效率
        const effData = fractions.map(f => data[f]?.avg_efficiency || 0)
        lccSeries.push({ name: label, type: 'line', data: lccData, smooth: true, lineStyle: { color: strategyColors[strategy] || '#94a3b8', width: 2 }, itemStyle: { color: strategyColors[strategy] || '#94a3b8' } })
        effSeries.push({ name: label, type: 'line', data: effData, smooth: true, lineStyle: { color: strategyColors[strategy] || '#94a3b8', width: 2 }, itemStyle: { color: strategyColors[strategy] || '#94a3b8' } })
      })

      /**
       * 生成折线图的通用ECharts配置
       * @param {Array} series - 数据系列数组
       * @param {string} yName - Y轴名称
       */
      const lineOption = (series, yName) => ({
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis' },                                    // 坐标轴触发提示
        legend: { data: Object.keys(attack.results).map(s => strategyLabels[s] || s), bottom: 0, textStyle: { color: '#475569', fontSize: 10 } },
        grid: { left: 55, right: 20, top: 15, bottom: 35 },
        xAxis: {
          type: 'category',
          data: fractions,                                               // X轴为扰动比例
          name: '扰动比例',
          nameTextStyle: { color: '#64748b' },
          axisLabel: { color: '#64748b' },
        },
        yAxis: {
          type: 'value',
          name: yName,                                                   // Y轴标签
          nameTextStyle: { color: '#64748b' },
          axisLabel: { color: '#64748b' },
          splitLine: { lineStyle: { color: '#e2e8f0' } },
        },
        series,
      })
      // 渲染连通保持率折线图
      initChart(attackLccChart, lineOption(lccSeries, '连通保持率'))
      // 渲染流转效率折线图
      initChart(attackEffChart, lineOption(effSeries, '流转效率'))
    }

    // ========== 稳定性AUC对比条形图 ==========
    const auc = props.resilience.robustness_curves?.area_under_curve
    if (auc) {
      // 将策略键名映射为中文标签
      const aucData = Object.entries(auc).map(([k, v]) => ({ name: strategyLabels[k] || k, value: v }))
      initChart(robustAucChart, {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 100, right: 40, top: 10, bottom: 20 },
        xAxis: {
          type: 'value',
          name: 'AUC',                                                   // X轴标签
          axisLabel: { color: '#64748b' },
          splitLine: { lineStyle: { color: '#e2e8f0' } },
        },
        yAxis: {
          type: 'category',                                              // Y轴显示策略名称
          data: aucData.map(d => d.name),
          axisLabel: { color: '#475569', fontSize: 11 },
        },
        series: [{
          type: 'bar',
          data: aucData.map(d => d.value),
          itemStyle: { color: '#16a34a', borderRadius: [0, 4, 4, 0] },  // 绿色柱条，右侧圆角
          barMaxWidth: 24,
          label: { show: true, position: 'right', color: '#475569', fontSize: 11, formatter: '{c}' }, // 柱条右侧显示数值
        }],
      })
    }

    // ========== K核分解条形图 ==========
    const kcore = props.resilience.vulnerability_metrics?.k_core_decomposition
    if (kcore) {
      // 将k值映射为"第N层"格式，统计每层的单位数量
      const kcData = Object.entries(kcore).map(([k, v]) => ({ name: `第${k}层`, value: v }))
      initChart(kcoreChart, {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 55, right: 20, top: 10, bottom: 25 },
        xAxis: {
          type: 'category',                                              // X轴显示层级
          data: kcData.map(d => d.name),
          axisLabel: { color: '#64748b' },
        },
        yAxis: {
          type: 'value',
          name: '单位数',                                                 // Y轴标签
          nameTextStyle: { color: '#64748b' },
          axisLabel: { color: '#64748b' },
          splitLine: { lineStyle: { color: '#e2e8f0' } },
        },
        series: [{
          type: 'bar',
          data: kcData.map(d => d.value),
          itemStyle: { color: '#22c55e', borderRadius: 4 },              // 绿色柱条，四角圆角
          barMaxWidth: 36,
        }],
      })
    }

    // ========== 单位流转风险贡献条形图 ==========
    const nv = props.resilience.vulnerability_metrics?.node_vulnerability?.top_nodes
    if (nv) {
      // 反转数组使最大值显示在顶部
      const nvData = [...nv].reverse()
      initChart(nodeVulnChart, {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 100, right: 50, top: 5, bottom: 15 },
        xAxis: {
          type: 'value',
          axisLabel: { color: '#64748b' },
          splitLine: { lineStyle: { color: '#e2e8f0' } },
        },
        yAxis: {
          type: 'category',                                              // Y轴显示单位名称
          data: nvData.map(d => d.label),
          axisLabel: { color: '#475569', fontSize: 10, width: 90, overflow: 'truncate' },
        },
        series: [{
          type: 'bar',
          data: nvData.map(d => d.vulnerability),                        // 风险贡献值
          itemStyle: { color: '#ef4444', borderRadius: [0, 3, 3, 0] },  // 红色柱条（表示风险）
          barMaxWidth: 18,
        }],
      })
    }

    // ========== 连锁失效分析图 ==========
    const cascade = props.resilience.cascading_failure_analysis?.capacity_threshold_analysis
    if (cascade) {
      // 将容量阈值键名转换为可读格式（如 threshold_0.5 → T=0.5）
      const casData = Object.entries(cascade).map(([k, v]) => ({
        name: k.replace('threshold_', 'T='),
        avg: v.avg_cascade_size,                                         // 平均连锁影响范围
        max: v.max_cascade_size,                                         // 最大连锁影响范围
      }))
      initChart(cascadeChart, {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis' },
        legend: { data: ['平均连锁影响范围', '最大连锁影响范围'], bottom: 0, textStyle: { color: '#475569', fontSize: 10 } },
        grid: { left: 55, right: 20, top: 10, bottom: 35 },
        xAxis: {
          type: 'category',                                              // X轴显示容量阈值
          data: casData.map(d => d.name),
          axisLabel: { color: '#64748b' },
        },
        yAxis: {
          type: 'value',
          axisLabel: { color: '#64748b' },
          splitLine: { lineStyle: { color: '#e2e8f0' } },
        },
        series: [
          { name: '平均连锁影响范围', type: 'bar', data: casData.map(d => d.avg), itemStyle: { color: '#16a34a', borderRadius: 3 }, barMaxWidth: 24 },
          { name: '最大连锁影响范围', type: 'bar', data: casData.map(d => d.max), itemStyle: { color: '#f59e0b', borderRadius: 3 }, barMaxWidth: 24 },
        ],
      })
    }
  })
}

// 组件挂载时首次渲染所有图表
onMounted(() => renderAll())
// 监听props.resilience变化，数据更新时重新渲染图表
watch(() => props.resilience, renderAll)
// 组件卸载时销毁所有图表实例和ResizeObserver，防止内存泄漏
onUnmounted(() => {
  allCharts.forEach(({ chart, observer }) => { observer?.disconnect(); chart?.dispose() })
})
</script>

<style scoped>
.resilience-container { display: flex; flex-direction: column; gap: 20px; }
.section { }
.section-title { font-size: 15px; font-weight: 600; color: #1e293b; margin-bottom: 6px; padding-bottom: 8px; border-bottom: 1px solid #22c55e; }
.section-desc { font-size: 12px; color: #64748b; line-height: 1.6; margin-bottom: 12px; padding: 8px 12px; background: #f0fdf4; border-radius: 8px; }
.stat-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
.stat-card { background: #ffffff; border: 1px solid #22c55e; border-radius: 10px; padding: 16px; text-align: center; cursor: help; }
.stat-card.warning { border-color: #ef4444; }
.stat-card.warning .stat-value { color: #ef4444; }
.stat-value { font-size: 28px; font-weight: 700; color: #16a34a; }
.stat-label { font-size: 12px; color: #475569; margin-top: 4px; }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.chart-panel { background: #ffffff; border: 1px solid #22c55e; border-radius: 10px; padding: 14px; }
.chart-box { width: 100%; height: 260px; }
.chart-box-lg { width: 100%; height: 380px; }

.concept-panel { background: #ffffff; border: 1px solid #22c55e; border-radius: 10px; padding: 16px; }
.concept-title { font-size: 14px; font-weight: 600; color: #15803d; margin-bottom: 12px; }
.concept-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 10px; }
.concept-item { display: flex; gap: 8px; padding: 8px 12px; background: #f0fdf4; border-radius: 8px; align-items: flex-start; }
.concept-key { font-size: 12px; font-weight: 600; color: #16a34a; white-space: nowrap; min-width: 100px; }
.concept-text { font-size: 12px; color: #475569; line-height: 1.5; }
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
