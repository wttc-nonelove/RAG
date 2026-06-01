<template>
  <div>
    <h2>知识库管理</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-top:20px">
      <el-col :span="4">
        <el-card shadow="hover" body-style="padding:16px;text-align:center">
          <div style="font-size:12px;color:#909399">总文件数</div>
          <div style="font-size:28px;font-weight:bold;color:#303133;margin-top:4px">{{ docStats.total }}</div>
        </el-card>
      </el-col>
      <el-col :span="4" v-for="ft in fileTypeList" :key="ft.key">
        <el-card shadow="hover" body-style="padding:16px;text-align:center">
          <div style="font-size:12px;color:#909399">{{ ft.label }}</div>
          <div style="font-size:22px;font-weight:bold;margin-top:4px;display:flex;align-items:center;justify-content:center;gap:6px">
            <el-icon :color="ft.color" :size="20"><component :is="ft.icon" /></el-icon>
            <span :style="{color:ft.color}">{{ docStats.type_counts[ft.key] || 0 }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="2">
        <el-card shadow="hover" body-style="padding:16px;text-align:center">
          <div style="font-size:12px;color:#909399">成功</div>
          <div style="font-size:22px;font-weight:bold;color:#67c23a;margin-top:4px">{{ docStats.status_counts['completed'] || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="2">
        <el-card shadow="hover" body-style="padding:16px;text-align:center">
          <div style="font-size:12px;color:#909399">待解析</div>
          <div style="font-size:22px;font-weight:bold;color:#e6a23c;margin-top:4px">{{ (docStats.status_counts['pending'] || 0) + (docStats.status_counts['parsing'] || 0) }}</div>
        </el-card>
      </el-col>
      <el-col :span="2">
        <el-card shadow="hover" body-style="padding:16px;text-align:center">
          <div style="font-size:12px;color:#909399">失败</div>
          <div style="font-size:22px;font-weight:bold;color:#f56c6c;margin-top:4px">{{ docStats.status_counts['failed'] || 0 }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 文档列表 -->
    <el-card style="margin-top:20px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div style="display:flex;gap:12px">
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
          <div style="display:flex;gap:12px">
            <el-button type="primary" @click="showUpload = true">上传文档</el-button>
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
          </div>
        </div>
      </template>

      <!-- 批量操作栏 -->
      <div v-if="selectedDocs.length > 0" style="margin-bottom:12px;padding:10px;background:#ecf5ff;border-radius:4px;display:flex;align-items:center;gap:12px">
        <span style="font-size:13px;color:#409eff">已选择 {{ selectedDocs.length }} 个文档</span>
        <el-button size="small" type="warning" @click="handleBatchReparse">批量重新解析</el-button>
        <el-button size="small" type="danger" @click="handleBatchDelete">批量删除</el-button>
        <el-button size="small" @click="selectedDocs = []">取消选择</el-button>
      </div>

      <el-table :data="documents" stripe v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="filename" label="文件名" min-width="200">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:8px">
              <el-icon :color="getFileColor(row.file_type)" :size="18"><component :is="getFileIcon(row.file_type)" /></el-icon>
              <span>{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="file_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :color="getFileColor(row.file_type)" style="color:#fff;border:none" size="small">{{ row.file_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="100">
          <template #default="{ row }">
            <span style="font-size:12px;color:#606266">{{ formatFileSize(row.file_size) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="parse_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.parse_status === 'completed' ? 'success' : row.parse_status === 'failed' ? 'danger' : 'warning'">
              {{ row.parse_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="tag" label="标签" width="120" />
        <el-table-column prop="created_at" label="上传时间" width="180" />
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handlePreview(row)">预览</el-button>
            <el-upload :show-file-list="false" :before-upload="(f) => handleUpdate(row.id, f)" :accept="acceptTypes">
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
      <div style="margin-top:16px;display:flex;justify-content:flex-end">
        <el-pagination v-model:current-page="page" :page-size="size" :total="total" layout="total,prev,pager,next" @current-change="loadDocs" />
      </div>
    </el-card>

    <el-dialog v-model="showUpload" title="上传文档" width="550" @closed="resetUpload">
      <el-upload drag action="#" :auto-upload="false" :on-change="onFileChange" :file-list="uploadFiles" multiple :accept="acceptTypes">
        <el-icon style="font-size:40px;color:#c0c4cc"><UploadFilled /></el-icon>
        <div>拖拽文件到此处或<em>点击上传</em>（支持多选）</div>
        <template #tip>
          <div style="color:#909399;font-size:12px">支持 PDF、DOCX、TXT、MD、XLSX、CSV 格式，可同时选择多个文件</div>
        </template>
      </el-upload>
      <el-input v-model="uploadTag" placeholder="标签（可选）" style="margin-top:12px" />
      <div v-if="uploadQueue.length" style="margin-top:12px;max-height:200px;overflow-y:auto">
        <div v-for="(item, idx) in uploadQueue" :key="idx" style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #f0f0f0">
          <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px">{{ item.file.name }}</span>
          <el-tag v-if="item.status==='pending'" size="small" type="info">待解析</el-tag>
          <el-tag v-else-if="item.status==='uploading'" size="small" type="warning">上传中</el-tag>
          <el-tag v-else-if="item.status==='completed'" size="small" type="success">已完成</el-tag>
          <el-tag v-else-if="item.status==='failed'" size="small" type="danger">失败</el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="showUpload = false">{{ uploading ? '关闭' : '取消' }}</el-button>
        <el-button type="primary" :loading="uploading" :disabled="uploadQueue.length===0" @click="handleUpload">
          {{ uploading ? '上传中...' : '开始上传' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showPreview" title="文档预览" width="700">
      <div v-if="previewData">
        <div style="margin-bottom:12px;color:#909399">
          {{ previewData.filename }} | 第 {{ previewData.current_page }} / {{ previewData.total_pages }} 页
        </div>
        <el-input type="textarea" :model-value="previewData.content" :rows="20" readonly />
        <div style="margin-top:12px;text-align:center">
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
import { getDocuments, getDocumentStats, uploadDocument, updateDocument, deleteDocument, reparseDocument, reparseAllDocuments, deleteAllDocuments, batchDeleteDocuments, batchReparseDocuments, previewDocument } from '../../api/documents'

const fileTypeList = [
  { key: 'PDF', label: 'PDF', color: '#e74c3c', icon: markRaw(Document) },
  { key: 'DOCX', label: 'DOCX', color: '#3498db', icon: markRaw(Document) },
  { key: 'TXT', label: 'TXT', color: '#909399', icon: markRaw(Memo) },
  { key: 'MD', label: 'MD', color: '#9b59b6', icon: markRaw(Notebook) },
  { key: 'XLSX', label: 'XLSX', color: '#27ae60', icon: markRaw(Grid) },
  { key: 'XLS', label: 'XLS', color: '#27ae60', icon: markRaw(Grid) },
  { key: 'CSV', label: 'CSV', color: '#e67e22', icon: markRaw(Files) },
]

const acceptTypes = '.pdf,.docx,.txt,.md,.xlsx,.xls,.csv'

function getFileIcon(type) {
  const ft = fileTypeList.find(f => f.key === type)
  return ft ? ft.icon : markRaw(Document)
}

function getFileColor(type) {
  const ft = fileTypeList.find(f => f.key === type)
  return ft ? ft.color : '#909399'
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
const selectedDocs = ref([])

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
  ElMessage.success(`上传完成：${successCount}/${uploadQueue.value.length} 成功`)
  loadDocs()
  loadStats()
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
