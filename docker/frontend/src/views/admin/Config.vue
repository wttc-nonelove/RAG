<template>
  <div>
    <h2>系统配置</h2>
    <el-card style="margin-top:20px">
      <el-form label-width="160px">
        <el-form-item label="Temperature">
          <el-slider v-model="config.temperature" :min="0" :max="2" :step="0.1" show-input />
        </el-form-item>
        <el-form-item label="Top-P">
          <el-slider v-model="config.top_p" :min="0" :max="1" :step="0.05" show-input />
        </el-form-item>
        <el-form-item label="Max Tokens">
          <el-input-number v-model="config.max_tokens" :min="256" :max="8192" :step="256" />
        </el-form-item>
        <el-form-item label="Top-K">
          <el-input-number v-model="config.top_k" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="相似度阈值">
          <el-slider v-model="config.similarity_threshold" :min="0" :max="1" :step="0.05" show-input />
        </el-form-item>
        <el-form-item label="分块大小">
          <el-input-number v-model="config.chunk_size" :min="128" :max="2048" :step="64" />
        </el-form-item>
        <el-form-item label="分块重叠">
          <el-input-number v-model="config.chunk_overlap" :min="0" :max="512" :step="32" />
        </el-form-item>
        <el-form-item label="启用知识图谱">
          <el-switch v-model="config.kg_enabled" />
        </el-form-item>
        <el-form-item label="历史轮数">
          <el-input-number v-model="config.history_rounds" :min="0" :max="20" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import client from '../../api/client'

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
})

onMounted(async () => {
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
  } catch {}
})

async function handleSave() {
  try {
    await client.put('/config', {
      temperature: String(config.temperature),
      top_p: String(config.top_p),
      max_tokens: String(config.max_tokens),
      top_k: String(config.top_k),
      similarity_threshold: String(config.similarity_threshold),
      chunk_size: String(config.chunk_size),
      chunk_overlap: String(config.chunk_overlap),
      kg_enabled: String(config.kg_enabled),
      history_rounds: String(config.history_rounds),
    })
    ElMessage.success('配置保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}
</script>
