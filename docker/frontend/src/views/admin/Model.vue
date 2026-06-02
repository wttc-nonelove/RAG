<template>
  <div>
    <div class="clay-hero" style="background:linear-gradient(135deg,#fa709a,#fee140)">
      <h2 class="clay-hero-title">模型管理</h2>
      <p class="clay-hero-subtitle">管理 AI 模型供应商、配置和 Token 用量</p>
    </div>

    <el-tabs v-model="activeTab" style="margin-top:20px" @tab-change="handleTabChange">
      <!-- 用量查询 -->
      <el-tab-pane label="用量查询" name="usage">
        <el-row :gutter="16" style="margin-bottom:20px">
          <el-col :span="6">
            <div class="clay-card" style="text-align:center">
              <div class="clay-stat-label">总消耗 Tokens</div>
              <div class="clay-stat-value" style="color:#667eea">{{ usageStats.total_tokens.toLocaleString() }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="clay-card" style="text-align:center">
              <div class="clay-stat-label">对话消耗</div>
              <div class="clay-stat-value" style="color:#10b981">{{ usageStats.chat_tokens.toLocaleString() }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="clay-card" style="text-align:center">
              <div class="clay-stat-label">Embedding 消耗</div>
              <div class="clay-stat-value" style="color:#f59e0b">{{ usageStats.embedding_tokens.toLocaleString() }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="clay-card" style="text-align:center">
              <div class="clay-stat-label">总问答次数</div>
              <div class="clay-stat-value" style="color:#8b5cf6">{{ usageStats.qa_count.toLocaleString() }}</div>
            </div>
          </el-col>
        </el-row>
        <div class="clay-panel">
          <div class="clay-panel-header"><span class="clay-panel-title">各模型用量明细</span></div>
          <el-table :data="usageStats.by_model" stripe style="width:100%">
            <el-table-column prop="model_name" label="模型名称" min-width="150">
              <template #default="{ row }"><span style="font-weight:500">{{ row.model_name }}</span></template>
            </el-table-column>
            <el-table-column label="类型" width="100">
              <template #default="{ row }"><el-tag :type="row.model_type==='chat'?'primary':'success'" effect="dark" round size="small">{{ row.model_type==='chat'?'对话':'Embedding' }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="total_tokens" label="消耗 Tokens" width="150">
              <template #default="{ row }"><span style="font-weight:700;color:#667eea">{{ row.total_tokens.toLocaleString() }}</span></template>
            </el-table-column>
            <el-table-column prop="count" label="调用次数" width="120" />
            <el-table-column label="平均消耗" width="150">
              <template #default="{ row }">{{ row.count > 0 ? Math.round(row.total_tokens / row.count).toLocaleString() : 0 }}</template>
            </el-table-column>
            <el-table-column label="占比" width="150">
              <template #default="{ row }"><el-progress :percentage="usageStats.total_tokens > 0 ? Math.round(row.total_tokens / usageStats.total_tokens * 100) : 0" :stroke-width="10" /></template>
            </el-table-column>
          </el-table>
          <div v-if="usageStats.by_model.length === 0" class="clay-empty"><div class="clay-empty-icon" style="background:#ecf0ff"><el-icon :size="32" color="#667eea"><DataAnalysis /></el-icon></div><div class="clay-empty-desc">暂无用量数据</div></div>
        </div>
      </el-tab-pane>

      <!-- 供应商管理 -->
      <el-tab-pane label="模型供应商" name="providers">
        <div class="clay-panel">
          <div class="clay-panel-header">
            <span class="clay-panel-title">供应商列表</span>
            <el-button type="primary" class="clay-btn" size="small" @click="openProviderDialog()" style="background:linear-gradient(135deg,#fa709a,#fee140);border:none">添加供应商</el-button>
          </div>
          <el-table :data="providers" stripe style="width:100%">
            <el-table-column prop="provider_name" label="供应商" min-width="120">
              <template #default="{ row }"><span style="font-weight:600">{{ row.provider_name }}</span></template>
            </el-table-column>
            <el-table-column prop="api_base_url" label="API 地址" min-width="250">
              <template #default="{ row }"><span style="font-family:monospace;font-size:12px;color:#606266">{{ row.api_base_url }}</span></template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="100">
              <template #default="{ row }"><el-tag :type="row.is_active?'success':'info'" effect="dark" round size="small">{{ row.is_active?'启用':'停用' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleTest(row)">测试</el-button>
                <el-button link type="primary" size="small" @click="openProviderDialog(row)">编辑</el-button>
                <el-popconfirm title="确定删除？" @confirm="handleDeleteProvider(row.id)">
                  <template #reference><el-button link type="danger" size="small">删除</el-button></template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 对话模型 -->
      <el-tab-pane label="对话模型" name="chat">
        <div class="clay-panel">
          <div class="clay-panel-header">
            <span class="clay-panel-title">对话模型配置</span>
            <el-button type="primary" class="clay-btn" size="small" @click="openConfigDialog('chat')" style="background:linear-gradient(135deg,#fa709a,#fee140);border:none">添加模型</el-button>
          </div>
          <el-table :data="chatModels" stripe style="width:100%">
            <el-table-column prop="model_name" label="模型名称" min-width="150">
              <template #default="{ row }"><span style="font-weight:500">{{ row.model_name }}</span></template>
            </el-table-column>
            <el-table-column label="供应商" width="150">
              <template #default="{ row }">{{ getProviderName(row.provider_id) }}</template>
            </el-table-column>
            <el-table-column prop="is_default" label="默认" width="80">
              <template #default="{ row }"><el-tag v-if="row.is_default" type="success" effect="dark" round size="small">默认</el-tag></template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }"><el-tag :type="row.is_active?'success':'info'" effect="dark" round size="small">{{ row.is_active?'启用':'停用' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleSetDefault(row)" :disabled="row.is_default">设为默认</el-button>
                <el-button link type="primary" size="small" @click="openConfigDialog('chat', row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- Embedding 模型 -->
      <el-tab-pane label="Embedding 模型" name="embedding">
        <div class="clay-panel">
          <div class="clay-panel-header">
            <span class="clay-panel-title">Embedding 模型配置</span>
            <el-button type="primary" class="clay-btn" size="small" @click="openConfigDialog('embedding')" style="background:linear-gradient(135deg,#fa709a,#fee140);border:none">添加模型</el-button>
          </div>
          <el-table :data="embeddingModels" stripe style="width:100%">
            <el-table-column prop="model_name" label="模型名称" min-width="150">
              <template #default="{ row }"><span style="font-weight:500">{{ row.model_name }}</span></template>
            </el-table-column>
            <el-table-column label="供应商" width="150">
              <template #default="{ row }">{{ getProviderName(row.provider_id) }}</template>
            </el-table-column>
            <el-table-column prop="embedding_dimension" label="维度" width="100" />
            <el-table-column prop="is_default" label="默认" width="80">
              <template #default="{ row }"><el-tag v-if="row.is_default" type="success" effect="dark" round size="small">默认</el-tag></template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleSetDefault(row)" :disabled="row.is_default">设为默认</el-button>
                <el-button link type="primary" size="small" @click="openConfigDialog('embedding', row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- Prompt 模板 -->
      <el-tab-pane label="Prompt 模板" name="prompts">
        <div class="clay-panel">
          <div class="clay-panel-header"><span class="clay-panel-title">System Prompt 模板管理</span></div>
          <div style="padding:20px">
            <div v-for="m in chatModels" :key="m.id" style="margin-bottom:24px">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                <span style="font-weight:600;font-size:15px">{{ m.model_name }} <el-tag v-if="m.is_default" type="success" effect="dark" round size="small">默认</el-tag></span>
                <el-button type="primary" class="clay-btn" size="small" @click="handleSavePrompt(m)" style="background:linear-gradient(135deg,#fa709a,#fee140);border:none">保存</el-button>
              </div>
              <el-input v-model="m._editingPrompt" type="textarea" :rows="6" placeholder="输入系统提示词模板..." />
            </div>
            <div v-if="chatModels.length===0" class="clay-empty"><div class="clay-empty-icon" style="background:#fffbeb"><el-icon :size="32" color="#f59e0b"><Document /></el-icon></div><div class="clay-empty-desc">暂无对话模型，请先添加</div></div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 供应商编辑弹窗 -->
    <el-dialog v-model="showProviderDialog" :title="editingProvider ? '编辑供应商' : '添加供应商'" width="450" class="clay-dialog">
      <el-form :model="providerForm" label-width="100px">
        <el-form-item label="供应商名称"><el-input v-model="providerForm.provider_name" placeholder="如: DeepSeek、通义千问" /></el-form-item>
        <el-form-item label="API 地址"><el-input v-model="providerForm.api_base_url" placeholder="如: https://api.deepseek.com" /></el-form-item>
        <el-form-item label="API Key"><el-input v-model="providerForm.api_key" type="password" show-password placeholder="留空则不更新" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProviderDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveProvider">确定</el-button>
      </template>
    </el-dialog>

    <!-- 模型配置弹窗 -->
    <el-dialog v-model="showConfigDialog" :title="editingConfig ? '编辑模型' : '添加模型配置'" width="480" class="clay-dialog">
      <el-form :model="configForm" label-width="110px">
        <el-form-item label="供应商">
          <el-select v-model="configForm.provider_id" style="width:100%" placeholder="选择供应商">
            <el-option v-for="p in providers" :key="p.id" :label="p.provider_name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称"><el-input v-model="configForm.model_name" placeholder="如: deepseek-chat、text-embedding-v1" /></el-form-item>
        <el-form-item label="模型类型">
          <el-select v-model="configForm.model_type" style="width:100%">
            <el-option label="对话模型 (chat)" value="chat" />
            <el-option label="Embedding 模型" value="embedding" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="configForm.model_type==='embedding'" label="Embedding 维度"><el-input-number v-model="configForm.embedding_dimension" :min="64" :max="4096" :step="64" /></el-form-item>
        <el-form-item v-if="configForm.model_type==='chat'" label="系统提示词"><el-input v-model="configForm.system_prompt" type="textarea" :rows="4" placeholder="可选，留空使用默认" /></el-form-item>
        <el-form-item label="设为默认"><el-switch v-model="configForm.is_default" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveConfig">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Document } from '@element-plus/icons-vue'
import { getProviders, createProvider, updateProvider, deleteProvider, testProvider, getModelConfigs, createModelConfig, setDefaultModel, savePrompt } from '../../api/models'
import client from '../../api/client'

const activeTab = ref('usage')
const providers = ref([])
const chatModels = ref([])
const embeddingModels = ref([])

const usageStats = reactive({ total_tokens: 0, chat_tokens: 0, embedding_tokens: 0, qa_count: 0, by_model: [] })

const showProviderDialog = ref(false)
const editingProvider = ref(null)
const providerForm = reactive({ provider_name: '', api_base_url: '', api_key: '' })

const showConfigDialog = ref(false)
const editingConfig = ref(null)
const configForm = reactive({ provider_id: null, model_name: '', model_type: 'chat', system_prompt: '', embedding_dimension: 1536, is_default: false })

onMounted(() => { loadUsage() })

function getProviderName(id) { return providers.value.find(p => p.id === id)?.provider_name || '-' }

async function loadProviders() { try { const res = await getProviders(); providers.value = res.data || [] } catch {} }
async function loadConfigs(type) { try { const res = await getModelConfigs({ type }); const items = res.data || []; items.forEach(m => { m._editingPrompt = m.system_prompt || '' }); return items } catch { return [] } }
async function loadUsage() { try { const res = await client.get('/models/usage'); const data = res.data || {}; usageStats.total_tokens = data.total_tokens || 0; usageStats.chat_tokens = data.chat_tokens || 0; usageStats.embedding_tokens = data.embedding_tokens || 0; usageStats.qa_count = data.qa_count || 0; usageStats.by_model = data.by_model || [] } catch {} }

async function handleTabChange(tab) {
  if (tab === 'usage') await loadUsage()
  else if (tab === 'providers') loadProviders()
  else if (tab === 'chat') chatModels.value = await loadConfigs('chat')
  else if (tab === 'embedding') embeddingModels.value = await loadConfigs('embedding')
  else if (tab === 'prompts') chatModels.value = await loadConfigs('chat')
}

function openProviderDialog(row) {
  if (row) { editingProvider.value = row; providerForm.provider_name = row.provider_name; providerForm.api_base_url = row.api_base_url; providerForm.api_key = '' }
  else { editingProvider.value = null; providerForm.provider_name = ''; providerForm.api_base_url = ''; providerForm.api_key = '' }
  showProviderDialog.value = true
}

async function handleSaveProvider() {
  if (!providerForm.provider_name || !providerForm.api_base_url) return ElMessage.warning('请填写供应商名称和 API 地址')
  try {
    if (editingProvider.value) { const data = { provider_name: providerForm.provider_name, api_base_url: providerForm.api_base_url }; if (providerForm.api_key) data.api_key = providerForm.api_key; await updateProvider(editingProvider.value.id, data); ElMessage.success('供应商更新成功') }
    else { if (!providerForm.api_key) return ElMessage.warning('请输入 API Key'); await createProvider({ ...providerForm }); ElMessage.success('供应商添加成功') }
    showProviderDialog.value = false; loadProviders()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
}

async function handleTest(row) {
  const loading = ElMessage({ message: '正在测试连通性...', type: 'info', duration: 0 })
  try { const res = await testProvider(row.id); loading.close(); if (res.data.status === 'ok') ElMessage.success(`连通性测试通过，延迟 ${res.data.latency_ms}ms`); else ElMessage.error(`测试失败: ${res.data.error || '未知错误'}`) } catch { loading.close(); ElMessage.error('测试失败') }
}

async function handleDeleteProvider(id) { try { await deleteProvider(id); ElMessage.success('删除成功'); loadProviders() } catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') } }

function openConfigDialog(type, row) {
  configForm.model_type = type
  if (row) { editingConfig.value = row; configForm.provider_id = row.provider_id; configForm.model_name = row.model_name; configForm.system_prompt = row.system_prompt || ''; configForm.embedding_dimension = row.embedding_dimension || 1536; configForm.is_default = !!row.is_default }
  else { editingConfig.value = null; configForm.provider_id = null; configForm.model_name = ''; configForm.system_prompt = ''; configForm.embedding_dimension = 1536; configForm.is_default = false }
  showConfigDialog.value = true
}

async function handleSaveConfig() {
  if (!configForm.provider_id || !configForm.model_name) return ElMessage.warning('请选择供应商并填写模型名称')
  try {
    const data = { provider_id: configForm.provider_id, model_name: configForm.model_name, model_type: configForm.model_type, system_prompt: configForm.system_prompt || null, embedding_dimension: configForm.model_type === 'embedding' ? configForm.embedding_dimension : null }
    if (editingConfig.value) { await client.put(`/models/configs/${editingConfig.value.id}`, data) } else { await createModelConfig(data) }
    if (configForm.is_default) { if (editingConfig.value) { await setDefaultModel(editingConfig.value.id) } else { const configs = await getModelConfigs({ type: configForm.model_type }); const items = configs.data || []; const created = items.find(c => c.model_name === configForm.model_name && c.provider_id === configForm.provider_id); if (created) await setDefaultModel(created.id) } }
    ElMessage.success('模型配置保存成功'); showConfigDialog.value = false
    if (configForm.model_type === 'chat') chatModels.value = await loadConfigs('chat'); else embeddingModels.value = await loadConfigs('embedding')
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
}

async function handleSetDefault(row) { try { await setDefaultModel(row.id); ElMessage.success('默认模型已设置'); if (row.model_type === 'chat') chatModels.value = await loadConfigs('chat'); else embeddingModels.value = await loadConfigs('embedding') } catch (e) { ElMessage.error(e.response?.data?.detail || '设置失败') } }

async function handleSavePrompt(model) { try { await savePrompt(model.id, { system_prompt: model._editingPrompt }); ElMessage.success('Prompt 模板已保存') } catch { ElMessage.error('保存失败') } }
</script>
