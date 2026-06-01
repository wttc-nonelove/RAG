<template>
  <el-container style="height:calc(100vh - 140px)">
    <el-aside width="260px" style="background:#fff;border-right:1px solid #e8e8e8">
      <div style="padding:12px">
        <el-button type="primary" style="width:100%" @click="handleNew">新建对话</el-button>
      </div>
      <el-menu :default-active="String(qa.currentConv?.id || '')">
        <el-menu-item v-for="conv in qa.conversations" :key="conv.id" :index="String(conv.id)" @click="qa.selectConversation(conv)">
          <div style="display:flex;justify-content:space-between;width:100%">
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ conv.title }}</span>
            <el-icon @click.stop="qa.removeConversation(conv.id)" style="color:#f56c6c"><Delete /></el-icon>
          </div>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-main style="display:flex;flex-direction:column;padding:0">
        <div ref="chatArea" style="flex:1;overflow-y:auto;padding:20px">
          <div v-for="msg in qa.messages" :key="msg.id" :class="['message', msg.role]">
            <div class="bubble">
              <div v-html="renderMarkdown(msg.content)"></div>
              <div v-if="msg.sources && msg.sources.length" style="margin-top:8px;border-top:1px solid #ddd;padding-top:8px">
                <div style="font-size:12px;color:#909399;margin-bottom:4px">引用来源：</div>
                <el-tag v-for="(s, i) in msg.sources" :key="i" size="small" style="margin:2px" type="info">
                  {{ s.doc_name }} {{ s.page ? `p.${s.page}` : '' }}
                </el-tag>
              </div>
            </div>
          </div>
          <div v-if="qa.messages.length === 0" style="text-align:center;color:#c0c4cc;padding-top:100px">
            开始提问吧
          </div>
        </div>

        <div style="padding:16px 20px;border-top:1px solid #e8e8e8;background:#fff;display:flex;gap:12px">
          <el-select v-model="modelName" style="width:180px" size="large">
            <el-option v-for="m in models" :key="m.model_name" :label="m.model_name" :value="m.model_name" />
          </el-select>
          <el-input v-model="question" placeholder="输入问题..." @keyup.enter="handleSend" size="large" style="flex:1">
            <template #append>
              <el-button :loading="qa.sending" @click="handleSend">发送</el-button>
            </template>
          </el-input>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { useQAStore } from '../../stores/qa'
import { getModels } from '../../api/qa'
import MarkdownIt from 'markdown-it'

const qa = useQAStore()
const md = new MarkdownIt()
const question = ref('')
const modelName = ref('deepseek-chat')
const models = ref([])
const chatArea = ref(null)

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
.message { margin-bottom: 16px; display: flex; }
.message.user { justify-content: flex-end; }
.message.bot { justify-content: flex-start; }
.bubble {
  max-width: 70%;
  padding: 10px 16px;
  border-radius: 12px;
  line-height: 1.6;
}
.message.user .bubble { background: #409eff; color: #fff; border-bottom-right-radius: 4px; }
.message.bot .bubble { background: #f4f4f5; color: #303133; border-bottom-left-radius: 4px; }
</style>
