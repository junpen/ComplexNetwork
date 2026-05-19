<template>
  <div class="doc-container">
    <div class="doc-sidebar">
      <div class="sidebar-title">📖 目录导航</div>
      <div
        v-for="(section, idx) in sections"
        :key="idx"
        :class="['sidebar-item', { active: activeSection === idx }]"
        @click="scrollToSection(idx)"
      >
        <span class="sidebar-num">{{ idx + 1 }}</span>
        <span class="sidebar-label">{{ section.title }}</span>
      </div>
    </div>

    <div class="doc-main" ref="docMain">
      <div class="doc-header">
        <h1 class="doc-title">多源异构文书流转分析平台</h1>
        <p class="doc-subtitle">Multi-Source Heterogeneous Document Flow Analysis Platform</p>
        <p class="doc-version">版本 1.0.0 · 使用说明</p>
      </div>

      <div class="doc-section" v-for="(section, idx) in sections" :key="idx" :ref="el => sectionRefs[idx] = el">
        <div class="section-title-bar">
          <span class="section-icon">{{ section.icon }}</span>
          <h2 class="section-heading">{{ section.title }}</h2>
        </div>
        <div class="section-body" v-html="section.content"></div>
      </div>

      <div class="doc-footer">
        <span>多源异构文书流转分析平台 · 使用说明</span>
        <span>© 2025 NetworkX</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const docMain = ref(null)
const sectionRefs = ref([])
const activeSection = ref(0)

const sections = [
  {
    title: '平台简介',
    icon: '📋',
    content: `
      <p class="doc-p">多源异构文书流转分析平台是一个面向文书/文电流转场景的<b>复杂网络分析系统</b>。平台从达梦数据库中采集文书流转记录，自动构建文书流转网络，并利用复杂网络科学方法对流转体系进行全面分析，帮助您快速掌握流转体系的结构特征、识别关键枢纽单位、评估风险与稳定性。</p>
      <div class="doc-card">
        <div class="card-title">🎯 平台能为您做什么</div>
        <ul class="doc-list">
          <li><b>一览全局</b>：以可视化网络图展示全部文书流转关系，直观把握整体结构</li>
          <li><b>量化分析</b>：从往来频次、枢纽度、可达性等多维度量化每个单位的流转特征</li>
          <li><b>识别关键</b>：自动识别流转体系中的核心枢纽、不可替代单位和瓶颈节点</li>
          <li><b>评估风险</b>：评估流转网络的抗毁性、脆弱性和连锁失效风险</li>
          <li><b>输出结论</b>：自动生成分析结论报告，支持导出HTML/文本格式</li>
        </ul>
      </div>
    `
  },
  {
    title: '界面布局',
    icon: '🖥',
    content: `
      <p class="doc-p">平台界面由<b>顶部操作栏</b>、<b>功能Tab导航</b>、<b>主内容区</b>和<b>底部状态栏</b>四个区域组成：</p>
      <div class="layout-diagram">
        <div class="layout-row layout-header">
          <span>📱 顶部操作栏：平台标题 | 接收时间筛选 | 查询/重置/刷新按钮</span>
        </div>
        <div class="layout-row layout-tabs">
          <span>📑 Tab导航：流转概览 | 文书流转图 | 流转特征指标 | 关键单位分析 | 流转稳定性/风险 | 分析结论 | 使用说明</span>
        </div>
        <div class="layout-row layout-main">
          <span>📊 主内容区：根据选中的Tab展示对应的分析内容</span>
        </div>
        <div class="layout-row layout-footer">
          <span>📌 底部状态栏：平台信息 | 当前数据概况（单位数、文书流转数、已移除数）</span>
        </div>
      </div>
      <div class="doc-card">
        <div class="card-title">💡 使用流程建议</div>
        <div class="flow-steps">
          <div class="flow-step">
            <div class="step-num">1</div>
            <div class="step-content">
              <div class="step-title">设定查询条件</div>
              <div class="step-desc">在顶部选择接收时间范围，点击"查询"加载数据</div>
            </div>
          </div>
          <div class="flow-step">
            <div class="step-num">2</div>
            <div class="step-content">
              <div class="step-title">查看流转概览</div>
              <div class="step-desc">在"流转概览"Tab了解当前数据的基本情况</div>
            </div>
          </div>
          <div class="flow-step">
            <div class="step-num">3</div>
            <div class="step-content">
              <div class="step-title">浏览流转图</div>
              <div class="step-desc">在"文书流转图"Tab以可视化方式查看网络拓扑，可删除关注外的节点</div>
            </div>
          </div>
          <div class="flow-step">
            <div class="step-num">4</div>
            <div class="step-content">
              <div class="step-title">深入分析</div>
              <div class="step-desc">依次查看"流转特征指标"、"关键单位分析"、"流转稳定性/风险"三个分析Tab</div>
            </div>
          </div>
          <div class="flow-step">
            <div class="step-num">5</div>
            <div class="step-content">
              <div class="step-title">导出结论</div>
              <div class="step-desc">在"分析结论"Tab查看自动生成的结论报告，并导出HTML或文本文件</div>
            </div>
          </div>
        </div>
      </div>
    `
  },
  {
    title: '数据查询与筛选',
    icon: '🔍',
    content: `
      <p class="doc-p">平台顶部操作栏提供数据查询与筛选功能，所有分析模块共享同一份数据状态。</p>
      <div class="doc-card">
        <div class="card-title">⏰ 时间范围筛选</div>
        <ul class="doc-list">
          <li><b>起始时间</b>：设置接收时间的起始点，仅加载该时间之后的文书流转数据</li>
          <li><b>截止时间</b>：设置接收时间的截止点，仅加载该时间之前的文书流转数据</li>
          <li><b>查询</b>：设置时间范围后点击"查询"，系统重新从数据库加载数据并执行全部分析</li>
          <li><b>重置</b>：清空时间筛选和已删除节点，恢复到全量数据状态</li>
        </ul>
        <div class="tip-box">
          <span class="tip-icon">💡</span>
          <span class="tip-text">不设置时间范围时，系统默认加载全部数据。</span>
        </div>
      </div>
      <div class="doc-card">
        <div class="card-title">🔄 刷新分析</div>
        <p class="doc-p">点击右上角"刷新分析"按钮，系统将重新执行全部分析计算并刷新页面数据。该操作会根据当前设置的时间范围重新加载数据。</p>
      </div>
      <div class="doc-card">
        <div class="card-title">📊 底部状态栏</div>
        <p class="doc-p">页面底部实时显示当前数据概况：</p>
        <ul class="doc-list">
          <li><b>单位数</b>：当前网络中的单位（节点）总数</li>
          <li><b>文书流转数</b>：当前网络中的文书流转（边）总数</li>
          <li><b>已移除</b>：在流转图中被手动删除的单位数量（红色显示）</li>
        </ul>
      </div>
    `
  },
  {
    title: '流转概览',
    icon: '📊',
    content: `
      <p class="doc-p">"流转概览"是平台的默认首页，展示当前文书流转网络的基本统计信息，帮助您快速了解数据概况。</p>
      <div class="doc-card">
        <div class="card-title">📈 查看内容</div>
        <ul class="doc-list">
          <li><b>单位总数</b>：参与文书流转的单位总量</li>
          <li><b>文书流转总数</b>：所有文书流转关系的总量</li>
          <li><b>网络密度</b>：实际文书流转覆盖程度（0~1之间，越接近1表示往来越密集）</li>
          <li><b>连通性</b>：网络是否为全连通（任意两个单位之间都有路径可达）</li>
        </ul>
      </div>
      <div class="doc-card">
        <div class="card-title">📖 如何解读</div>
        <div class="tip-box">
          <span class="tip-icon">💡</span>
          <span class="tip-text">网络密度低于0.15表示流转网络较为稀疏，大部分单位之间没有直接往来；高于0.3则表示流转覆盖面较广。连通性为"全连通"是理想状态，存在多个连通分量则说明部分单位之间完全无法通过文书链路到达。</span>
        </div>
      </div>
    `
  },
  {
    title: '文书流转图',
    icon: '🔗',
    content: `
      <p class="doc-p">"文书流转图"Tab提供<b>交互式有向网络图</b>可视化，您可以直观地查看单位之间的文书流转关系，并支持多种交互操作。</p>
      <div class="doc-card">
        <div class="card-title">🖱 图操作方式</div>
        <table class="doc-table">
          <thead><tr><th>操作</th><th>方式</th><th>效果</th></tr></thead>
          <tbody>
            <tr><td>缩放</td><td>鼠标滚轮</td><td>放大/缩小图形</td></tr>
            <tr><td>平移</td><td>鼠标左键拖拽空白区域</td><td>移动画布</td></tr>
            <tr><td>查看节点信息</td><td>鼠标悬停节点</td><td>显示单位名称、连接数</td></tr>
            <tr><td>删除节点</td><td>右键点击节点</td><td>弹出菜单选择"删除该节点"</td></tr>
            <tr><td>恢复全部节点</td><td>右键点击空白区域</td><td>弹出菜单选择"恢复全部节点"</td></tr>
          </tbody>
        </table>
      </div>
      <div class="doc-card">
        <div class="card-title">🎨 图元素说明</div>
        <ul class="doc-list">
          <li><b>节点（圆形）</b>：代表一个单位，所有单位使用统一颜色标识</li>
          <li><b>边（带箭头的连线）</b>：代表一条文书流转关系，箭头方向表示流转方向</li>
          <li><b>节点大小</b>：与该单位的连接数（往来频次）成正比</li>
          <li><b>边的粗细</b>：与流转权重成正比</li>
        </ul>
      </div>
      <div class="doc-card">
        <div class="card-title">✂️ 删除节点功能</div>
        <p class="doc-p">在流转图中右键点击某个节点，选择"删除该节点"后：</p>
        <ul class="doc-list">
          <li>该节点及其所有连接的边会从视图中移除</li>
          <li>系统自动基于剩余节点重新计算所有分析结果</li>
          <li>底部状态栏显示红色"已移除"数量</li>
          <li>右键空白处选择"恢复全部节点"可一键恢复</li>
        </ul>
        <div class="tip-box">
          <span class="tip-icon">💡</span>
          <span class="tip-text">删除节点功能适用于：排除干扰单位后聚焦分析核心子网络；模拟某个单位失效后对整体流转的影响。</span>
        </div>
      </div>
    `
  },
  {
    title: '流转特征指标',
    icon: '📈',
    content: `
      <p class="doc-p">"流转特征指标"Tab从多个维度对文书流转网络的拓扑结构进行量化分析。每个分析子模块配有<b>图表可视化</b>和<b>概念说明面板</b>，帮助您理解指标含义。</p>
      <div class="doc-card">
        <div class="card-title">📏 度分布分析</div>
        <p class="doc-p">衡量各单位的文书往来频次分布情况。</p>
        <ul class="doc-list">
          <li><b>往来频次排名</b>：列出往来最频繁的Top单位及其频次</li>
          <li><b>接收/发送频次</b>：分别统计每个单位接收和发出文书的频次</li>
          <li><b>变异系数</b>：大于0.7说明负载严重集中于少数单位</li>
        </ul>
        <div class="tip-box">
          <span class="tip-icon">📖</span>
          <span class="tip-text">概念：度（Degree）= 一个单位与其他单位的文书往来总次数。入度 = 接收次数，出度 = 发送次数。</span>
        </div>
      </div>
      <div class="doc-card">
        <div class="card-title">📐 距离分析</div>
        <p class="doc-p">衡量单位之间文书传递的路径长度。</p>
        <ul class="doc-list">
          <li><b>平均转发层级</b>：所有单位对之间的平均最短转发路径，越小越高效（≤2为优秀）</li>
          <li><b>最大转发跨度</b>：全网最长的最短路径，反映最远端的传递距离</li>
          <li><b>连通分量</b>：如果不连通，表示存在互相无法到达的"孤岛"</li>
        </ul>
        <div class="tip-box">
          <span class="tip-icon">📖</span>
          <span class="tip-text">概念：路径长度 = 文书从A传递到B所需经过的中间环节数量。</span>
        </div>
      </div>
      <div class="doc-card">
        <div class="card-title">🎯 中心性分析</div>
        <p class="doc-p">从五个维度衡量每个单位在网络中的"重要性"。</p>
        <table class="doc-table">
          <thead><tr><th>指标</th><th>含义</th><th>怎么看</th></tr></thead>
          <tbody>
            <tr><td>度中心性</td><td>直接往来活跃度</td><td>值越高，与越多单位有直接往来</td></tr>
            <tr><td>介数中心性</td><td>文书传递枢纽度</td><td>值越高，越多最短路径经过此单位</td></tr>
            <tr><td>接近中心性</td><td>流转可达性</td><td>值越高，到所有单位的平均距离越短</td></tr>
            <tr><td>特征向量中心性</td><td>连接质量</td><td>值越高，与越多"重要"单位有往来</td></tr>
            <tr><td>PageRank</td><td>全局影响力</td><td>值越高，在全网中的综合影响力越大</td></tr>
          </tbody>
        </table>
      </div>
      <div class="doc-card">
        <div class="card-title">🔗 聚集分析</div>
        <p class="doc-p">衡量同级单位之间的横向协作水平。</p>
        <ul class="doc-list">
          <li><b>平均聚集系数</b>：接近0表示横向直接沟通极少（严格的层级传递模式）</li>
          <li><b>三角形计数</b>：三方互通（A↔B、B↔C、A↔C）的数量</li>
        </ul>
      </div>
      <div class="doc-card">
        <div class="card-title">🌐 网络级指标</div>
        <ul class="doc-list">
          <li><b>度同质性</b>：正值表示"强强互通"，负值表示核心枢纽主要与边缘单位往来</li>
          <li><b>幂律指数</b>：接近1表示典型的层级指挥结构（少数核心连接大量边缘）</li>
        </ul>
      </div>
    `
  },
  {
    title: '关键单位分析',
    icon: '⭐',
    content: `
      <p class="doc-p">"关键单位分析"Tab从多个维度识别和评估流转网络中的核心单位，帮助您确定哪些单位需要重点保护。</p>
      <div class="doc-card">
        <div class="card-title">🏆 综合重要度</div>
        <p class="doc-p">融合五种中心性指标（度中心性、介数中心性、接近中心性、特征向量中心性、PageRank）的加权综合评分，自动排名列出最重要的单位。</p>
        <div class="tip-box">
          <span class="tip-icon">💡</span>
          <span class="tip-text">关注排名第一的单位——它通常是整个文书流转体系的核心枢纽，需要最高级别的通信保障。</span>
        </div>
      </div>
      <div class="doc-card">
        <div class="card-title">🔄 可替代程度</div>
        <p class="doc-p">评估每个单位被其他单位替代的难易程度。分为两组对比展示：</p>
        <ul class="doc-list">
          <li><b>⚠️ 最不可替代单位</b>：替代度最低的单位，一旦缺失将严重影响流转体系</li>
          <li><b>✅ 最可替代单位</b>：替代度较高的单位，即使缺失也有其他单位可以替代其功能</li>
        </ul>
        <div class="tip-box">
          <span class="tip-icon">💡</span>
          <span class="tip-text">不可替代单位应作为重点保护对象，考虑为其建立备份机制。</span>
        </div>
      </div>
      <div class="doc-card">
        <div class="card-title">🕳 结构洞分析</div>
        <p class="doc-p">识别占据"流转瓶颈"位置的单位——它们连接着网络中不同的群体，且这些群体之间缺乏直接联系。</p>
        <ul class="doc-list">
          <li><b>约束值</b>：越低表示该单位占据的瓶颈位置越关键</li>
          <li><b>有效规模</b>：越高表示该单位的信息来源越多元</li>
        </ul>
      </div>
      <div class="doc-card">
        <div class="card-title">🔑 关键参与者分析</div>
        <p class="doc-p">评估移除每个单位后对网络的影响程度。影响得分越高，说明该单位越关键，移除后对流转体系的破坏越大。</p>
      </div>
      <div class="doc-card">
        <div class="card-title">⚠️ 脆弱性贡献</div>
        <p class="doc-p">量化每个单位对网络整体脆弱性的贡献程度。得分越高的单位，其存在本身就在增加整个流转体系的脆弱性（通常是因为过多流转依赖于该单位）。</p>
      </div>
    `
  },
  {
    title: '流转稳定性/风险',
    icon: '🛡',
    content: `
      <p class="doc-p">"流转稳定性/风险"Tab评估流转网络的抗毁能力和风险水平，帮助您了解流转体系在遭受干扰时的表现。</p>
      <div class="doc-card">
        <div class="card-title">💪 韧性指标</div>
        <ul class="doc-list">
          <li><b>综合稳定性评分</b>：0~1之间，≥0.65为良好，0.4~0.65为中等，＜0.4为较差</li>
          <li><b>边连通度</b>：使网络分裂所需移除的最少文书通道数。值为1表示存在"生命线"通道</li>
          <li><b>代数连通度</b>：衡量网络的紧密程度，越高越稳定</li>
        </ul>
        <div class="tip-box">
          <span class="tip-icon">📖</span>
          <span class="tip-text">概念：韧性（Resilience）= 网络从干扰中恢复的能力。评分越高，流转体系越能承受单位/通道的损失。</span>
        </div>
      </div>
      <div class="doc-card">
        <div class="card-title">🚨 脆弱性指标</div>
        <ul class="doc-list">
          <li><b>关键枢纽单位（关键点）</b>：移除后导致网络分裂的单位，即"单点故障"节点</li>
          <li><b>唯一文书通道（桥接边）</b>：移除后导致网络不连通的通道，即"生命线"通道</li>
          <li><b>K核分解</b>：按度值逐层剥离网络，识别核心层与边缘层</li>
        </ul>
        <div class="tip-box">
          <span class="tip-icon">💡</span>
          <span class="tip-text">关键枢纽单位和唯一文书通道越多，说明流转体系的脆弱点越多，需要重点保护。</span>
        </div>
      </div>
      <div class="doc-card">
        <div class="card-title">⚔️ 扰动模拟（攻击模拟）</div>
        <p class="doc-p">模拟不同干扰策略下移除单位对网络连通性的影响：</p>
        <ul class="doc-list">
          <li><b>随机扰动</b>：随机移除单位，模拟无差别干扰</li>
          <li><b>度攻击</b>：优先移除往来最活跃的单位</li>
          <li><b>介数攻击</b>：优先移除枢纽度最高的单位</li>
          <li><b>PageRank攻击</b>：优先移除影响力最大的单位</li>
        </ul>
        <p class="doc-p">图表展示在不同移除比例下，网络最大连通分量占比的变化。下降越快说明网络越脆弱。</p>
      </div>
      <div class="doc-card">
        <div class="card-title">💥 连锁失效分析</div>
        <p class="doc-p">模拟某个单位失效后引发的级联崩溃效应。当一个单位失效后，其负载转移到邻居单位，超出容量的邻居也会失效，形成连锁反应。</p>
        <ul class="doc-list">
          <li><b>高风险触发点</b>：失效后波及范围最大的单位</li>
          <li><b>容量阈值分析</b>：不同容量倍数下的连锁规模对比</li>
        </ul>
      </div>
      <div class="doc-card">
        <div class="card-title">📉 鲁棒性曲线</div>
        <p class="doc-p">展示不同攻击策略下的鲁棒性曲线（横轴为移除比例，纵轴为最大连通分量占比）：</p>
        <ul class="doc-list">
          <li><b>曲线下面积（AUC）越接近1</b>：抗毁能力越强</li>
          <li><b>定向攻击曲线远低于随机攻击</b>：说明网络对精准打击极为脆弱</li>
        </ul>
      </div>
    `
  },
  {
    title: '分析结论与导出',
    icon: '📋',
    content: `
      <p class="doc-p">"分析结论"Tab基于实时数据<b>自动生成</b>完整的分析结论报告，包含9个维度的分析结论和综合改进建议。</p>
      <div class="doc-card">
        <div class="card-title">📑 报告内容</div>
        <table class="doc-table">
          <thead><tr><th>章节</th><th>内容</th></tr></thead>
          <tbody>
            <tr><td>一、流转网络基本结构</td><td>单位数、流转数、密集度、连通性评价</td></tr>
            <tr><td>二、文书流转负载均衡性</td><td>往来频次分布、高频单位Top5</td></tr>
            <tr><td>三、核心枢纽与影响力分析</td><td>各维度枢纽单位识别与影响力评估</td></tr>
            <tr><td>四、流转网络拓扑结构</td><td>聚集度、同质性、层级特征分析</td></tr>
            <tr><td>五、关键单位识别与可替代性</td><td>最不可替代/最可替代单位对比</td></tr>
            <tr><td>六、文书流转瓶颈分析</td><td>结构洞位置的关键瓶颈单位</td></tr>
            <tr><td>七、流转稳定性与脆弱性评估</td><td>稳定性评分、关键点、唯一通道统计</td></tr>
            <tr><td>八、扰动模拟与抗毁性</td><td>各攻击策略对比、脆弱程度评估</td></tr>
            <tr><td>九、连锁失效风险评估</td><td>高风险触发点、连锁规模评估</td></tr>
            <tr><td>★ 综合结论与改进建议</td><td>核心发现汇总 + 针对性改进建议</td></tr>
          </tbody>
        </table>
      </div>
      <div class="doc-card">
        <div class="card-title">🔴 风险等级说明</div>
        <p class="doc-p">每个分析结论章节标注有风险等级标签：</p>
        <table class="doc-table">
          <thead><tr><th>等级</th><th>颜色</th><th>含义</th></tr></thead>
          <tbody>
            <tr><td>高风险</td><td><span style="color:#dc2626;font-weight:700;">● 红色</span></td><td>存在严重风险，需立即关注</td></tr>
            <tr><td>中风险</td><td><span style="color:#d97706;font-weight:700;">● 琥珀色</span></td><td>存在明显不足，建议改进</td></tr>
            <tr><td>低风险</td><td><span style="color:#16a34a;font-weight:700;">● 绿色</span></td><td>状况良好，可保持现状</td></tr>
          </tbody>
        </table>
      </div>
      <div class="doc-card">
        <div class="card-title">📥 导出报告</div>
        <p class="doc-p">报告页面右上角提供两个导出按钮：</p>
        <ul class="doc-list">
          <li><b>📄 导出HTML报告</b>：生成带完整样式的HTML文件，可直接在浏览器中打开查看或打印</li>
          <li><b>📝 导出文本报告</b>：生成纯文本文件，方便粘贴到其他文档中</li>
        </ul>
        <div class="tip-box">
          <span class="tip-icon">💡</span>
          <span class="tip-text">导出的报告反映的是当前时刻的数据状态和分析结论。更改查询条件后，需重新导出才能获得最新报告。</span>
        </div>
      </div>
    `
  },
  {
    title: '术语对照表',
    icon: '📖',
    content: `
      <p class="doc-p">平台将复杂网络科学中的数学术语映射为文书流转场景的业务术语，便于理解：</p>
      <table class="doc-table">
        <thead><tr><th>您看到的术语</th><th>对应概念</th><th>含义说明</th></tr></thead>
        <tbody>
          <tr><td>单位</td><td>节点（Node）</td><td>参与文书流转的实体（指挥部、部队、战区等）</td></tr>
          <tr><td>文书流转</td><td>边（Edge）</td><td>两个单位之间的文书传递关系</td></tr>
          <tr><td>往来频次</td><td>度（Degree）</td><td>一个单位与其他单位的文书往来总次数</td></tr>
          <tr><td>接收频次</td><td>入度（In-Degree）</td><td>单位接收文书的总次数</td></tr>
          <tr><td>发送频次</td><td>出度（Out-Degree）</td><td>单位发出文书的总次数</td></tr>
          <tr><td>转发层级</td><td>路径长度（Path Length）</td><td>文书传递所经过的中间环节数</td></tr>
          <tr><td>最大转发跨度</td><td>网络直径（Diameter）</td><td>全网最远的转发路径长度</td></tr>
          <tr><td>流转孤岛</td><td>连通分量（Component）</td><td>互相可达但与其他部分隔离的单位群</td></tr>
          <tr><td>横向协作度</td><td>聚集系数（Clustering）</td><td>同级单位之间直接互通的程度</td></tr>
          <tr><td>枢纽度</td><td>介数中心性（Betweenness）</td><td>单位作为文书传递中转站的频率</td></tr>
          <tr><td>可达性</td><td>接近中心性（Closeness）</td><td>单位到所有其他单位的平均转发效率</td></tr>
          <tr><td>流转瓶颈</td><td>结构洞（Structural Hole）</td><td>连接不同群体且群体间无直接联系的枢纽位置</td></tr>
          <tr><td>关键枢纽单位</td><td>关键点（Articulation Point）</td><td>移除后导致部分单位完全失联的单位</td></tr>
          <tr><td>唯一文书通道</td><td>桥接边（Bridge）</td><td>移除后导致网络分裂的文书通道</td></tr>
          <tr><td>扰动模拟</td><td>攻击模拟（Attack Simulation）</td><td>模拟各种干扰对流转体系的影响</td></tr>
          <tr><td>连锁崩溃</td><td>连锁失效（Cascading Failure）</td><td>一个单位失效引发其他单位相继失效的连锁反应</td></tr>
          <tr><td>抗毁性</td><td>鲁棒性（Robustness）</td><td>网络在干扰下维持正常运转的能力</td></tr>
          <tr><td>稳定性</td><td>韧性（Resilience）</td><td>网络从干扰中恢复的能力</td></tr>
          <tr><td>可替代程度</td><td>可替代性（Substitutability）</td><td>一个单位被其他单位替代的难易程度</td></tr>
        </tbody>
      </table>
    `
  },
  {
    title: '常见问题',
    icon: '❓',
    content: `
      <div class="doc-card">
        <div class="card-title">❓ 页面加载后没有数据</div>
        <p class="doc-p">请确认后端服务已启动（运行 <code>python server.py</code>），且达梦数据库服务正常运行。如果数据库不可用，系统会自动使用样例数据。</p>
      </div>
      <div class="doc-card">
        <div class="card-title">❓ 分析结果很长时间没出来</div>
        <p class="doc-p">韧性分析中的攻击模拟和连锁失效分析计算量较大，数据量大时可能需要数十秒。请耐心等待，不要重复点击"刷新分析"。</p>
      </div>
      <div class="doc-card">
        <div class="card-title">❓ 删除节点后如何恢复</div>
        <p class="doc-p">有两种方式：①在流转图中右键点击空白区域，选择"恢复全部节点"；②点击顶部"重置"按钮，会同时清空时间筛选和已删除节点。</p>
      </div>
      <div class="doc-card">
        <div class="card-title">❓ 导出的报告内容是空白的</div>
        <p class="doc-p">请先等待所有分析模块加载完成（页面不再显示"正在分析文书流转数据..."），然后再点击导出按钮。报告内容基于当前已加载的分析数据生成。</p>
      </div>
      <div class="doc-card">
        <div class="card-title">❓ 分析结论中的数据与预期不符</div>
        <p class="doc-p">请检查：①是否设置了时间范围筛选，导致数据子集与预期不同；②是否在流转图中删除了某些节点；③点击"重置"恢复全量数据后重新分析。</p>
      </div>
      <div class="doc-card">
        <div class="card-title">❓ 如何切换数据源</div>
        <p class="doc-p">数据源由后端配置文件 config.py 中的 DATA_SOURCE 字段控制。设置为 "database" 时从达梦数据库加载，数据库不可用时自动回退到样例数据文件。</p>
      </div>
    `
  },
]

function scrollToSection(idx) {
  activeSection.value = idx
  const el = sectionRefs.value[idx]
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function handleScroll() {
  if (!docMain.value) return
  const scrollTop = docMain.value.scrollTop
  let currentIdx = 0
  for (let i = 0; i < sectionRefs.value.length; i++) {
    const el = sectionRefs.value[i]
    if (el && el.offsetTop - 120 <= scrollTop) {
      currentIdx = i
    }
  }
  activeSection.value = currentIdx
}

onMounted(() => {
  if (docMain.value) {
    docMain.value.addEventListener('scroll', handleScroll)
  }
})

onUnmounted(() => {
  if (docMain.value) {
    docMain.value.removeEventListener('scroll', handleScroll)
  }
})
</script>

<style scoped>
.doc-container {
  display: flex;
  gap: 0;
  max-width: 1200px;
  margin: 0 auto;
  height: calc(100vh - 200px);
  min-height: 500px;
}

.doc-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid #dcfce7;
  padding: 16px 0;
  overflow-y: auto;
  border-radius: 10px 0 0 10px;
  border: 1px solid #dcfce7;
  border-right: none;
}

.sidebar-title {
  font-size: 14px;
  font-weight: 700;
  color: #15803d;
  padding: 0 16px 12px;
  border-bottom: 1px solid #f0fdf4;
  margin-bottom: 8px;
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 16px;
  cursor: pointer;
  font-size: 13px;
  color: #475569;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.sidebar-item:hover {
  background: #f0fdf4;
  color: #15803d;
}

.sidebar-item.active {
  background: #f0fdf4;
  color: #16a34a;
  border-left-color: #16a34a;
  font-weight: 600;
}

.sidebar-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #e2e8f0;
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

.sidebar-item.active .sidebar-num {
  background: #16a34a;
  color: #fff;
}

.doc-main {
  flex: 1;
  overflow-y: auto;
  background: #ffffff;
  padding: 32px 40px;
  border-radius: 0 10px 10px 0;
  border: 1px solid #dcfce7;
  border-left: none;
  scroll-behavior: smooth;
}

.doc-header {
  text-align: center;
  padding-bottom: 28px;
  margin-bottom: 32px;
  border-bottom: 2px solid #22c55e;
}

.doc-title {
  font-size: 28px;
  font-weight: 800;
  color: #15803d;
  margin-bottom: 8px;
}

.doc-subtitle {
  font-size: 14px;
  color: #64748b;
  letter-spacing: 1px;
}

.doc-version {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 8px;
}

.doc-section {
  margin-bottom: 36px;
}

.section-title-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
  border-radius: 8px;
  border-left: 4px solid #16a34a;
  margin-bottom: 16px;
}

.section-icon {
  font-size: 20px;
}

.section-heading {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.section-body {
  padding: 0 8px;
}

.doc-p {
  font-size: 14px;
  color: #334155;
  line-height: 1.8;
  margin: 8px 0;
}

.doc-card {
  background: #f8faf8;
  border: 1px solid #dcfce7;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 16px;
}

.card-title {
  font-size: 15px;
  font-weight: 700;
  color: #15803d;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #dcfce7;
}

.doc-list {
  padding-left: 20px;
  font-size: 14px;
  color: #334155;
  line-height: 2;
}

.doc-list li {
  margin-bottom: 2px;
}

.doc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-top: 8px;
}

.doc-table th {
  background: #f0fdf4;
  color: #15803d;
  font-weight: 600;
  padding: 10px 12px;
  text-align: left;
  border-bottom: 2px solid #bbf7d0;
}

.doc-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
}

.doc-table tr:hover td {
  background: #f0fdf4;
}

.tip-box {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 12px 16px;
  margin-top: 12px;
}

.tip-icon {
  font-size: 16px;
  flex-shrink: 0;
  margin-top: 1px;
}

.tip-text {
  font-size: 13px;
  color: #92400e;
  line-height: 1.7;
}

.layout-diagram {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 16px 0;
  padding: 16px;
  background: #f8faf8;
  border-radius: 10px;
  border: 1px solid #dcfce7;
}

.layout-row {
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 12px;
  color: #334155;
  text-align: center;
}

.layout-header {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  font-weight: 600;
}

.layout-tabs {
  background: #ffffff;
  border: 1px solid #dcfce7;
  font-size: 11px;
}

.layout-main {
  background: #ffffff;
  border: 2px dashed #22c55e;
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.layout-footer {
  background: #f8faf8;
  border: 1px solid #dcfce7;
  font-size: 11px;
}

.flow-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.flow-step {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 12px 16px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #dcfce7;
}

.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: #16a34a;
  color: #fff;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.step-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.step-desc {
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
}

.doc-footer {
  display: flex;
  justify-content: space-between;
  padding-top: 20px;
  margin-top: 20px;
  border-top: 2px solid #dcfce7;
  font-size: 12px;
  color: #94a3b8;
}

@media (max-width: 900px) {
  .doc-container {
    flex-direction: column;
    height: auto;
  }
  .doc-sidebar {
    width: 100%;
    border-radius: 10px 10px 0 0;
    border-right: 1px solid #dcfce7;
    border-bottom: none;
    display: flex;
    flex-wrap: wrap;
    padding: 12px;
    gap: 4px;
  }
  .sidebar-title {
    width: 100%;
    border-bottom: none;
    margin-bottom: 4px;
    padding: 0 8px 8px;
  }
  .sidebar-item {
    padding: 6px 10px;
    border-left: none;
    border-bottom: 2px solid transparent;
  }
  .sidebar-item.active {
    border-left-color: transparent;
    border-bottom-color: #16a34a;
  }
  .doc-main {
    border-radius: 0 0 10px 10px;
    border-left: 1px solid #dcfce7;
    padding: 24px 20px;
  }
}
</style>
