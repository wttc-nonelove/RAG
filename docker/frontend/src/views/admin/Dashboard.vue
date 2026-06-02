<template>
  <div>
    <!-- 页面标题区域 -->
    <div class="hero-banner">
      <div class="hero-content">
        <h2 class="hero-title">欢迎回来，{{ username }}！</h2>
        <p class="hero-subtitle">系统运行正常，今天又是充满知识的一天</p>
      </div>
      <div class="hero-decoration">
        <div class="deco-circle deco-1"></div>
        <div class="deco-circle deco-2"></div>
        <div class="deco-circle deco-3"></div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-top:24px">
      <el-col :span="4" v-for="item in stats" :key="item.label">
        <div class="clay-card" :style="{'--accent': item.color, '--bg': item.bgColor}">
          <div class="clay-icon" :style="{background: item.bgColor, borderColor: item.color}">
            <el-icon :size="24" :color="item.color"><component :is="item.icon" /></el-icon>
          </div>
          <div class="clay-info">
            <div class="clay-label">{{ item.label }}</div>
            <div class="clay-value" :style="{color: item.color}">{{ item.value }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 问答趋势图 + 系统状态 -->
    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="16">
        <div class="clay-panel">
          <div class="clay-panel-header">
            <span class="clay-panel-title">问答趋势</span>
            <el-radio-group v-model="trendDays" size="small" @change="loadTrends">
              <el-radio-button :value="7">近7天</el-radio-button>
              <el-radio-button :value="30">近30天</el-radio-button>
            </el-radio-group>
          </div>
          <div ref="trendChartRef" style="width:100%;height:280px"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="clay-panel" style="height:100%">
          <div class="clay-panel-header">
            <span class="clay-panel-title">系统状态</span>
            <div class="status-badge" :class="allHealthy ? 'healthy' : 'unhealthy'">
              {{ allHealthy ? '全部正常' : '有异常' }}
            </div>
          </div>
          <div class="status-list">
            <div v-for="(status, name) in systemStatus" :key="name" class="status-item">
              <div style="display:flex;align-items:center;gap:10px">
                <div class="status-dot" :class="status === 'ok' ? 'healthy' : 'unhealthy'"></div>
                <span style="font-size:14px;font-weight:500">{{ serviceNames[name] || name }}</span>
              </div>
              <el-tag :type="status === 'ok' ? 'success' : 'danger'" effect="dark" round size="small">
                {{ status === 'ok' ? '正常' : '异常' }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 文档分布 + 存储用量 + 快捷操作 -->
    <el-row :gutter="20" style="margin-top:24px">
      <el-col :span="8">
        <div class="clay-panel">
          <div class="clay-panel-header">
            <span class="clay-panel-title">文档分布</span>
          </div>
          <div ref="docTypeChartRef" style="width:100%;height:220px"></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="clay-panel">
          <div class="clay-panel-header">
            <span class="clay-panel-title">存储用量</span>
          </div>
          <div style="padding:24px 20px;text-align:center">
            <div class="storage-ring">
              <svg viewBox="0 0 120 120" style="width:120px;height:120px">
                <circle cx="60" cy="60" r="50" fill="none" stroke="#f0f0f0" stroke-width="10" />
                <circle cx="60" cy="60" r="50" fill="none" stroke="url(#storageGrad)" stroke-width="10"
                  stroke-linecap="round" :stroke-dasharray="314" :stroke-dashoffset="314 - (314 * storagePercent / 100)"
                  transform="rotate(-90 60 60)" />
                <defs>
                  <linearGradient id="storageGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="#667eea" />
                    <stop offset="100%" stop-color="#764ba2" />
                  </linearGradient>
                </defs>
              </svg>
              <div class="storage-text">
                <div class="storage-value">{{ storage.documents_mb }}</div>
                <div class="storage-unit">MB</div>
              </div>
            </div>
            <div style="margin-top:16px;font-size:13px;color:#909399">向量库：约 {{ totalChunks.toLocaleString() }} 条向量</div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="clay-panel">
          <div class="clay-panel-header">
            <span class="clay-panel-title">快捷操作</span>
          </div>
          <div class="action-grid">
            <div v-for="action in quickActions" :key="action.label"
              class="action-item"
              :style="{'--action-bg': action.bgColor, '--action-color': action.iconColor}"
              @click="$router.push(action.route)">
              <div class="action-icon">
                <el-icon :size="28" :color="action.iconColor"><component :is="action.icon" /></el-icon>
              </div>
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
  { label: '文档总数', value: 0, icon: markRaw(Document), color: '#667eea', bgColor: '#ecf0ff' },
  { label: '解析成功率', value: '0%', icon: markRaw(SuccessFilled), color: '#10b981', bgColor: '#ecfdf5' },
  { label: '问答总次数', value: 0, icon: markRaw(ChatDotRound), color: '#f59e0b', bgColor: '#fffbeb' },
  { label: '今日问答', value: 0, icon: markRaw(Timer), color: '#ef4444', bgColor: '#fef2f2' },
  { label: '活跃用户', value: 0, icon: markRaw(User), color: '#8b5cf6', bgColor: '#f5f3ff' },
  { label: '向量片段', value: 0, icon: markRaw(Share), color: '#06b6d4', bgColor: '#ecfeff' },
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

const storage = reactive({ documents_mb: 0 })
const totalChunks = ref(0)
const docTypeCounts = ref({})
const storagePercent = computed(() => Math.min(Math.round(storage.documents_mb / 10240 * 100), 100))

const quickActions = [
  { label: '上传文档', icon: markRaw(UploadFilled), route: '/knowledge', bgColor: '#ecf0ff', iconColor: '#667eea' },
  { label: '开始问答', icon: markRaw(Position), route: '/qa', bgColor: '#ecfdf5', iconColor: '#10b981' },
  { label: '查看图谱', icon: markRaw(Compass), route: '/graph', bgColor: '#fffbeb', iconColor: '#f59e0b' },
  { label: '系统配置', icon: markRaw(Setting), route: '/config', bgColor: '#f5f3ff', iconColor: '#8b5cf6' },
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
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#e8e8e8', textStyle: { color: '#303133' } },
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
        itemStyle: { color: '#667eea', borderWidth: 3, borderColor: '#fff' },
        lineStyle: { width: 3, color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#667eea' },
          { offset: 1, color: '#764ba2' },
        ]) },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(102,126,234,0.2)' },
            { offset: 1, color: 'rgba(102,126,234,0.01)' },
          ]),
        },
      }],
    }, true)
  } catch {}
}

function renderDocTypeChart() {
  if (!docTypeChart || !docTypeCounts.value) return
  const typeColors = { PDF: '#ef4444', DOCX: '#3b82f6', TXT: '#9ca3af', MD: '#a855f7', XLSX: '#22c55e', XLS: '#22c55e', CSV: '#f97316' }
  const data = Object.entries(docTypeCounts.value).map(([name, value]) => ({
    name, value, itemStyle: { color: typeColors[name] || '#9ca3af' }
  }))
  docTypeChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)', backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#e8e8e8', textStyle: { color: '#303133' } },
    legend: { bottom: 0, textStyle: { fontSize: 11, color: '#606266' }, itemWidth: 10, itemHeight: 10, itemGap: 12 },
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['50%', '45%'], data,
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' }, itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.1)' } },
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
    }],
  }, true)
}

async function loadSystemStatus() { try { const res = await getSystemStatus(); Object.assign(systemStatus, res.data) } catch {} }
async function loadStorage() { try { const res = await getStorage(); storage.documents_mb = res.data.documents_mb || 0 } catch {} }

let resizeHandler = null
onMounted(async () => {
  await nextTick()
  if (trendChartRef.value) trendChart = echarts.init(trendChartRef.value)
  if (docTypeChartRef.value) docTypeChart = echarts.init(docTypeChartRef.value)
  resizeHandler = () => { trendChart?.resize(); docTypeChart?.resize() }
  window.addEventListener('resize', resizeHandler)
  await loadStats()
  await loadTrends()
  await loadSystemStatus()
  await loadStorage()
})
onBeforeUnmount(() => { if (resizeHandler) window.removeEventListener('resize', resizeHandler); trendChart?.dispose(); docTypeChart?.dispose() })
</script>

<style scoped>
/* 英雄横幅 */
.hero-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  border-radius: 20px;
  padding: 32px 36px;
  position: relative;
  overflow: hidden;
}
.hero-content { position: relative; z-index: 1; }
.hero-title { color: #fff; margin: 0; font-size: 26px; font-weight: 700; }
.hero-subtitle { color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 14px; }
.hero-decoration { position: absolute; top: 0; right: 0; bottom: 0; width: 300px; }
.deco-circle { position: absolute; border-radius: 50%; opacity: 0.15; }
.deco-1 { width: 200px; height: 200px; background: #fff; top: -40px; right: -20px; animation: float 6s ease-in-out infinite; }
.deco-2 { width: 120px; height: 120px; background: #f0f9eb; bottom: -30px; right: 60px; animation: float 8s ease-in-out infinite reverse; }
.deco-3 { width: 80px; height: 80px; background: #fff; top: 20px; right: 140px; animation: float 5s ease-in-out infinite; }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-12px); } }

/* 黏土卡片 */
.clay-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  border: 3px solid #f0f0f0;
  box-shadow: 0 4px 0 #f0f0f0, 0 6px 20px rgba(0,0,0,0.04);
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: default;
}
.clay-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 0 #f0f0f0, 0 12px 30px rgba(0,0,0,0.08);
  border-color: var(--accent);
}
.clay-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2px solid;
  box-shadow: 0 3px 0 rgba(0,0,0,0.06);
}
.clay-info { flex: 1; }
.clay-label { font-size: 12px; color: #909399; font-weight: 500; }
.clay-value { font-size: 26px; font-weight: 800; margin-top: 2px; line-height: 1; }

/* 黏土面板 */
.clay-panel {
  background: #fff;
  border-radius: 16px;
  border: 3px solid #f0f0f0;
  box-shadow: 0 4px 0 #f0f0f0, 0 6px 20px rgba(0,0,0,0.04);
  overflow: hidden;
}
.clay-panel-header {
  padding: 18px 22px;
  border-bottom: 2px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.clay-panel-title { font-weight: 700; font-size: 16px; color: #1a1a2e; }

/* 状态 */
.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}
.status-badge.healthy { background: #ecfdf5; color: #10b981; }
.status-badge.unhealthy { background: #fef2f2; color: #ef4444; }
.status-list { padding: 4px 0; }
.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 22px;
  transition: background 0.15s;
}
.status-item:hover { background: #fafafa; }
.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-dot.healthy { background: #10b981; box-shadow: 0 0 8px rgba(16,185,129,0.4); }
.status-dot.unhealthy { background: #ef4444; box-shadow: 0 0 8px rgba(239,68,68,0.4); }

/* 存储环形图 */
.storage-ring { position: relative; display: inline-block; }
.storage-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.storage-value { font-size: 28px; font-weight: 800; color: #1a1a2e; line-height: 1; }
.storage-unit { font-size: 12px; color: #909399; margin-top: 2px; }

/* 快捷操作 */
.action-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  padding: 18px;
}
.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 12px;
  border-radius: 14px;
  background: var(--action-bg);
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.action-item:hover {
  transform: translateY(-4px) scale(1.02);
  border-color: var(--action-color);
  box-shadow: 0 6px 0 var(--action-bg), 0 10px 20px rgba(0,0,0,0.06);
}
.action-icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 3px 0 rgba(0,0,0,0.06);
}
.action-label { font-size: 13px; font-weight: 600; color: #1a1a2e; }
</style>
