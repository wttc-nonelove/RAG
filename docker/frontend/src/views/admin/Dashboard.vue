<template>
  <div>
    <!-- 页面标题区域 -->
    <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:12px;padding:24px 28px;margin-bottom:20px">
      <h2 style="color:#fff;margin:0;font-size:22px;font-weight:600">工作台</h2>
      <p style="color:rgba(255,255,255,0.8);margin:6px 0 0;font-size:13px">欢迎回来，{{ username }}！系统运行正常</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16">
      <el-col :span="4" v-for="item in stats" :key="item.label">
        <div class="stat-card" :style="{'--accent': item.iconColor}">
          <div class="stat-icon" :style="{background: item.bgColor}">
            <el-icon :size="22" :color="item.iconColor"><component :is="item.icon" /></el-icon>
          </div>
          <div>
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-value">{{ item.value }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 问答趋势图 + 系统状态 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="16">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">问答趋势</span>
            <el-radio-group v-model="trendDays" size="small" @change="loadTrends">
              <el-radio-button :value="7">近7天</el-radio-button>
              <el-radio-button :value="30">近30天</el-radio-button>
            </el-radio-group>
          </div>
          <div ref="trendChartRef" style="width:100%;height:280px"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="panel" style="height:100%">
          <div class="panel-header">
            <span class="panel-title">系统状态</span>
            <span class="status-dot" :class="allHealthy ? 'healthy' : 'unhealthy'"></span>
          </div>
          <div v-for="(status, name) in systemStatus" :key="name" class="status-item">
            <div style="display:flex;align-items:center;gap:10px">
              <span class="status-dot" :class="status === 'ok' ? 'healthy' : 'unhealthy'"></span>
              <span style="font-size:14px;font-weight:500">{{ serviceNames[name] || name }}</span>
            </div>
            <el-tag :type="status === 'ok' ? 'success' : 'danger'" size="small" effect="dark" round>
              {{ status === 'ok' ? '正常' : '异常' }}
            </el-tag>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 文档分布 + 存储用量 + 快捷操作 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="8">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">文档分布</span>
          </div>
          <div ref="docTypeChartRef" style="width:100%;height:220px"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">存储用量</span>
          </div>
          <div style="padding:20px 0">
            <div style="text-align:center;margin-bottom:16px">
              <div style="font-size:36px;font-weight:700;color:#409eff">{{ storage.documents_mb }}</div>
              <div style="font-size:13px;color:#909399;margin-top:4px">MB 已使用</div>
            </div>
            <el-progress :percentage="storagePercent" :stroke-width="14" :format="(p) => p + '%'" style="margin:0 20px" />
            <div style="font-size:12px;color:#909399;margin-top:12px;text-align:center">向量库：约 {{ totalChunks.toLocaleString() }} 条向量</div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">快捷操作</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:4px">
            <div v-for="action in quickActions" :key="action.label"
              class="action-card"
              :style="{'--bg': action.bgColor, '--color': action.iconColor}"
              @click="$router.push(action.route)">
              <el-icon :size="28" :color="action.iconColor"><component :is="action.icon" /></el-icon>
              <div class="action-label">{{ action.label }}</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, markRaw } from 'vue'
import * as echarts from 'echarts'
import { Document, ChatDotRound, User, Share, SuccessFilled, Timer, UploadFilled, Position, Compass, Setting } from '@element-plus/icons-vue'
import { getStats, getTrends, getStorage, getSystemStatus } from '../../api/dashboard'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const username = computed(() => auth.user?.username || '管理员')

const stats = ref([
  { label: '文档总数', value: 0, icon: markRaw(Document), bgColor: '#ecf5ff', iconColor: '#409eff' },
  { label: '解析成功率', value: '0%', icon: markRaw(SuccessFilled), bgColor: '#f0f9eb', iconColor: '#67c23a' },
  { label: '问答总次数', value: 0, icon: markRaw(ChatDotRound), bgColor: '#fdf6ec', iconColor: '#e6a23c' },
  { label: '今日问答', value: 0, icon: markRaw(Timer), bgColor: '#fef0f0', iconColor: '#f56c6c' },
  { label: '活跃用户', value: 0, icon: markRaw(User), bgColor: '#f4f4f5', iconColor: '#909399' },
  { label: '向量片段', value: 0, icon: markRaw(Share), bgColor: '#ecf5ff', iconColor: '#409eff' },
])

const trendDays = ref(7)
const trendChartRef = ref(null)
const docTypeChartRef = ref(null)
let trendChart = null
let docTypeChart = null

const systemStatus = reactive({
  mysql: 'ok',
  redis: 'ok',
  neo4j: 'ok',
  chromadb: 'ok',
})

const serviceNames = {
  mysql: 'MySQL',
  redis: 'Redis',
  neo4j: 'Neo4j',
  chromadb: 'ChromaDB',
}

const allHealthy = computed(() => Object.values(systemStatus).every(s => s === 'ok'))

const storage = reactive({
  documents_mb: 0,
})

const totalChunks = ref(0)
const docTypeCounts = ref({})

const storagePercent = computed(() => {
  return Math.min(Math.round(storage.documents_mb / 10240 * 100), 100)
})

const quickActions = [
  { label: '上传文档', icon: markRaw(UploadFilled), route: '/knowledge', bgColor: '#ecf5ff', iconColor: '#409eff' },
  { label: '开始问答', icon: markRaw(Position), route: '/qa', bgColor: '#f0f9eb', iconColor: '#67c23a' },
  { label: '查看图谱', icon: markRaw(Compass), route: '/graph', bgColor: '#fdf6ec', iconColor: '#e6a23c' },
  { label: '系统配置', icon: markRaw(Setting), route: '/config', bgColor: '#f4f4f5', iconColor: '#909399' },
]

async function loadStats() {
  try {
    const res = await getStats()
    stats.value[0].value = res.data.total_documents || 0
    stats.value[1].value = (res.data.parse_success_rate || 0) + '%'
    stats.value[2].value = res.data.total_questions || 0
    stats.value[3].value = res.data.today_questions || 0
    stats.value[4].value = res.data.active_users || 0
    stats.value[5].value = res.data.total_chunks || 0
    totalChunks.value = res.data.total_chunks || 0
    docTypeCounts.value = res.data.type_counts || {}
    renderDocTypeChart()
  } catch {}
}

async function loadTrends() {
  try {
    const res = await getTrends({ days: trendDays.value })
    const data = res.data || []
    if (!trendChart) return
    trendChart.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.95)',
        borderColor: '#e8e8e8',
        textStyle: { color: '#303133' },
      },
      grid: { left: 50, right: 20, top: 20, bottom: 30 },
      xAxis: {
        type: 'category',
        data: data.map(d => d.date),
        axisLabel: { fontSize: 11, color: '#909399' },
        axisLine: { lineStyle: { color: '#e8e8e8' } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: { fontSize: 11, color: '#909399' },
        splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } },
        axisLine: { show: false },
      },
      series: [{
        type: 'line',
        data: data.map(d => d.count),
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: { color: '#409eff', borderWidth: 2, borderColor: '#fff' },
        lineStyle: { width: 3, color: '#409eff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64,158,255,0.25)' },
            { offset: 1, color: 'rgba(64,158,255,0.02)' },
          ]),
        },
      }],
    }, true)
  } catch {}
}

function renderDocTypeChart() {
  if (!docTypeChart || !docTypeCounts.value) return
  const typeColors = { PDF: '#e74c3c', DOCX: '#3498db', TXT: '#909399', MD: '#9b59b6', XLSX: '#27ae60', XLS: '#27ae60', CSV: '#e67e22' }
  const data = Object.entries(docTypeCounts.value).map(([name, value]) => ({
    name,
    value,
    itemStyle: { color: typeColors[name] || '#909399' }
  }))
  docTypeChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e8e8e8',
      textStyle: { color: '#303133' },
    },
    legend: {
      bottom: 0,
      textStyle: { fontSize: 11, color: '#606266' },
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 12,
    },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['50%', '45%'],
      data,
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.1)' },
      },
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
    }],
  }, true)
}

async function loadSystemStatus() {
  try {
    const res = await getSystemStatus()
    Object.assign(systemStatus, res.data)
  } catch {}
}

async function loadStorage() {
  try {
    const res = await getStorage()
    storage.documents_mb = res.data.documents_mb || 0
  } catch {}
}

let resizeHandler = null

onMounted(async () => {
  await nextTick()
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
  }
  if (docTypeChartRef.value) {
    docTypeChart = echarts.init(docTypeChartRef.value)
  }
  resizeHandler = () => {
    trendChart?.resize()
    docTypeChart?.resize()
  }
  window.addEventListener('resize', resizeHandler)
  await loadStats()
  await loadTrends()
  await loadSystemStatus()
  await loadStorage()
})

onBeforeUnmount(() => {
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
  trendChart?.dispose()
  docTypeChart?.dispose()
})
</script>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 18px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border: 1px solid #f0f0f0;
  transition: all 0.2s ease;
  cursor: default;
}
.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transform: translateY(-2px);
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-label {
  font-size: 12px;
  color: #909399;
  line-height: 1;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin-top: 4px;
  line-height: 1;
}

.panel {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border: 1px solid #f0f0f0;
  overflow: hidden;
}
.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.panel-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid #f5f5f5;
  transition: background 0.15s;
}
.status-item:last-child {
  border-bottom: none;
}
.status-item:hover {
  background: #fafafa;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}
.status-dot.healthy {
  background: #67c23a;
  box-shadow: 0 0 6px rgba(103,194,58,0.4);
}
.status-dot.unhealthy {
  background: #f56c6c;
  box-shadow: 0 0 6px rgba(245,108,108,0.4);
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 12px;
  border-radius: 10px;
  background: var(--bg);
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}
.action-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.08);
  border-color: var(--color);
}
.action-label {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}
</style>
