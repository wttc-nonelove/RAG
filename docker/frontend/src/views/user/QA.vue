<template>
  <el-container style="height:calc(100vh - 140px)">
    <!-- 左侧会话列表 -->
    <el-aside width="280px" class="conv-sidebar">
      <div class="conv-sidebar-header">
        <el-button type="primary" style="width:100%;border-radius:10px" @click="handleNew">
          <el-icon style="margin-right:4px"><Plus /></el-icon>新建对话
        </el-button>
      </div>
      <div class="conv-list">
        <div v-for="conv in qa.conversations" :key="conv.id"
          class="conv-item"
          :class="{ active: qa.currentConv?.id === conv.id }"
          @click="qa.selectConversation(conv)">
          <div class="conv-item-content">
            <el-icon :size="16" style="color:#909399;flex-shrink:0"><ChatDotRound /></el-icon>
            <span class="conv-title">{{ conv.title }}</span>
          </div>
          <el-icon class="conv-delete" @click.stop="qa.removeConversation(conv.id)"><Delete /></el-icon>
        </div>
        <div v-if="qa.conversations.length === 0" style="text-align:center;color:#c0c4cc;padding:40px 20px;font-size:13px">
          暂无对话，点击上方按钮新建
        </div>
      </div>
    </el-aside>

    <!-- 右侧聊天区域 -->
    <el-container>
      <el-main style="display:flex;flex-direction:column;padding:0">
        <!-- 消息区域 -->
        <div ref="chatArea" class="chat-area">
          <div v-for="msg in qa.messages" :key="msg.id" :class="['message', msg.role]">
            <div class="message-avatar" v-if="msg.role === 'bot'">
              <el-icon :size="20" color="#fff"><ChatDotRound /></el-icon>
            </div>
            <div class="bubble">
              <div v-html="renderMarkdown(msg.content)"></div>
              <!-- 引用来源 -->
              <div v-if="msg.sources && msg.sources.length" class="sources-section">
                <div class="sources-title">引用来源</div>
                <div class="sources-tags">
                  <el-tag v-for="(s, i) in msg.sources" :key="i" size="small" effect="plain" round>
                    {{ s.doc_name }} {{ s.page ? `p.${s.page}` : '' }}
                  </el-tag>
                </div>
              </div>
              <!-- 知识图谱引用 -->
              <div v-if="msg.kg_references && (msg.kg_references.entities?.length || msg.kg_references.edges?.length)" class="kg-section">
                <div class="kg-title">知识图谱引用</div>
                <div v-if="msg.kg_references.entities?.length" class="kg-entities">
                  <span class="kg-label">实体：</span>
                  <el-popover v-for="entity in msg.kg_references.entities" :key="entity.name" trigger="hover" width="220" placement="top">
                    <template #reference>
                      <el-tag size="small" :color="getTypeColor(entity.type)" style="margin:2px;cursor:pointer;color:#fff;border:none" round>
                        {{ entity.name }}
                      </el-tag>
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
          <!-- 空状态 -->
          <div v-if="qa.messages.length === 0" class="empty-state">
            <div class="empty-icon">
              <el-icon :size="48" color="#c0c4cc"><ChatDotRound /></el-icon>
            </div>
            <div class="empty-title">开始提问吧</div>
            <div class="empty-desc">输入您的问题，AI 将基于知识库为您解答</div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <el-select v-model="modelName" style="width:180px" size="large">
            <el-option v-for="m in models" :key="m.model_name" :label="m.model_name" :value="m.model_name" />
          </el-select>
          <el-input v-model="question" placeholder="输入问题..." @keyup.enter="handleSend" size="large" style="flex:1">
            <template #append>
              <el-button :loading="qa.sending" @click="handleSend" style="border-radius:0 8px 8px 0">
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

async function handleNew() {
  await qa.newConversation()
}

async function handleSend() {
  if (!question.value.trim()) return
  const q = question.value
  question.value = ''
  await qa.sendMessage(q, modelName.value)
  await nextTick()
  if (chatArea.value) chatArea.value.scrollTop = chatArea.value.scrollHeight
}

function renderMarkdown(text) {
  return md.render(text || '')
}
</script>

<style scoped>
/* 会话侧边栏 */
.conv-sidebar {
  background: #fff;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
}
.conv-sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.conv-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
  margin-bottom: 4px;
}
.conv-item:hover {
  background: #f5f7fa;
}
.conv-item.active {
  background: #ecf5ff;
}
.conv-item-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}
.conv-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: #303133;
}
.conv-delete {
  color: #c0c4cc;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
  flex-shrink: 0;
}
.conv-item:hover .conv-delete {
  opacity: 1;
}
.conv-delete:hover {
  color: #f56c6c;
}

/* 聊天区域 */
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f5f7fa;
}

.message {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.message.user {
  justify-content: flex-end;
}
.message.bot {
  justify-content: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.user-avatar {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
}

.bubble {
  max-width: 70%;
  padding: 14px 18px;
  border-radius: 14px;
  line-height: 1.7;
  font-size: 14px;
}
.message.user .bubble {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.message.bot .bubble {
  background: #fff;
  color: #303133;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

/* 引用来源 */
.sources-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}
.sources-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  font-weight: 500;
}
.sources-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 知识图谱引用 */
.kg-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}
.kg-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  font-weight: 500;
}
.kg-label {
  font-size: 12px;
  color: #606266;
  margin-right: 4px;
}
.kg-entities {
  margin-bottom: 8px;
}
.kg-edges {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.kg-edge-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
  padding: 2px 0;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding-top: 100px;
}
.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: #ecf5ff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}
.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}
.empty-desc {
  font-size: 13px;
  color: #909399;
}

/* 输入区域 */
.input-area {
  padding: 16px 20px;
  border-top: 1px solid #e8e8e8;
  background: #fff;
  display: flex;
  gap: 12px;
}
.input-area :deep(.el-input__wrapper) {
  border-radius: 10px;
}
</style>
