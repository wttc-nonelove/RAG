<template>
  <div>
    <h2>工作台</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="6" v-for="item in stats" :key="item.label">
        <el-card shadow="hover">
          <div style="display:flex;align-items:center;gap:12px">
            <div :style="getIconStyle(item.bgColor)">
              <el-icon :size="24" :color="item.iconColor"><component :is="item.icon" /></el-icon>
            </div>
            <div>
              <div style="font-size:13px;color:#909399">{{ item.label }}</div>
              <div style="font-size:28px;font-weight:bold;margin-top:4px;color:#303133">{{ item.value }}</div>
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

    <!-- 存储信息 + 快捷操作 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span style="font-weight:bold">存储信息</span>
          </template>
          <div style="text-align:center;padding:10px 0">
            <div style="font-size:13px;color:#909399;margin-bottom:8px">文档存储</div>
            <div style="font-size:32px;font-weight:bold;color:#409eff">{{ storage.documents_mb }} <span style="font-size:14px;color:#909399">MB</span></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <span style="font-weight:bold">快捷操作</span>
          </template>
          <div style="display:flex;gap:16px;flex-wrap:wrap">
            <div v-for="action in quickActions" :key="action.label"
              :style="getActionStyle(action.bgColor)"
              @click="$router.push(action.route)"
              @mouseenter="$event.currentTarget.style.transform='translateY(-2px)'"
              @mouseleave="$event.currentTarget.style.transform='translateY(0)'">
              <el-icon :size="28" :color="action.iconColor" style="display:block;margin:0 auto 8px"><component :is="action.icon" /></el-icon>
              <div style="font-size:13px;color:#303133">{{ action.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, markRaw } from 'vue'
import * as echarts from 'echarts'
import { Document, ChatDotRound, User, Share, UploadFilled, Position, Compass, Setting } from '@element-plus/icons-vue'
import { getStats, getTrends, getStorage, getSystemStatus } from '../../api/dashboard'

const stats = ref([
  { label: '文档总数', value: 0, icon: markRaw(Document), bgColor: '#ecf5ff', iconColor: '#409eff' },
  { label: '问答次数', value: 0, icon: markRaw(ChatDotRound), bgColor: '#f0f9eb', iconColor: '#67c23a' },
  { label: '用户数量', value: 0, icon: markRaw(User), bgColor: '#fdf6ec', iconColor: '#e6a23c' },
  { label: '向量片段', value: 0, icon: markRaw(Share), bgColor: '#fef0f0', iconColor: '#f56c6c' },
])

const trendDays = ref(7)
const trendChartRef = ref(null)
let trendChart = null

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

const quickActions = [
  { label: '上传文档', icon: markRaw(UploadFilled), route: '/knowledge', bgColor: '#ecf5ff', iconColor: '#409eff' },
  { label: '开始问答', icon: markRaw(Position), route: '/qa', bgColor: '#f0f9eb', iconColor: '#67c23a' },
  { label: '查看图谱', icon: markRaw(Compass), route: '/graph', bgColor: '#fdf6ec', iconColor: '#e6a23c' },
  { label: '系统配置', icon: markRaw(Setting), route: '/config', bgColor: '#f4f4f5', iconColor: '#909399' },
]

function getIconStyle(bgColor) {
  return { width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: bgColor }
}

function getActionStyle(bgColor) {
  return { flex: 1, minWidth: '120px', textAlign: 'center', padding: '16px 12px', borderRadius: '8px', cursor: 'pointer', transition: 'all 0.2s', background: bgColor }
}

async function loadStats() {
  try {
    const res = await getStats()
    stats.value[0].value = res.data.total_documents || 0
    stats.value[1].value = res.data.total_questions || 0
    stats.value[2].value = res.data.total_users || 0
    stats.value[3].value = res.data.total_chunks || 0
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
    resizeHandler = () => trendChart?.resize()
    window.addEventListener('resize', resizeHandler)
    await loadTrends()
  }
  await loadSystemStatus()
  await loadStorage()
})

onBeforeUnmount(() => {
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
  trendChart?.dispose()
})
</script>
