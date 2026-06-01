<template>
  <div>
    <h2>模型管理</h2>
    <el-tabs v-model="activeTab" style="margin-top:20px" @tab-change="handleTabChange">
      <!-- 供应商管理 -->
      <el-tab-pane label="模型供应商" name="providers">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>供应商列表</span>
              <el-button type="primary" size="small" @click="openProviderDialog()">添加供应商</el-button>
            </div>
          </template>
          <el-table :data="providers" stripe>
            <el-table-column prop="provider_name" label="供应商" />
            <el-table-column prop="api_base_url" label="API 地址" />
            <el-table-column prop="is_active" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="250">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleTest(row)">测试</el-button>
                <el-button link type="primary" size="small" @click="openProviderDialog(row)">编辑</el-button>
                <el-popconfirm title="确定删除？" @confirm="handleDeleteProvider(row.id)">
                  <template #reference>
                    <el-button link type="danger" size="small">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 对话模型 -->
      <el-tab-pane label="对话模型" name="chat">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>对话模型配置</span>
              <el-button type="primary" size="small" @click="openConfigDialog('chat')">添加模型</el-button>
            </div>
          </template>
          <el-table :data="chatModels" stripe>
            <el-table-column prop="model_name" label="模型名称" />
            <el-table-column label="供应商" width="150">
              <template #default="{ row }">
                {{ getProviderName(row.provider_id) }}
              </template>
            </el-table-column>
            <el-table-column prop="is_default" label="默认" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_default" type="success">默认</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '启用' : '停用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleSetDefault(row)" :disabled="row.is_default">设为默认</el-button>
                <el-button link type="primary" size="small" @click="openConfigDialog('chat', row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- Embedding 模型 -->
      <el-tab-pane label="Embedding 模型" name="embedding">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>Embedding 模型配置</span>
              <el-button type="primary" size="small" @click="openConfigDialog('embedding')">添加模型</el-button>
            </div>
          </template>
          <el-table :data="embeddingModels" stripe>
            <el-table-column prop="model_name" label="模型名称" />
            <el-table-column label="供应商" width="150">
              <template #default="{ row }">
                {{ getProviderName(row.provider_id) }}
              </template>
            </el-table-column>
            <el-table-column prop="embedding_dimension" label="维度" width="100" />
            <el-table-column prop="is_default" label="默认" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_default" type="success">默认</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleSetDefault(row)" :disabled="row.is_default">设为默认</el-button>
                <el-button link type="primary" size="small" @click="openConfigDialog('embedding', row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- Prompt 模板 -->
      <el-tab-pane label="Prompt 模板" name="prompts">
        <el-card>
          <div v-for="m in chatModels" :key="m.id" style="margin-bottom:24px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
              <span style="font-weight:bold">{{ m.model_name }} <el-tag v-if="m.is_default" type="success" size="small">默认</el-tag></span>
              <el-button type="primary" size="small" @click="handleSavePrompt(m)">保存</el-button>
            </div>
            <el-input v-model="m._editingPrompt" type="textarea" :rows="6" placeholder="输入系统提示词模板..." />
          </div>
          <div v-if="chatModels.length===0" style="text-align:center;color:#c0c4cc;padding:40px">暂无对话模型，请先添加</div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 供应商编辑弹窗 -->
    <el-dialog v-model="showProviderDialog" :title="editingProvider ? '编辑供应商' : '添加供应商'" width="450">
      <el-form :model="providerForm" label-width="100px">
        <el-form-item label="供应商名称">
          <el-input v-model="providerForm.provider_name" placeholder="如: DeepSeek、通义千问" />
        </el-form-item>
        <el-form-item label="API 地址">
          <el-input v-model="providerForm.api_base_url" placeholder="如: https://api.deepseek.com" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="providerForm.api_key" type="password" show-password placeholder="留空则不更新" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProviderDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveProvider">确定</el-button>
      </template>
    </el-dialog>

    <!-- 模型配置弹窗 -->
    <el-dialog v-model="showConfigDialog" :title="editingConfig ? '编辑模型' : '添加模型配置'" width="480">
      <el-form :model="configForm" label-width="110px">
        <el-form-item label="供应商">
          <el-select v-model="configForm.provider_id" style="width:100%" placeholder="选择供应商">
            <el-option v-for="p in providers" :key="p.id" :label="p.provider_name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="configForm.model_name" placeholder="如: deepseek-chat、text-embedding-v1" />
        </el-form-item>
        <el-form-item label="模型类型">
          <el-select v-model="configForm.model_type" style="width:100%">
            <el-option label="对话模型 (chat)" value="chat" />
            <el-option label="Embedding 模型" value="embedding" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="configForm.model_type === 'embedding'" label="Embedding 维度">
          <el-input-number v-model="configForm.embedding_dimension" :min="64" :max="4096" :step="64" />
        </el-form-item>
        <el-form-item v-if="configForm.model_type === 'chat'" label="系统提示词">
          <el-input v-model="configForm.system_prompt" type="textarea" :rows="4" placeholder="可选，留空使用默认" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="configForm.is_default" />
        </el-form-item>
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
import {
  getProviders, createProvider, updateProvider, deleteProvider, testProvider,
  getModelConfigs, createModelConfig, setDefaultModel, savePrompt,
} from '../../api/models'
import client from '../../api/client'

const activeTab = ref('providers')
const providers = ref([])
const chatModels = ref([])
const embeddingModels = ref([])

// 供应商弹窗
const showProviderDialog = ref(false)
const editingProvider = ref(null)
const providerForm = reactive({ provider_name: '', api_base_url: '', api_key: '' })

// 模型配置弹窗
const showConfigDialog = ref(false)
const editingConfig = ref(null)
const configForm = reactive({
  provider_id: null,
  model_name: '',
  model_type: 'chat',
  system_prompt: '',
  embedding_dimension: 1536,
  is_default: false,
})

onMounted(() => loadProviders())

function getProviderName(id) {
  return providers.value.find(p => p.id === id)?.provider_name || '-'
}

async function loadProviders() {
  try {
    const res = await getProviders()
    providers.value = res.data || []
  } catch {}
}

async function loadConfigs(type) {
  try {
    const res = await getModelConfigs({ type })
    const items = res.data || []
    // 给每条记录加 _editingPrompt 用于 prompt 编辑
    items.forEach(m => { m._editingPrompt = m.system_prompt || '' })
    return items
  } catch { return [] }
}

async function handleTabChange(tab) {
  if (tab === 'providers') loadProviders()
  else if (tab === 'chat') chatModels.value = await loadConfigs('chat')
  else if (tab === 'embedding') embeddingModels.value = await loadConfigs('embedding')
  else if (tab === 'prompts') chatModels.value = await loadConfigs('chat')
}

// ---- 供应商 CRUD ----
function openProviderDialog(row) {
  if (row) {
    editingProvider.value = row
    providerForm.provider_name = row.provider_name
    providerForm.api_base_url = row.api_base_url
    providerForm.api_key = ''
  } else {
    editingProvider.value = null
    providerForm.provider_name = ''
    providerForm.api_base_url = ''
    providerForm.api_key = ''
  }
  showProviderDialog.value = true
}

async function handleSaveProvider() {
  if (!providerForm.provider_name || !providerForm.api_base_url) {
    return ElMessage.warning('请填写供应商名称和 API 地址')
  }
  try {
    if (editingProvider.value) {
      const data = { provider_name: providerForm.provider_name, api_base_url: providerForm.api_base_url }
      if (providerForm.api_key) data.api_key = providerForm.api_key
      await updateProvider(editingProvider.value.id, data)
      ElMessage.success('供应商更新成功')
    } else {
      if (!providerForm.api_key) return ElMessage.warning('请输入 API Key')
      await createProvider({ ...providerForm })
      ElMessage.success('供应商添加成功')
    }
    showProviderDialog.value = false
    loadProviders()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function handleTest(row) {
  const loading = ElMessage({ message: '正在测试连通性...', type: 'info', duration: 0 })
  try {
    const res = await testProvider(row.id)
    loading.close()
    if (res.data.status === 'ok') {
      ElMessage.success(`连通性测试通过，延迟 ${res.data.latency_ms}ms`)
    } else {
      ElMessage.error(`测试失败: ${res.data.error || '未知错误'}`)
    }
  } catch (e) {
    loading.close()
    ElMessage.error('测试失败')
  }
}

async function handleDeleteProvider(id) {
  try {
    await deleteProvider(id)
    ElMessage.success('删除成功')
    loadProviders()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

// ---- 模型配置 CRUD ----
function openConfigDialog(type, row) {
  configForm.model_type = type
  if (row) {
    editingConfig.value = row
    configForm.provider_id = row.provider_id
    configForm.model_name = row.model_name
    configForm.system_prompt = row.system_prompt || ''
    configForm.embedding_dimension = row.embedding_dimension || 1536
    configForm.is_default = !!row.is_default
  } else {
    editingConfig.value = null
    configForm.provider_id = null
    configForm.model_name = ''
    configForm.system_prompt = ''
    configForm.embedding_dimension = 1536
    configForm.is_default = false
  }
  showConfigDialog.value = true
}

async function handleSaveConfig() {
  if (!configForm.provider_id || !configForm.model_name) {
    return ElMessage.warning('请选择供应商并填写模型名称')
  }
  try {
    const data = {
      provider_id: configForm.provider_id,
      model_name: configForm.model_name,
      model_type: configForm.model_type,
      system_prompt: configForm.system_prompt || null,
      embedding_dimension: configForm.model_type === 'embedding' ? configForm.embedding_dimension : null,
    }
    if (editingConfig.value) {
      await client.put(`/models/configs/${editingConfig.value.id}`, data)
    } else {
      await createModelConfig(data)
    }
    if (configForm.is_default) {
      if (editingConfig.value) {
        await setDefaultModel(editingConfig.value.id)
      } else {
        const configs = await getModelConfigs({ type: configForm.model_type })
        const items = configs.data || []
        const created = items.find(c => c.model_name === configForm.model_name && c.provider_id === configForm.provider_id)
        if (created) await setDefaultModel(created.id)
      }
    }
    ElMessage.success('模型配置保存成功')
    showConfigDialog.value = false
    if (configForm.model_type === 'chat') chatModels.value = await loadConfigs('chat')
    else embeddingModels.value = await loadConfigs('embedding')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

async function handleSetDefault(row) {
  try {
    await setDefaultModel(row.id)
    ElMessage.success('默认模型已设置')
    if (row.model_type === 'chat') chatModels.value = await loadConfigs('chat')
    else embeddingModels.value = await loadConfigs('embedding')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '设置失败')
  }
}

// ---- Prompt 保存 ----
async function handleSavePrompt(model) {
  try {
    await savePrompt(model.id, { system_prompt: model._editingPrompt })
    ElMessage.success('Prompt 模板已保存')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}
</script>
