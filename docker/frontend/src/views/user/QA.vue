<template>
  <el-container style="height:calc(100vh - 140px)">
    <el-aside width="280px" class="conv-sidebar">
      <div class="conv-header">
        <el-button type="primary" class="clay-btn" style="width:100%;background:linear-gradient(135deg,#667eea,#764ba2);border:none" @click="handleNew">
          <el-icon style="margin-right:4px"><Plus /></el-icon>新建对话
        </el-button>
      </div>
      <div class="conv-list">
        <div v-for="conv in qa.conversations" :key="conv.id"
          class="conv-item" :class="{ active: qa.currentConv?.id === conv.id }"
          @click="qa.selectConversation(conv)">
          <div class="conv-item-content">
            <el-icon :size="16" style="color:#909399;flex-shrink:0"><ChatDotRound /></el-icon>
            <span class="conv-title">{{ conv.title }}</span>
          </div>
          <el-icon class="conv-delete" @click.stop="qa.removeConversation(conv.id)"><Delete /></el-icon>
        </div>
        <div v-if="qa.conversations.length === 0" class="clay-empty" style="padding:40px 20px">
          <div class="clay-empty-icon" style="background:#ecf0ff">
            <el-icon :size="32" color="#667eea"><ChatDotRound /></el-icon>
          </div>
          <div class="clay-empty-desc">暂无对话</div>
        </div>
      </div>
    </el-aside>

    <el-container>
      <el-main style="display:flex;flex-direction:column;padding:0">
        <div ref="chatArea" class="chat-area">
          <div v-for="msg in qa.messages" :key="msg.id" :class="['message', msg.role]">
            <div class="message-avatar bot-avatar" v-if="msg.role === 'bot'">
              <el-icon :size="20" color="#fff"><ChatDotRound /></el-icon>
            </div>
            <div class="bubble" :class="msg.role">
              <div v-html="renderMarkdown(msg.content)"></div>
              <div v-if="msg.sources && msg.sources.length" class="sources-section">
                <div class="sources-title">引用来源</div>
                <div class="sources-tags">
                  <el-tag v-for="(s, i) in msg.sources" :key="i" size="small" effect="plain" round>
                    {{ s.doc_name }} {{ s.page ? `p.${s.page}` : '' }}
                  </el-tag>
                </div>
              </div>
              <div v-if="msg.kg_references && (msg.kg_references.entities?.length || msg.kg_references.edges?.length)" class="kg-section">
                <div class="kg-title">知识图谱引用</div>
                <div v-if="msg.kg_references.entities?.length" class="kg-entities">
                  <span class="kg-label">实体：</span>
                  <el-popover v-for="entity in msg.kg_references.entities" :key="entity.name" trigger="hover" width="220" placement="top">
                    <template #reference>
                      <el-tag size="small" :color="getTypeColor(entity.type)" style="margin:2px;cursor:pointer;color:#fff;border:none" round>{{ entity.name }}</el-tag>
                    </template>
                    <div style="font-size:13px">
                      <div style="font-weight:600;margin-bottom:6px">{{ entity.name }}</div>
                      <div style="color:#909399;font-size:12px;margin-bottom:4px">类型：{{ entity.type }}</div>
                      <div v-if="entity.description" style="color:#606266;font-size:12px;line-height:1.5">{{ entity.description }}</div>
                    </div>
                  </el-popover>
                </div>
                <div v-if="msg.kg_references.edges?.length" class="kg-edges">
                  <span class="kg-label">关系：</span>
                  <div v-for="(edge, i) in msg.kg_references.edges" :key="i" class="kg-edge-item">
                    <el-tag size="small" :color="getEntityColor(msg.kg_references.entities, edge.source)" style="color:#fff;border:none;font-size:11px" round>{{ edge.source }}</el-tag>
                    <span style="color:#909399;font-size:11px">—[{{ edge.rel }}]→</span>
                    <el-tag size="small" :color="getEntityColor(msg.kg_references.entities, edge.target)" style="color:#fff;border:none;font-size:11px" round>{{ edge.target }}</el-tag>
                  </div>
                </div>
              </div>
            </div>
            <div class="message-avatar user-avatar" v-if="msg.role === 'user'">
              <el-icon :size="20" color="#fff"><User /></el-icon>
            </div>
          </div>
          <div v-if="qa.messages.length === 0" class="clay-empty" style="padding-top:120px">
            <div class="clay-empty-icon" style="background:linear-gradient(135deg,#ecf0ff,#f5f3ff)">
              <el-icon :size="48" color="#667eea"><ChatDotRound /></el-icon>
            </div>
            <div class="clay-empty-title">开始提问吧</div>
            <div class="clay-empty-desc">输入您的问题，AI 将基于知识库为您解答</div>
          </div>
        </div>

        <div class="input-area">
          <el-select v-model="modelName" style="width:180px" size="large">
            <el-option v-for="m in models" :key="m.model_name" :label="m.model_name" :value="m.model_name" />
          </el-select>
          <el-input v-model="question" placeholder="输入问题..." @keyup.enter="handleSend" size="large" style="flex:1" class="clay-input">
            <template #append>
              <el-button :loading="qa.sending" @click="handleSend" class="clay-btn" style="border-radius:0 10px 10px 0;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none">
                <el-icon v-if="!qa.sending" style="margin-right:4px"><Position /></el-icon>
                {{ qa.sending ? '发送中...' : '发送' }}
              </el-button>
            </template>
          </el-input>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Delete, ChatDotRound, Plus, User, Position } from '@element-plus/icons-vue'
import { useQAStore } from '../../stores/qa'
import { getModels } from '../../api/qa'
import MarkdownIt from 'markdown-it'

const qa = useQAStore()
const md = new MarkdownIt()
const question = ref('')
const modelName = ref('deepseek-chat')
const models = ref([])
const chatArea = ref(null)

const COLORS = ['#5470c6','#91cc75','#fac858','#ee6666','#73c0de','#3ba272','#fc8452','#9a60b4','#ea7ccc','#48b8d0','#ff6b6b','#4ecdc4','#45b7d1','#96ceb4','#ffeaa7','#dfe6e9','#fd79a8','#6c5ce7','#00b894','#e17055']
const TYPE_COLORS = {}

function getTypeColor(type) {
  if (!TYPE_COLORS[type]) {
    const keys = Object.keys(TYPE_COLORS)
    TYPE_COLORS[type] = COLORS[keys.length % COLORS.length]
  }
  return TYPE_COLORS[type]
}

function getEntityColor(entities, name) {
  if (!entities) return '#909399'
  const entity = entities.find(e => e.name === name)
  return entity ? getTypeColor(entity.type) : '#909399'
}

onMounted(async () => {
  await qa.loadConversations()
  try {
    const res = await getModels()
    models.value = res.data
    if (models.value.length) {
      const defaultModel = models.value.find(m => m.is_default)
      if (defaultModel) modelName.value = defaultModel.model_name
    }
  } catch {}
})

async function handleNew() { await qa.newConversation() }

async function handleSend() {
  if (!question.value.trim()) return
  const q = question.value
  question.value = ''
  await qa.sendMessage(q, modelName.value)
  await nextTick()
  if (chatArea.value) chatArea.value.scrollTop = chatArea.value.scrollHeight
}

function renderMarkdown(text) { return md.render(text || '') }
</script>

<style scoped>
.conv-sidebar { background: #fff; border-right: 3px solid #f0f0f0; display: flex; flex-direction: column; }
.conv-header { padding: 16px; border-bottom: 2px solid #f0f0f0; }
.conv-list { flex: 1; overflow-y: auto; padding: 8px; }
.conv-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px; border-radius: 12px; cursor: pointer;
  transition: all 0.2s; margin-bottom: 4px;
  border: 2px solid transparent;
}
.conv-item:hover { background: #f5f7fa; border-color: #e8e8e8; }
.conv-item.active { background: #ecf0ff; border-color: #667eea; }
.conv-item-content { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
.conv-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; color: #303133; font-weight: 500; }
.conv-delete { color: #c0c4cc; cursor: pointer; opacity: 0; transition: opacity 0.15s; flex-shrink: 0; }
.conv-item:hover .conv-delete { opacity: 1; }
.conv-delete:hover { color: #f56c6c; }

.chat-area { flex: 1; overflow-y: auto; padding: 24px; background: #f8f9fb; }
.message { margin-bottom: 20px; display: flex; gap: 12px; align-items: flex-start; }
.message.user { justify-content: flex-end; }
.message.bot { justify-content: flex-start; }

.message-avatar {
  width: 40px; height: 40px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  border: 2px solid rgba(255,255,255,0.3); box-shadow: 0 3px 0 rgba(0,0,0,0.08);
}
.bot-avatar { background: linear-gradient(135deg, #667eea, #764ba2); }
.user-avatar { background: linear-gradient(135deg, #f093fb, #f5576c); }

.bubble {
  max-width: 70%; padding: 14px 18px; border-radius: 16px; line-height: 1.7; font-size: 14px;
  border: 2px solid transparent;
}
.bubble.user {
  background: linear-gradient(135deg, #667eea, #764ba2); color: #fff;
  border-bottom-right-radius: 4px; border-color: rgba(255,255,255,0.2);
}
.bubble.bot {
  background: #fff; color: #303133;
  border-bottom-left-radius: 4px; border-color: #f0f0f0;
  box-shadow: 0 3px 0 #f0f0f0;
}

.sources-section { margin-top: 12px; padding-top: 12px; border-top: 1px solid #f0f0f0; }
.sources-title { font-size: 12px; color: #909399; margin-bottom: 8px; font-weight: 500; }
.sources-tags { display: flex; flex-wrap: wrap; gap: 6px; }

.kg-section { margin-top: 12px; padding-top: 12px; border-top: 1px solid #f0f0f0; }
.kg-title { font-size: 12px; color: #909399; margin-bottom: 8px; font-weight: 500; }
.kg-label { font-size: 12px; color: #606266; margin-right: 4px; }
.kg-entities { margin-bottom: 8px; }
.kg-edges { display: flex; flex-direction: column; gap: 4px; }
.kg-edge-item { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #606266; padding: 2px 0; }

.input-area {
  padding: 16px 20px; border-top: 2px solid #f0f0f0; background: #fff;
  display: flex; gap: 12px;
}
.input-area :deep(.el-input__wrapper) {
  border-radius: 12px; border: 2px solid #e8e8e8; box-shadow: 0 3px 0 #e8e8e8;
}
</style>
