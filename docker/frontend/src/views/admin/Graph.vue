<template>
  <div>
    <h2>知识图谱</h2>
    <el-card style="margin-top:20px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div style="display:flex;gap:12px;align-items:center">
            <el-input v-model="searchKey" placeholder="搜索实体" style="width:200px" clearable @keyup.enter="handleSearch" />
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="loadGraph">全部</el-button>
            <el-button type="success" @click="showEntityDialog=true">添加实体</el-button>
            <el-button type="warning" @click="openRelationDialog">添加关系</el-button>
          </div>
          <span style="color:#909399;font-size:13px">节点: {{ graphData.nodes.length }} | 关系: {{ graphData.edges.length }}</span>
        </div>
      </template>
      <div style="margin-bottom:8px">
        <el-tag v-for="(color, type) in TYPE_COLORS" :key="type" :color="color" style="margin-right:8px;color:#fff;font-size:12px" size="small">{{ type }}</el-tag>
      </div>
      <div ref="chartRef" style="width:100%;height:calc(100vh - 310px)"></div>
    </el-card>

    <el-dialog v-model="showEntityDialog" title="添加实体" width="400">
      <el-form :model="entityForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="entityForm.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="entityForm.type" style="width:100%">
            <el-option v-for="t in entityTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="entityForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEntityDialog=false">取消</el-button>
        <el-button type="primary" @click="handleCreateEntity">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showRelationDialog" title="添加关系" width="450">
      <el-form :model="relationForm" label-width="80px">
        <el-form-item label="源实体">
          <el-select v-model="relationForm.source" filterable placeholder="选择源实体" style="width:100%">
            <el-option v-for="n in graphData.nodes" :key="n.name" :label="n.name" :value="n.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="关系">
          <el-input v-model="relationForm.relation" placeholder="如: 属于、包含、依赖" />
        </el-form-item>
        <el-form-item label="目标实体">
          <el-select v-model="relationForm.target" filterable placeholder="选择目标实体" style="width:100%">
            <el-option v-for="n in graphData.nodes" :key="n.name" :label="n.name" :value="n.name" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRelationDialog=false">取消</el-button>
        <el-button type="primary" @click="handleCreateRelation">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showNodeAction" title="实体操作" width="350">
      <p>实体: <strong>{{ selectedNode }}</strong></p>
      <el-popconfirm title="确定删除该实体及其所有关系？" @confirm="handleDeleteEntity">
        <template #reference>
          <el-button type="danger" style="width:100%">删除实体</el-button>
        </template>
      </el-popconfirm>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { getGraphOverview, searchGraph, createEntity, deleteEntity } from '../../api/graph'
import client from '../../api/client'

const chartRef = ref(null)
const searchKey = ref('')
let chart = null
let resizeHandler = null

const graphData = ref({ nodes: [], edges: [] })

const entityTypes = ['人物', '组织', '地点', '概念', '技术', '产品', '事件']
const COLORS = ['#5470c6','#91cc75','#fac858','#ee6666','#73c0de','#3ba272','#fc8452','#9a60b4','#ea7ccc','#48b8d0']
const TYPE_MAP = { '人物':0, '组织':1, '地点':2, '概念':3, '技术':4, '产品':5, '事件':6 }
const TYPE_COLORS = { '人物':'#5470c6','组织':'#91cc75','地点':'#fac858','概念':'#ee6666','技术':'#73c0de','产品':'#3ba272','事件':'#fc8452' }

const showEntityDialog = ref(false)
const entityForm = reactive({ name: '', type: '概念', description: '' })

const showRelationDialog = ref(false)
const relationForm = reactive({ source: '', relation: '', target: '' })

const showNodeAction = ref(false)
const selectedNode = ref('')

function buildChartOption(data) {
  const nodes = data.nodes.map((n, i) => {
    const typeIdx = TYPE_MAP[n.type] ?? (i % COLORS.length)
    return {
      id: n.name, name: n.name,
      symbolSize: 30 + Math.min((n.description?.length || 0) / 3, 20),
      itemStyle: { color: COLORS[typeIdx % COLORS.length] },
      label: { show: true, fontSize: 12 },
      category: typeIdx,
    }
  })
  const edges = data.edges.map(e => ({
    source: e.source, target: e.target,
    label: { show: true, formatter: e.rel, fontSize: 10, color: '#666' },
  }))
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => p.dataType === 'node' ? p.name : `${p.data.source} —[${p.data.label?.formatter||''}]→ ${p.data.target}`
    },
    series: [{
      type: 'graph', layout: 'force', roam: true, draggable: true,
      force: { repulsion: 300, gravity: 0.1, edgeLength: [80, 200] },
      data: nodes, links: edges,
      lineStyle: { color: '#aaa', curveness: 0.1 },
      emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
    }]
  }
}

async function loadGraph() {
  searchKey.value = ''
  try {
    const res = await getGraphOverview()
    graphData.value = res.data || { nodes: [], edges: [] }
    renderChart()
  } catch (e) { ElMessage.error('加载图谱失败') }
}

async function handleSearch() {
  if (!searchKey.value.trim()) return loadGraph()
  try {
    const res = await searchGraph(searchKey.value)
    graphData.value = res.data || { nodes: [], edges: [] }
    renderChart()
  } catch (e) { ElMessage.error('搜索失败') }
}

function renderChart() {
  if (!chart) return
  chart.setOption(buildChartOption(graphData.value), true)
}

async function handleCreateEntity() {
  if (!entityForm.name.trim()) return ElMessage.warning('请输入实体名称')
  try {
    await createEntity({ name: entityForm.name, type: entityForm.type, description: entityForm.description })
    ElMessage.success('实体创建成功')
    showEntityDialog.value = false
    entityForm.name = ''; entityForm.type = '概念'; entityForm.description = ''
    await loadGraph()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '创建失败') }
}

function openRelationDialog() {
  if (graphData.value.nodes.length < 2) return ElMessage.warning('至少需要2个实体才能创建关系')
  relationForm.source = ''; relationForm.relation = ''; relationForm.target = ''
  showRelationDialog.value = true
}

async function handleCreateRelation() {
  if (!relationForm.source || !relationForm.relation || !relationForm.target) return ElMessage.warning('请填写完整')
  if (relationForm.source === relationForm.target) return ElMessage.warning('源实体和目标实体不能相同')
  try {
    await client.post('/graph/relations', { source: relationForm.source, relation: relationForm.relation, target: relationForm.target })
    ElMessage.success('关系创建成功')
    showRelationDialog.value = false
    await loadGraph()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '创建失败') }
}

async function handleDeleteEntity() {
  try {
    await deleteEntity(selectedNode.value)
    ElMessage.success('实体删除成功')
    showNodeAction.value = false
    await loadGraph()
  } catch (e) { ElMessage.error('删除失败') }
}

onMounted(async () => {
  await nextTick()
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    resizeHandler = () => chart?.resize()
    window.addEventListener('resize', resizeHandler)
    chart.on('click', (params) => {
      if (params.dataType === 'node') {
        selectedNode.value = params.name
        showNodeAction.value = true
      }
    })
    await loadGraph()
  }
})

onBeforeUnmount(() => {
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
  chart?.dispose()
})
</script>
