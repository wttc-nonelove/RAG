<template>
  <div>
    <div class="clay-hero" style="background:linear-gradient(135deg,#667eea,#764ba2)">
      <h2 class="clay-hero-title">系统配置</h2>
      <p class="clay-hero-subtitle">调整模型参数、检索策略和系统设置</p>
    </div>

    <el-row :gutter="20" style="margin-top:20px">
      <!-- 左侧配置 -->
      <el-col :span="16">
        <!-- 模型参数配置 -->
        <div class="clay-panel" style="margin-bottom:20px">
          <div class="clay-panel-header"><span class="clay-panel-title">模型参数配置</span></div>
          <div style="padding:24px">
            <el-form label-width="140px">
              <el-form-item label="Embedding 模式">
                <el-radio-group v-model="config.embedding_mode">
                  <el-radio value="local">本地 Embedding</el-radio>
                  <el-radio value="remote">远程 Embedding</el-radio>
                </el-radio-group>
                <div style="margin-top:8px">
                  <el-tag v-if="config.embedding_mode === 'local'" type="info" effect="plain" size="small">使用本地哈希算法生成向量，无需API密钥</el-tag>
                  <el-tag v-else type="warning" effect="plain" size="small">使用远程API（如通义千问），需要配置模型供应商</el-tag>
                </div>
              </el-form-item>
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
                <el-button type="primary" class="clay-btn" @click="handleSave('model')" style="background:linear-gradient(135deg,#667eea,#764ba2);border:none">保存模型配置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- 检索参数配置 -->
        <div class="clay-panel" style="margin-bottom:20px">
          <div class="clay-panel-header"><span class="clay-panel-title">检索参数配置</span></div>
          <div style="padding:24px">
            <el-form label-width="140px">
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
                <el-button type="primary" class="clay-btn" @click="handleSave('retrieval')" style="background:linear-gradient(135deg,#667eea,#764ba2);border:none">保存检索配置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- 分块策略配置 -->
        <div class="clay-panel" style="margin-bottom:20px">
          <div class="clay-panel-header"><span class="clay-panel-title">分块策略配置</span></div>
          <div style="padding:24px">
            <el-form label-width="140px">
              <el-form-item label="Chunk 大小（字符数）">
                <el-input-number v-model="config.chunk_size" :min="128" :max="2048" :step="64" />
              </el-form-item>
              <el-form-item label="重叠长度（字符数）">
                <el-input-number v-model="config.chunk_overlap" :min="0" :max="512" :step="32" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" class="clay-btn" @click="handleSave('chunk')" style="background:linear-gradient(135deg,#667eea,#764ba2);border:none">保存分块配置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>

        <!-- 知识图谱提取配置 -->
        <div class="clay-panel" style="margin-bottom:20px">
          <div class="clay-panel-header"><span class="clay-panel-title">知识图谱提取配置</span></div>
          <div style="padding:24px">
            <el-form label-width="140px">
              <el-form-item label="提取分段大小">
                <el-input-number v-model="config.kg_chunk_size" :min="1000" :max="10000" :step="500" />
                <span style="margin-left:12px;font-size:12px;color:#909399">字符数（越大越全面，但越慢）</span>
              </el-form-item>
              <el-form-item label="分段重叠长度">
                <el-input-number v-model="config.kg_overlap" :min="0" :max="2000" :step="100" />
                <span style="margin-left:12px;font-size:12px;color:#909399">字符数（减少边界遗漏）</span>
              </el-form-item>
              <el-form-item label="最小提取阈值">
                <el-input-number v-model="config.kg_min_chars" :min="50" :max="1000" :step="50" />
                <span style="margin-left:12px;font-size:12px;color:#909399">字符数（低于此长度不提取）</span>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" class="clay-btn" @click="handleSave('kg')" style="background:linear-gradient(135deg,#667eea,#764ba2);border:none">保存提取配置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </el-col>

      <!-- 右侧信息 -->
      <el-col :span="8">
        <!-- 系统状态 -->
        <div class="clay-panel" style="margin-bottom:20px">
          <div class="clay-panel-header"><span class="clay-panel-title">系统状态</span></div>
          <div class="status-list">
            <div v-for="(status, name) in systemStatus" :key="name" class="status-item">
              <div style="display:flex;align-items:center;gap:10px">
                <div class="status-dot" :class="status === 'ok' ? 'healthy' : 'unhealthy'"></div>
                <span style="font-size:14px;font-weight:500">{{ serviceNames[name] || name }}</span>
              </div>
              <el-tag :type="status === 'ok' ? 'success' : 'danger'" effect="dark" round size="small">{{ status === 'ok' ? '正常' : '异常' }}</el-tag>
            </div>
          </div>
        </div>

        <!-- 存储信息 -->
        <div class="clay-panel" style="margin-bottom:20px">
          <div class="clay-panel-header"><span class="clay-panel-title">存储信息</span></div>
          <div style="padding:20px;text-align:center">
            <div style="font-size:36px;font-weight:800;color:#667eea">{{ storage.documents_mb }}</div>
            <div style="font-size:13px;color:#909399;margin-top:4px">MB 已使用</div>
          </div>
        </div>

        <!-- 模型信息 -->
        <div class="clay-panel">
          <div class="clay-panel-header"><span class="clay-panel-title">模型信息</span></div>
          <div style="max-height:300px;overflow-y:auto">
            <div v-for="m in models" :key="m.id" class="model-item">
              <div style="display:flex;align-items:center;gap:8px">
                <div style="font-weight:600;font-size:13px">{{ m.model_name }}</div>
                <el-tag v-if="m.is_default" type="success" effect="dark" round size="small">默认</el-tag>
              </div>
              <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
                <el-tag :type="m.model_type==='chat'?'primary':'success'" effect="plain" round size="small">{{ m.model_type==='chat'?'对话':'向量' }}</el-tag>
                <el-tag :type="m.is_active?'success':'danger'" effect="plain" round size="small">{{ m.is_active?'启用':'停用' }}</el-tag>
              </div>
            </div>
            <div v-if="models.length === 0" style="text-align:center;color:#c0c4cc;padding:20px;font-size:13px">暂无模型</div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import client from '../../api/client'
import { getSystemStatus, getStorage } from '../../api/dashboard'
import { getModelConfigs } from '../../api/models'

const route = useRoute()
const models = ref([])

const config = reactive({
  embedding_mode: 'local',
  temperature: 0.7, top_p: 0.9, max_tokens: 2048, top_k: 5, similarity_threshold: 0.6,
  chunk_size: 512, chunk_overlap: 128, kg_enabled: true, history_rounds: 5,
  kg_chunk_size: 3000, kg_overlap: 500, kg_min_chars: 200,
})

const systemStatus = reactive({ mysql: 'ok', redis: 'ok', neo4j: 'ok', chromadb: 'ok' })
const serviceNames = { mysql: 'MySQL', redis: 'Redis', neo4j: 'Neo4j', chromadb: 'ChromaDB' }
const storage = reactive({ documents_mb: 0 })

async function loadConfig() {
  try {
    const res = await client.get('/config')
    const data = res.data || {}
    if (data.embedding_mode != null) config.embedding_mode = data.embedding_mode
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
  try { const res = await getSystemStatus(); Object.assign(systemStatus, res.data) } catch {}
  try { const res = await getStorage(); storage.documents_mb = res.data.documents_mb || 0 } catch {}
  try { const res = await getModelConfigs(); models.value = res.data || [] } catch {}
}

onMounted(loadConfig)
watch(() => route.path, (newPath) => { if (newPath === '/config') loadConfig() })

const saveMap = {
  model: ['embedding_mode', 'temperature', 'top_p', 'max_tokens'],
  retrieval: ['top_k', 'similarity_threshold', 'history_rounds', 'kg_enabled'],
  chunk: ['chunk_size', 'chunk_overlap'],
  kg: ['kg_chunk_size', 'kg_overlap', 'kg_min_chars'],
}

async function handleSave(section) {
  const keys = saveMap[section] || Object.keys(config)
  const payload = {}
  keys.forEach(key => { payload[key] = String(config[key]) })
  try { await client.put('/config', payload); ElMessage.success('配置保存成功') } catch { ElMessage.error('保存失败') }
}
</script>

<style scoped>
.status-list { padding: 4px 0; }
.status-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 22px; transition: background 0.15s;
}
.status-item:hover { background: #fafafa; }
.status-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}
.status-dot.healthy { background: #10b981; box-shadow: 0 0 8px rgba(16,185,129,0.4); }
.status-dot.unhealthy { background: #ef4444; box-shadow: 0 0 8px rgba(239,68,68,0.4); }

.model-item {
  padding: 12px 22px;
  border-bottom: 1px solid #f5f5f5;
  transition: background 0.15s;
}
.model-item:hover { background: #fafafa; }
.model-item:last-child { border-bottom: none; }
</style>
