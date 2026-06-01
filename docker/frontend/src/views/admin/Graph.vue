<template>
  <div>
    <h2>知识图谱</h2>
    <el-row :gutter="20" style="margin-top:20px">
      <!-- 左侧：图谱 -->
      <el-col :span="showRelationPanel ? 18 : 24">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <div style="display:flex;gap:12px;align-items:center">
                <el-input v-model="searchKey" placeholder="搜索实体" style="width:200px" clearable @keyup.enter="handleSearch" />
                <el-button type="primary" @click="handleSearch">搜索</el-button>
                <el-button @click="loadGraph">全部</el-button>
                <el-button type="success" @click="showEntityDialog=true">添加实体</el-button>
                <el-button type="warning" @click="openRelationDialog">添加关系</el-button>
                <el-button :type="showRelationPanel ? 'primary' : 'info'" @click="showRelationPanel = !showRelationPanel">
                  {{ showRelationPanel ? '隐藏关系' : '关系列表' }}
                </el-button>
              </div>
              <span style="color:#909399;font-size:13px">节点: {{ graphData.nodes.length }} | 关系: {{ graphData.edges.length }}</span>
            </div>
          </template>
          <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <el-tag :type="activeType === '' ? 'primary' : 'info'" size="small" style="cursor:pointer" @click="clearTypeFilter">全部</el-tag>
            <el-tag v-for="(color, type) in TYPE_COLORS" :key="type" :color="color"
              :style="{marginRight:'0',color:'#fff',fontSize:'12px',cursor:'pointer',opacity:activeType===type?1:0.6,border:activeType===type?'2px solid #303133':'none'}"
              size="small" @click="handleTypeFilter(type)">{{ type }}</el-tag>
            <span v-if="activeType" style="font-size:12px;color:#909399;margin-left:8px">
              筛选: {{ activeType }} | 节点: {{ filteredNodeCount }} | 关系: {{ filteredEdgeCount }}
            </span>
          </div>
          <div style="margin-bottom:8px;display:flex;align-items:center;gap:16px">
            <span style="font-size:12px;color:#909399">节点大小:</span>
            <el-slider v-model="nodeSizeScale" :min="0.5" :max="2" :step="0.1" style="width:120px" @change="renderChart" />
            <el-switch v-model="showEdgeLabels" active-text="关系标签" inactive-text="" @change="renderChart" />
          </div>
          <div ref="chartRef" style="width:100%;height:calc(100vh - 400px)"></div>
        </el-card>
      </el-col>

      <!-- 右侧：关系列表面板 -->
      <el-col :span="6" v-if="showRelationPanel">
        <el-card style="height:100%">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font-weight:bold">关系列表</span>
              <el-button size="small" @click="loadRelations">刷新</el-button>
            </div>
          </template>
          <div style="max-height:calc(100vh - 480px);overflow-y:auto">
            <div v-for="(rel, idx) in relations" :key="idx"
              style="padding:8px 0;border-bottom:1px solid #f0f0f0;font-size:12px;cursor:pointer"
              :style="{background: highlightedRelation === idx ? '#ecf5ff' : ''}"
              @click="highlightRelation(idx, rel)">
              <div style="display:flex;align-items:center;gap:4px">
                <el-tag size="small" :color="getEntityColorFromGraph(rel.source)" style="color:#fff;border:none;font-size:11px">{{ rel.source }}</el-tag>
                <span style="color:#909399">—[{{ rel.rel }}]→</span>
                <el-tag size="small" :color="getEntityColorFromGraph(rel.target)" style="color:#fff;border:none;font-size:11px">{{ rel.target }}</el-tag>
              </div>
              <div style="text-align:right;margin-top:4px">
                <el-popconfirm title="确定删除该关系？" @confirm="handleDeleteRelation(rel)">
                  <template #reference>
                    <el-button link type="danger" size="small" @click.stop>删除</el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
            <el-empty v-if="relations.length === 0" description="暂无关系" :image-size="60" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 添加实体对话框 -->
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

    <!-- 添加关系对话框 -->
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

    <!-- 实体详情对话框 -->
    <el-dialog v-model="showNodeDetail" title="实体详情" width="500">
      <div v-if="selectedNode">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="名称">{{ selectedNode.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :color="TYPE_COLORS[selectedNode.type] || '#909399'" style="color:#fff;border:none">{{ selectedNode.type }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述">{{ selectedNode.description || '暂无描述' }}</el-descriptions-item>
        </el-descriptions>

        <div style="margin-top:16px">
          <div style="font-weight:bold;margin-bottom:8px">关联实体 ({{ nodeNeighbors.length }})</div>
          <div style="max-height:200px;overflow-y:auto">
            <div v-for="(n, idx) in nodeNeighbors" :key="idx" style="padding:6px 0;border-bottom:1px solid #f0f0f0;font-size:12px">
              <div style="display:flex;align-items:center;gap:4px">
                <span v-if="n.direction === 'out'" style="color:#909399">→</span>
                <el-tag size="small" :color="TYPE_COLORS[n.type] || '#909399'" style="color:#fff;border:none;font-size:11px">{{ n.name }}</el-tag>
                <span v-if="n.direction === 'in'" style="color:#909399">→</span>
                <span style="color:#909399;margin-left:4px">[{{ n.rel }}]</span>
              </div>
            </div>
            <el-empty v-if="nodeNeighbors.length === 0" description="暂无关联实体" :image-size="40" />
          </div>
        </div>

        <div style="margin-top:16px;display:flex;gap:12px">
          <el-button type="primary" @click="showEditEntity = true" style="flex:1">编辑实体</el-button>
          <el-popconfirm title="确定删除该实体及其所有关系？" @confirm="handleDeleteEntity">
            <template #reference>
              <el-button type="danger" style="flex:1">删除实体</el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>
    </el-dialog>

    <!-- 编辑实体对话框 -->
    <el-dialog v-model="showEditEntity" title="编辑实体" width="400">
      <el-form :model="editEntityForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="editEntityForm.name" disabled />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="editEntityForm.type" style="width:100%">
            <el-option v-for="t in entityTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editEntityForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditEntity=false">取消</el-button>
        <el-button type="primary" @click="handleUpdateEntity">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  getGraphOverview, searchGraph, filterByType, createEntity, updateEntity,
  deleteEntity, getEntityNeighbors, getRelations, createRelation, deleteRelation
} from '../../api/graph'

const chartRef = ref(null)
const searchKey = ref('')
const activeType = ref('')
const filteredNodeCount = ref(0)
const filteredEdgeCount = ref(0)
const nodeSizeScale = ref(1)
const showEdgeLabels = ref(true)
const showRelationPanel = ref(false)
const highlightedRelation = ref(-1)
let chart = null
let resizeHandler = null

const graphData = ref({ nodes: [], edges: [] })
const relations = ref([])

const entityTypes = ['人物', '组织', '地点', '概念', '技术', '产品', '事件', '制度', '指标', '流程']
const COLORS = ['#5470c6','#91cc75','#fac858','#ee6666','#73c0de','#3ba272','#fc8452','#9a60b4','#ea7ccc','#48b8d0']
const TYPE_MAP = { '人物':0, '组织':1, '地点':2, '概念':3, '技术':4, '产品':5, '事件':6, '制度':7, '指标':8, '流程':9 }
const TYPE_COLORS = { '人物':'#5470c6','组织':'#91cc75','地点':'#fac858','概念':'#ee6666','技术':'#73c0de','产品':'#3ba272','事件':'#fc8452','制度':'#9a60b4','指标':'#ea7ccc','流程':'#48b8d0' }

const showEntityDialog = ref(false)
const entityForm = reactive({ name: '', type: '概念', description: '' })

const showRelationDialog = ref(false)
const relationForm = reactive({ source: '', relation: '', target: '' })

const showNodeDetail = ref(false)
const showEditEntity = ref(false)
const selectedNode = ref(null)
const nodeNeighbors = ref([])
const editEntityForm = reactive({ name: '', type: '概念', description: '' })

function getEntityColorFromGraph(name) {
  const node = graphData.value.nodes.find(n => n.name === name)
  return node ? (TYPE_COLORS[node.type] || '#909399') : '#909399'
}

function buildChartOption(data) {
  const scale = nodeSizeScale.value
  const nodes = data.nodes.map((n, i) => {
    const typeIdx = TYPE_MAP[n.type] ?? (i % COLORS.length)
    return {
      id: n.name, name: n.name,
      symbolSize: (30 + Math.min((n.description?.length || 0) / 3, 20)) * scale,
      itemStyle: { color: COLORS[typeIdx % COLORS.length] },
      label: { show: true, fontSize: 12 },
      category: typeIdx,
    }
  })
  const edges = data.edges.map(e => ({
    source: e.source, target: e.target,
    label: { show: showEdgeLabels.value, formatter: e.rel, fontSize: 10, color: '#666' },
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
  activeType.value = ''
  filteredNodeCount.value = 0
  filteredEdgeCount.value = 0
  try {
    const res = await getGraphOverview()
    graphData.value = res.data || { nodes: [], edges: [] }
    renderChart()
  } catch (e) { ElMessage.error('加载图谱失败') }
}

async function loadRelations() {
  try {
    const res = await getRelations(500)
    relations.value = res.data || []
  } catch (e) { ElMessage.error('加载关系列表失败') }
}

async function handleSearch() {
  if (!searchKey.value.trim()) return loadGraph()
  activeType.value = ''
  try {
    const res = await searchGraph(searchKey.value)
    graphData.value = res.data || { nodes: [], edges: [] }
    filteredNodeCount.value = graphData.value.nodes.length
    filteredEdgeCount.value = graphData.value.edges.length
    renderChart()
  } catch (e) { ElMessage.error('搜索失败') }
}

async function handleTypeFilter(type) {
  activeType.value = type
  searchKey.value = ''
  try {
    const res = await filterByType(type)
    graphData.value = res.data || { nodes: [], edges: [] }
    filteredNodeCount.value = graphData.value.nodes.length
    filteredEdgeCount.value = graphData.value.edges.length
    renderChart()
  } catch (e) { ElMessage.error('筛选失败') }
}

function clearTypeFilter() {
  activeType.value = ''
  filteredNodeCount.value = 0
  filteredEdgeCount.value = 0
  loadGraph()
}

function highlightRelation(idx, rel) {
  highlightedRelation.value = idx
  // 高亮图谱中对应的边
  if (chart) {
    chart.dispatchAction({ type: 'highlight', seriesIndex: 0, dataType: 'edge', name: `${rel.source} > ${rel.target}` })
    setTimeout(() => {
      chart.dispatchAction({ type: 'downplay', seriesIndex: 0 })
    }, 2000)
  }
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
    await createRelation({ source: relationForm.source, relation: relationForm.relation, target: relationForm.target })
    ElMessage.success('关系创建成功')
    showRelationDialog.value = false
    await loadGraph()
    if (showRelationPanel.value) await loadRelations()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '创建失败') }
}

async function handleDeleteRelation(rel) {
  try {
    await deleteRelation(rel.source, rel.rel, rel.target)
    ElMessage.success('关系删除成功')
    await loadRelations()
    await loadGraph()
  } catch (e) { ElMessage.error('删除失败') }
}

async function handleNodeClick(nodeName) {
  const node = graphData.value.nodes.find(n => n.name === nodeName)
  if (!node) return
  selectedNode.value = node
  editEntityForm.name = node.name
  editEntityForm.type = node.type || '概念'
  editEntityForm.description = node.description || ''
  showNodeDetail.value = true
  try {
    const res = await getEntityNeighbors(nodeName)
    nodeNeighbors.value = res.data || []
  } catch {
    nodeNeighbors.value = []
  }
}

async function handleUpdateEntity() {
  try {
    await updateEntity(editEntityForm.name, { name: editEntityForm.name, type: editEntityForm.type, description: editEntityForm.description })
    ElMessage.success('实体更新成功')
    showEditEntity.value = false
    selectedNode.value.type = editEntityForm.type
    selectedNode.value.description = editEntityForm.description
    await loadGraph()
  } catch (e) { ElMessage.error('更新失败') }
}

async function handleDeleteEntity() {
  if (!selectedNode.value) return
  try {
    await deleteEntity(selectedNode.value.name)
    ElMessage.success('实体删除成功')
    showNodeDetail.value = false
    selectedNode.value = null
    await loadGraph()
    if (showRelationPanel.value) await loadRelations()
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
        handleNodeClick(params.name)
      }
    })
    await loadGraph()
    await loadRelations()
  }
})

onBeforeUnmount(() => {
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
  chart?.dispose()
})
</script>
