<template>
  <div>
    <h2>系统配置</h2>

    <!-- 模型参数配置 -->
    <el-card style="margin-top:20px">
      <template #header>
        <span style="font-weight:bold">模型参数配置</span>
      </template>
      <el-form label-width="160px">
        <el-form-item label="Temperature">
          <el-slider v-model="config.temperature" :min="0" :max="2" :step="0.1" show-input style="width:300px" />
        </el-form-item>
        <el-form-item label="Top-P">
          <el-slider v-model="config.top_p" :min="0" :max="1" :step="0.05" show-input style="width:300px" />
        </el-form-item>
        <el-form-item label="Max Tokens">
          <el-input-number v-model="config.max_tokens" :min="256" :max="8192" :step="256" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave('model')">保存模型配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 检索参数配置 -->
    <el-card style="margin-top:20px">
      <template #header>
        <span style="font-weight:bold">检索参数配置</span>
      </template>
      <el-form label-width="160px">
        <el-form-item label="Top-K">
          <el-input-number v-model="config.top_k" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="相似度阈值">
          <el-slider v-model="config.similarity_threshold" :min="0" :max="1" :step="0.05" show-input style="width:300px" />
        </el-form-item>
        <el-form-item label="历史轮数">
          <el-input-number v-model="config.history_rounds" :min="0" :max="20" />
        </el-form-item>
        <el-form-item label="启用知识图谱">
          <el-switch v-model="config.kg_enabled" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave('retrieval')">保存检索配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 分块策略配置 -->
    <el-card style="margin-top:20px">
      <template #header>
        <span style="font-weight:bold">分块策略配置</span>
      </template>
      <el-form label-width="160px">
        <el-form-item label="Chunk 大小（字符数）">
          <el-input-number v-model="config.chunk_size" :min="128" :max="2048" :step="64" />
        </el-form-item>
        <el-form-item label="重叠长度（字符数）">
          <el-input-number v-model="config.chunk_overlap" :min="0" :max="512" :step="32" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave('chunk')">保存分块配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 知识图谱提取配置 -->
    <el-card style="margin-top:20px">
      <template #header>
        <span style="font-weight:bold">知识图谱提取配置</span>
      </template>
      <el-form label-width="160px">
        <el-form-item label="提取分段大小">
          <el-input-number v-model="config.kg_chunk_size" :min="1000" :max="10000" :step="500" />
          <span style="margin-left:12px;font-size:12px;color:#909399">字符数（越大提取越全面，但越慢）</span>
        </el-form-item>
        <el-form-item label="分段重叠长度">
          <el-input-number v-model="config.kg_overlap" :min="0" :max="2000" :step="100" />
          <span style="margin-left:12px;font-size:12px;color:#909399">字符数（重叠可减少边界遗漏）</span>
        </el-form-item>
        <el-form-item label="最小提取阈值">
          <el-input-number v-model="config.kg_min_chars" :min="50" :max="1000" :step="50" />
          <span style="margin-left:12px;font-size:12px;color:#909399">字符数（低于此长度的文本不提取）</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave('kg')">保存提取配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 系统信息 -->
    <el-card style="margin-top:20px">
      <template #header>
        <span style="font-weight:bold">系统信息</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="系统版本">v1.0.0</el-descriptions-item>
        <el-descriptions-item label="Python">3.11</el-descriptions-item>
        <el-descriptions-item label="FastAPI">0.115.x</el-descriptions-item>
        <el-descriptions-item label="ChromaDB">
          <el-tag :type="systemStatus.chromadb === 'ok' ? 'success' : 'danger'" size="small">
            {{ systemStatus.chromadb === 'ok' ? '连接正常' : '连接异常' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Neo4j">
          <el-tag :type="systemStatus.neo4j === 'ok' ? 'success' : 'danger'" size="small">
            {{ systemStatus.neo4j === 'ok' ? '连接正常' : '连接异常' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="MySQL">
          <el-tag :type="systemStatus.mysql === 'ok' ? 'success' : 'danger'" size="small">
            {{ systemStatus.mysql === 'ok' ? '连接正常' : '连接异常' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Redis">
          <el-tag :type="systemStatus.redis === 'ok' ? 'success' : 'danger'" size="small">
            {{ systemStatus.redis === 'ok' ? '连接正常' : '连接异常' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="文件存储">本地磁盘 — 已用 {{ storage.documents_mb }} MB</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 模型信息 -->
    <el-card style="margin-top:20px">
      <template #header>
        <span style="font-weight:bold">模型信息</span>
      </template>
      <el-table :data="models" stripe>
        <el-table-column prop="model_name" label="模型名称" min-width="150" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.model_type === 'chat' ? 'primary' : 'success'" size="small">
              {{ row.model_type === 'chat' ? '对话' : '向量' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="供应商" width="120">
          <template #default="{ row }">
            {{ row.provider_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="默认" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="warning" size="small">默认</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '已启用' : '已停用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import client from '../../api/client'
import { getSystemStatus, getStorage } from '../../api/dashboard'
import { getModelConfigs } from '../../api/models'

const route = useRoute()
const models = ref([])

const config = reactive({
  temperature: 0.7,
  top_p: 0.9,
  max_tokens: 2048,
  top_k: 5,
  similarity_threshold: 0.6,
  chunk_size: 512,
  chunk_overlap: 128,
  kg_enabled: true,
  history_rounds: 5,
  kg_chunk_size: 3000,
  kg_overlap: 500,
  kg_min_chars: 200,
})

const systemStatus = reactive({
  mysql: 'ok',
  redis: 'ok',
  neo4j: 'ok',
  chromadb: 'ok',
})

const storage = reactive({
  documents_mb: 0,
})

async function loadConfig() {
  try {
    const res = await client.get('/config')
    const data = res.data || {}
    if (data.temperature != null) config.temperature = parseFloat(data.temperature)
    if (data.top_p != null) config.top_p = parseFloat(data.top_p)
    if (data.max_tokens != null) config.max_tokens = parseInt(data.max_tokens)
    if (data.top_k != null) config.top_k = parseInt(data.top_k)
    if (data.similarity_threshold != null) config.similarity_threshold = parseFloat(data.similarity_threshold)
    if (data.chunk_size != null) config.chunk_size = parseInt(data.chunk_size)
    if (data.chunk_overlap != null) config.chunk_overlap = parseInt(data.chunk_overlap)
    if (data.kg_enabled != null) config.kg_enabled = data.kg_enabled === 'true'
    if (data.history_rounds != null) config.history_rounds = parseInt(data.history_rounds)
    if (data.kg_chunk_size != null) config.kg_chunk_size = parseInt(data.kg_chunk_size)
    if (data.kg_overlap != null) config.kg_overlap = parseInt(data.kg_overlap)
    if (data.kg_min_chars != null) config.kg_min_chars = parseInt(data.kg_min_chars)
  } catch {}
  try {
    const statusRes = await getSystemStatus()
    Object.assign(systemStatus, statusRes.data)
  } catch {}
  try {
    const storageRes = await getStorage()
    storage.documents_mb = storageRes.data.documents_mb || 0
  } catch {}
  // 加载模型信息
  try {
    const modelRes = await getModelConfigs()
    models.value = modelRes.data || []
  } catch {}
}

onMounted(loadConfig)

watch(() => route.path, (newPath) => {
  if (newPath === '/config') {
    loadConfig()
  }
})

// 按分类保存配置
const saveMap = {
  model: ['temperature', 'top_p', 'max_tokens'],
  retrieval: ['top_k', 'similarity_threshold', 'history_rounds', 'kg_enabled'],
  chunk: ['chunk_size', 'chunk_overlap'],
  kg: ['kg_chunk_size', 'kg_overlap', 'kg_min_chars'],
}

async function handleSave(section) {
  const keys = saveMap[section] || Object.keys(config)
  const payload = {}
  keys.forEach(key => {
    payload[key] = String(config[key])
  })
  try {
    await client.put('/config', payload)
    ElMessage.success('配置保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}
</script>
