<template>
  <div>
    <h2>知识库管理</h2>
    <el-card style="margin-top:20px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div style="display:flex;gap:12px">
            <el-input v-model="keyword" placeholder="搜索文档" style="width:200px" clearable @clear="loadDocs" @keyup.enter="loadDocs" />
            <el-select v-model="filterType" placeholder="类型" clearable style="width:100px" @change="loadDocs">
              <el-option label="PDF" value="PDF" />
              <el-option label="DOCX" value="DOCX" />
              <el-option label="TXT" value="TXT" />
            </el-select>
            <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px" @change="loadDocs">
              <el-option label="pending" value="pending" />
              <el-option label="parsing" value="parsing" />
              <el-option label="completed" value="completed" />
              <el-option label="failed" value="failed" />
            </el-select>
          </div>
          <el-button type="primary" @click="showUpload = true">上传文档</el-button>
        </div>
      </template>
      <el-table :data="documents" stripe v-loading="loading">
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column prop="file_type" label="类型" width="80" />
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
            <el-upload :show-file-list="false" :before-upload="(f) => handleUpdate(row.id, f)" accept=".pdf,.docx,.txt">
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
      <el-upload drag action="#" :auto-upload="false" :on-change="onFileChange" :file-list="uploadFiles" multiple accept=".pdf,.docx,.txt">
        <el-icon style="font-size:40px;color:#c0c4cc"><UploadFilled /></el-icon>
        <div>拖拽文件到此处或<em>点击上传</em>（支持多选）</div>
        <template #tip>
          <div style="color:#909399;font-size:12px">支持 PDF、DOCX、TXT 格式，可同时选择多个文件</div>
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { getDocuments, uploadDocument, updateDocument, deleteDocument, reparseDocument, previewDocument } from '../../api/documents'

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

onMounted(() => loadDocs())

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
}

async function handleUpdate(docId, file) {
  const fd = new FormData()
  fd.append('file', file)
  try {
    await updateDocument(docId, fd)
    ElMessage.success('更新成功')
    loadDocs()
  } catch {
    ElMessage.error('更新失败')
  }
  return false
}

async function handleDelete(id) {
  await deleteDocument(id)
  ElMessage.success('删除成功')
  loadDocs()
}

async function handleReparse(row) {
  await reparseDocument(row.id)
  ElMessage.success('重新解析已触发')
  loadDocs()
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
