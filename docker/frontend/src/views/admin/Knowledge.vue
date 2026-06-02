<template>
  <div>
    <!-- 页面标题区域 -->
    <div style="background:linear-gradient(135deg,#11998e 0%,#38ef7d 100%);border-radius:12px;padding:24px 28px;margin-bottom:20px">
      <h2 style="color:#fff;margin:0;font-size:22px;font-weight:600">知识库管理</h2>
      <p style="color:rgba(255,255,255,0.8);margin:6px 0 0;font-size:13px">管理文档上传、解析和知识图谱构建</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="14" style="margin-bottom:20px">
      <el-col :span="3">
        <div class="stat-card">
          <div class="stat-value" style="color:#409eff">{{ docStats.total }}</div>
          <div class="stat-label">总文件数</div>
        </div>
      </el-col>
      <el-col :span="3" v-for="ft in fileTypeList" :key="ft.key">
        <div class="stat-card">
          <div style="display:flex;align-items:center;justify-content:center;gap:6px">
            <el-icon :color="ft.color" :size="18"><component :is="ft.icon" /></el-icon>
            <span class="stat-value" :style="{color:ft.color}">{{ docStats.type_counts[ft.key] || 0 }}</span>
          </div>
          <div class="stat-label">{{ ft.label }}</div>
        </div>
      </el-col>
      <el-col :span="2">
        <div class="stat-card">
          <div class="stat-value" style="color:#67c23a">{{ docStats.status_counts['completed'] || 0 }}</div>
          <div class="stat-label">成功</div>
        </div>
      </el-col>
      <el-col :span="2">
        <div class="stat-card">
          <div class="stat-value" style="color:#e6a23c">{{ (docStats.status_counts['pending'] || 0) + (docStats.status_counts['parsing'] || 0) }}</div>
          <div class="stat-label">待解析</div>
        </div>
      </el-col>
      <el-col :span="2">
        <div class="stat-card">
          <div class="stat-value" style="color:#f56c6c">{{ docStats.status_counts['failed'] || 0 }}</div>
          <div class="stat-label">失败</div>
        </div>
      </el-col>
    </el-row>

    <!-- 文档列表 -->
    <div class="panel">
      <div class="panel-header">
        <div style="display:flex;gap:12px;align-items:center">
          <el-input v-model="keyword" placeholder="搜索文档" style="width:200px" clearable @clear="loadDocs" @keyup.enter="loadDocs" />
          <el-select v-model="filterType" placeholder="类型" clearable style="width:100px" @change="loadDocs">
            <el-option v-for="ft in fileTypeList" :key="ft.key" :label="ft.key" :value="ft.key" />
          </el-select>
          <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px" @change="loadDocs">
            <el-option label="pending" value="pending" />
            <el-option label="parsing" value="parsing" />
            <el-option label="completed" value="completed" />
            <el-option label="failed" value="failed" />
          </el-select>
        </div>
        <div style="display:flex;gap:10px">
          <el-button type="primary" @click="showUpload = true">
            <el-icon style="margin-right:4px"><UploadFilled /></el-icon>上传文档
          </el-button>
          <el-popconfirm title="确定重新解析所有文档？这将花费较长时间。" @confirm="handleReparseAll">
            <template #reference>
              <el-button type="warning" :loading="reparseAllLoading">一键重新解析</el-button>
            </template>
          </el-popconfirm>
          <el-popconfirm title="确定删除所有文档？此操作不可撤销！" @confirm="handleDeleteAll">
            <template #reference>
              <el-button type="danger" :loading="deleteAllLoading">一键删除</el-button>
            </template>
          </el-popconfirm>
          <el-popconfirm title="确定清理知识图谱中没有对应文档的孤立实体？" @confirm="handleCleanupOrphans">
            <template #reference>
              <el-button :loading="cleanupLoading">清理孤立实体</el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>

      <!-- 批量操作栏 -->
      <div v-if="selectedDocs.length > 0" class="batch-bar">
        <span style="font-size:13px;color:#409eff;font-weight:500">已选择 {{ selectedDocs.length }} 个文档</span>
        <el-button size="small" type="warning" @click="handleBatchReparse">批量重新解析</el-button>
        <el-button size="small" type="danger" @click="handleBatchDelete">批量删除</el-button>
        <el-button size="small" @click="selectedDocs = []">取消选择</el-button>
      </div>

      <el-table :data="documents" stripe v-loading="loading" @selection-change="handleSelectionChange" style="width:100%">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="filename" label="文件名" min-width="200">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:8px">
              <el-icon :color="getFileColor(row.file_type)" :size="18"><component :is="getFileIcon(row.file_type)" /></el-icon>
              <span style="font-weight:500">{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="file_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :color="getFileColor(row.file_type)" style="color:#fff;border:none" size="small" round>{{ row.file_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="100">
          <template #default="{ row }">
            <span style="font-size:12px;color:#606266">{{ formatFileSize(row.file_size) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="parse_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.parse_status === 'completed' ? 'success' : row.parse_status === 'failed' ? 'danger' : 'warning'" effect="dark" round size="small">
              {{ statusMap[row.parse_status] || row.parse_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="70" />
        <el-table-column prop="tag" label="标签" width="100" />
        <el-table-column prop="created_at" label="上传时间" width="170" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handlePreview(row)">预览</el-button>
            <el-upload :show-file-list="false" :before-upload="(f) => handleUpdate(row.id, f)" :accept="acceptTypes" style="display:inline">
              <el-button link type="primary" size="small">更新</el-button>
            </el-upload>
            <el-button link type="primary" size="small" @click="handleReparse(row)">重新解析</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <div style="padding:16px;display:flex;justify-content:flex-end">
        <el-pagination v-model:current-page="page" :page-size="size" :total="total" layout="total,prev,pager,next" @current-change="loadDocs" />
      </div>
    </div>

    <!-- 上传弹窗 -->
    <el-dialog v-model="showUpload" title="上传文档" width="550" @closed="resetUpload">
      <el-upload drag action="#" :auto-upload="false" :on-change="onFileChange" :file-list="uploadFiles" multiple :accept="acceptTypes">
        <el-icon style="font-size:48px;color:#c0c4cc;margin-bottom:12px"><UploadFilled /></el-icon>
        <div style="font-size:14px;color:#606266">拖拽文件到此处或<em style="color:#409eff;font-style:normal">点击上传</em></div>
        <div style="font-size:12px;color:#909399;margin-top:8px">支持 PDF、DOCX、TXT、MD、XLSX、CSV 格式</div>
      </el-upload>
      <el-input v-model="uploadTag" placeholder="标签（可选）" style="margin-top:16px" />
      <div v-if="uploadQueue.length" style="margin-top:16px;max-height:200px;overflow-y:auto;border:1px solid #f0f0f0;border-radius:8px;padding:8px">
        <div v-for="(item, idx) in uploadQueue" :key="idx" style="display:flex;align-items:center;gap:8px;padding:8px;border-radius:6px;transition:background 0.15s" :style="{background: idx % 2 === 0 ? '#fafafa' : '#fff'}">
          <el-icon :color="getFileColor(getFileType(item.file.name))" :size="16"><component :is="getFileIcon(getFileType(item.file.name))" /></el-icon>
          <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px">{{ item.file.name }}</span>
          <el-tag v-if="item.status==='pending'" size="small" type="info" effect="plain">待解析</el-tag>
          <el-tag v-else-if="item.status==='uploading'" size="small" type="warning" effect="plain">上传中</el-tag>
          <el-tag v-else-if="item.status==='completed'" size="small" type="success" effect="plain">已完成</el-tag>
          <el-tag v-else-if="item.status==='failed'" size="small" type="danger" effect="plain">失败</el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="showUpload = false">{{ uploading ? '关闭' : '取消' }}</el-button>
        <el-button type="primary" :loading="uploading" :disabled="uploadQueue.length===0" @click="handleUpload">
          {{ uploading ? '上传中...' : '开始上传' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览弹窗 -->
    <el-dialog v-model="showPreview" title="文档预览" width="700">
      <div v-if="previewData">
        <div style="margin-bottom:16px;display:flex;align-items:center;gap:12px">
          <el-icon :color="getFileColor(getFileType(previewData.filename))" :size="20"><component :is="getFileIcon(getFileType(previewData.filename))" /></el-icon>
          <span style="font-weight:500">{{ previewData.filename }}</span>
          <span style="color:#909399;font-size:12px">第 {{ previewData.current_page }} / {{ previewData.total_pages }} 页</span>
        </div>
        <el-input type="textarea" :model-value="previewData.content" :rows="20" readonly style="font-family:Consolas,monospace" />
        <div style="margin-top:16px;text-align:center">
          <el-button :disabled="previewPage <= 1" @click="previewPage--; loadPreview()">上一页</el-button>
          <el-button :disabled="!previewData.has_next" @click="previewPage++; loadPreview()">下一页</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, markRaw } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document, Notebook, Grid, Memo, Files } from '@element-plus/icons-vue'
import { getDocuments, getDocumentStats, uploadDocument, updateDocument, deleteDocument, reparseDocument, reparseAllDocuments, deleteAllDocuments, batchDeleteDocuments, batchReparseDocuments, cleanupOrphanEntities, previewDocument } from '../../api/documents'

const fileTypeList = [
  { key: 'PDF', label: 'PDF', color: '#e74c3c', icon: markRaw(Document) },
  { key: 'DOCX', label: 'DOCX', color: '#3498db', icon: markRaw(Document) },
  { key: 'TXT', label: 'TXT', color: '#909399', icon: markRaw(Memo) },
  { key: 'MD', label: 'MD', color: '#9b59b6', icon: markRaw(Notebook) },
  { key: 'XLSX', label: 'XLSX', color: '#27ae60', icon: markRaw(Grid) },
  { key: 'XLS', label: 'XLS', color: '#27ae60', icon: markRaw(Grid) },
  { key: 'CSV', label: 'CSV', color: '#e67e22', icon: markRaw(Files) },
]

const statusMap = {
  pending: '待解析',
  parsing: '解析中',
  completed: '已完成',
  failed: '失败',
}

const acceptTypes = '.pdf,.docx,.txt,.md,.xlsx,.xls,.csv'

function getFileIcon(type) {
  const ft = fileTypeList.find(f => f.key === type)
  return ft ? ft.icon : markRaw(Document)
}

function getFileColor(type) {
  const ft = fileTypeList.find(f => f.key === type)
  return ft ? ft.color : '#909399'
}

function getFileType(filename) {
  if (!filename) return 'TXT'
  const ext = filename.split('.').pop().toUpperCase()
  const map = { PDF: 'PDF', DOCX: 'DOCX', TXT: 'TXT', MD: 'MD', XLSX: 'XLSX', XLS: 'XLS', CSV: 'CSV' }
  return map[ext] || 'TXT'
}

function formatFileSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

const docStats = reactive({
  total: 0,
  type_counts: {},
  status_counts: {},
})

const documents = ref([])
const loading = ref(false)
const page = ref(1)
const size = 20
const total = ref(0)
const keyword = ref('')
const filterType = ref('')
const filterStatus = ref('')

const showUpload = ref(false)
const uploadFiles = ref([])
const uploadTag = ref('')
const uploading = ref(false)
const uploadQueue = ref([])

const showPreview = ref(false)
const previewData = ref(null)
const previewPage = ref(1)
const previewDocId = ref(null)
const reparseAllLoading = ref(false)
const deleteAllLoading = ref(false)
const cleanupLoading = ref(false)
const selectedDocs = ref([])

let refreshTimer = null

onMounted(() => {
  loadDocs()
  loadStats()
})

async function loadStats() {
  try {
    const res = await getDocumentStats()
    Object.assign(docStats, res.data)
  } catch {}
}

async function loadDocs() {
  loading.value = true
  try {
    const res = await getDocuments({ page: page.value, size, keyword: keyword.value, file_type: filterType.value, status: filterStatus.value })
    documents.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function onFileChange(file, fileList) {
  uploadQueue.value = fileList.map(f => ({ file: f.raw, status: 'pending' }))
}

function resetUpload() {
  uploadFiles.value = []
  uploadQueue.value = []
  uploadTag.value = ''
}

async function handleUpload() {
  if (!uploadQueue.value.length) return ElMessage.warning('请选择文件')
  uploading.value = true
  let successCount = 0
  for (const item of uploadQueue.value) {
    item.status = 'uploading'
    try {
      const fd = new FormData()
      fd.append('file', item.file)
      if (uploadTag.value) fd.append('tag', uploadTag.value)
      await uploadDocument(fd)
      item.status = 'completed'
      successCount++
    } catch {
      item.status = 'failed'
    }
  }
  uploading.value = false
  ElMessage.success(`上传完成：${successCount}/${uploadQueue.value.length} 成功，正在后台解析...`)
  loadDocs()
  loadStats()
  startAutoRefresh()
}

function startAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer)
  refreshTimer = setInterval(async () => {
    await loadDocs()
    await loadStats()
    const pendingCount = documents.value.filter(d => d.parse_status === 'pending' || d.parse_status === 'parsing').length
    if (pendingCount === 0) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }, 3000)
}

async function handleUpdate(docId, file) {
  const fd = new FormData()
  fd.append('file', file)
  try {
    await updateDocument(docId, fd)
    ElMessage.success('更新成功')
    loadDocs()
    loadStats()
  } catch {
    ElMessage.error('更新失败')
  }
  return false
}

async function handleDelete(id) {
  await deleteDocument(id)
  ElMessage.success('删除成功')
  loadDocs()
  loadStats()
}

async function handleReparse(row) {
  await reparseDocument(row.id)
  ElMessage.success('重新解析已触发')
  loadDocs()
}

async function handleReparseAll() {
  reparseAllLoading.value = true
  try {
    const res = await reparseAllDocuments()
    ElMessage.success(res.message || '重新解析已触发')
    loadDocs()
    loadStats()
    startAutoRefresh()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    reparseAllLoading.value = false
  }
}

async function handleDeleteAll() {
  deleteAllLoading.value = true
  try {
    const res = await deleteAllDocuments()
    ElMessage.success(res.message || '删除完成')
    loadDocs()
    loadStats()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    deleteAllLoading.value = false
  }
}

async function handleCleanupOrphans() {
  cleanupLoading.value = true
  try {
    const res = await cleanupOrphanEntities()
    ElMessage.success(res.message || '清理完成')
    loadDocs()
    loadStats()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    cleanupLoading.value = false
  }
}

function handleSelectionChange(selection) {
  selectedDocs.value = selection
}

async function handleBatchReparse() {
  if (selectedDocs.value.length === 0) return ElMessage.warning('请先选择文档')
  try {
    const ids = selectedDocs.value.map(d => d.id)
    const res = await batchReparseDocuments(ids)
    ElMessage.success(res.message || '重新解析已触发')
    selectedDocs.value = []
    loadDocs()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleBatchDelete() {
  if (selectedDocs.value.length === 0) return ElMessage.warning('请先选择文档')
  try {
    const ids = selectedDocs.value.map(d => d.id)
    const res = await batchDeleteDocuments(ids)
    ElMessage.success(res.message || '删除完成')
    selectedDocs.value = []
    loadDocs()
    loadStats()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handlePreview(row) {
  previewDocId.value = row.id
  previewPage.value = 1
  await loadPreview()
  showPreview.value = true
}

async function loadPreview() {
  const res = await previewDocument(previewDocId.value, { page: previewPage.value })
  previewData.value = res.data
}
</script>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 16px 12px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border: 1px solid #f0f0f0;
  transition: all 0.2s ease;
}
.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transform: translateY(-2px);
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1;
}
.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
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
  flex-wrap: wrap;
  gap: 12px;
}

.batch-bar {
  margin: 12px 16px;
  padding: 12px 16px;
  background: #ecf5ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
