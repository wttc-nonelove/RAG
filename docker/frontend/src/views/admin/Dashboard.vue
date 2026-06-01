<template>
  <div>
    <h2>工作台</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-top:20px">
      <el-col :span="4" v-for="item in stats" :key="item.label">
        <el-card shadow="hover">
          <div style="display:flex;align-items:center;gap:12px">
            <div :style="getIconStyle(item.bgColor)">
              <el-icon :size="22" :color="item.iconColor"><component :is="item.icon" /></el-icon>
            </div>
            <div>
              <div style="font-size:12px;color:#909399">{{ item.label }}</div>
              <div style="font-size:24px;font-weight:bold;margin-top:2px;color:#303133">{{ item.value }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 问答趋势图 + 系统状态 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font-weight:bold">问答趋势</span>
              <el-radio-group v-model="trendDays" size="small" @change="loadTrends">
                <el-radio-button :value="7">近7天</el-radio-button>
                <el-radio-button :value="30">近30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChartRef" style="width:100%;height:280px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" style="height:100%">
          <template #header>
            <span style="font-weight:bold">系统状态</span>
          </template>
          <div v-for="(status, name) in systemStatus" :key="name" style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #f0f0f0">
            <div style="display:flex;align-items:center;gap:8px">
              <span :style="{width:'8px',height:'8px',borderRadius:'50%',background:status==='ok'?'#67c23a':'#f56c6c',display:'inline-block'}"></span>
              <span style="font-size:14px">{{ serviceNames[name] || name }}</span>
            </div>
            <el-tag :type="status==='ok'?'success':'danger'" size="small">{{ status==='ok'?'正常':'异常' }}</el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 文档分布 + 存储用量 + 快捷操作 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span style="font-weight:bold">文档分布</span>
          </template>
          <div ref="docTypeChartRef" style="width:100%;height:200px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span style="font-weight:bold">存储用量</span>
          </template>
          <div style="padding:10px 0">
            <div style="font-size:14px;margin-bottom:12px">文件存储：<b>{{ storage.documents_mb }} MB</b></div>
            <el-progress :percentage="storagePercent" :stroke-width="12" :format="(p) => p + '%'" />
            <div style="font-size:12px;color:#909399;margin-top:8px">向量库规模：约 {{ totalChunks }} 条向量</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span style="font-weight:bold">快捷操作</span>
          </template>
          <div style="display:flex;gap:12px;flex-wrap:wrap">
            <div v-for="action in quickActions" :key="action.label"
              :style="getActionStyle(action.bgColor)"
              @click="$router.push(action.route)"
              @mouseenter="$event.currentTarget.style.transform='translateY(-2px)'"
              @mouseleave="$event.currentTarget.style.transform='translateY(0)'">
              <el-icon :size="24" :color="action.iconColor" style="display:block;margin:0 auto 6px"><component :is="action.icon" /></el-icon>
              <div style="font-size:12px;color:#303133">{{ action.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, markRaw } from 'vue'
import * as echarts from 'echarts'
import { Document, ChatDotRound, User, Share, SuccessFilled, Timer, UploadFilled, Position, Compass, Setting } from '@element-plus/icons-vue'
import { getStats, getTrends, getStorage, getSystemStatus } from '../../api/dashboard'

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

const storage = reactive({
  documents_mb: 0,
})

const totalChunks = ref(0)
const docTypeCounts = ref({})

const storagePercent = computed(() => {
  return Math.min(Math.round(storage.documents_mb / 10240 * 100), 100) // 假设总容量10GB
})

const quickActions = [
  { label: '上传文档', icon: markRaw(UploadFilled), route: '/knowledge', bgColor: '#ecf5ff', iconColor: '#409eff' },
  { label: '开始问答', icon: markRaw(Position), route: '/qa', bgColor: '#f0f9eb', iconColor: '#67c23a' },
  { label: '查看图谱', icon: markRaw(Compass), route: '/graph', bgColor: '#fdf6ec', iconColor: '#e6a23c' },
  { label: '系统配置', icon: markRaw(Setting), route: '/config', bgColor: '#f4f4f5', iconColor: '#909399' },
]

function getIconStyle(bgColor) {
  return { width: '42px', height: '42px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: bgColor }
}

function getActionStyle(bgColor) {
  return { flex: '1 1 calc(50% - 6px)', textAlign: 'center', padding: '12px 8px', borderRadius: '8px', cursor: 'pointer', transition: 'all 0.2s', background: bgColor }
}

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
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 20, bottom: 30 },
      xAxis: {
        type: 'category',
        data: data.map(d => d.date),
        axisLabel: { fontSize: 11, color: '#909399' },
        axisLine: { lineStyle: { color: '#e8e8e8' } },
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: { fontSize: 11, color: '#909399' },
        splitLine: { lineStyle: { color: '#f0f0f0' } },
      },
      series: [{
        type: 'line',
        data: data.map(d => d.count),
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#409eff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64,158,255,0.3)' },
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
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '45%'],
      data,
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
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
  await loadStats()
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
