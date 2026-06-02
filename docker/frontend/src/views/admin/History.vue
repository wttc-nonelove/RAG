<template>
  <div>
    <!-- 页面标题区域 -->
    <div style="background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);border-radius:12px;padding:24px 28px;margin-bottom:20px">
      <h2 style="color:#fff;margin:0;font-size:22px;font-weight:600">问答历史</h2>
      <p style="color:rgba(255,255,255,0.8);margin:6px 0 0;font-size:13px">查看所有用户的问答记录和统计信息</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom:20px">
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-icon" style="background:#ecf5ff">
            <el-icon :size="22" color="#409eff"><Timer /></el-icon>
          </div>
          <div>
            <div class="stat-label">今日问答数</div>
            <div class="stat-value" style="color:#409eff">{{ stats.today_questions }}</div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-icon" style="background:#f0f9eb">
            <el-icon :size="22" color="#67c23a"><Document /></el-icon>
          </div>
          <div>
            <div class="stat-label">最热门文档</div>
            <div class="stat-value" style="color:#67c23a;font-size:14px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:150px">{{ stats.hot_doc || '-' }}</div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-icon" style="background:#fdf6ec">
            <el-icon :size="22" color="#e6a23c"><Search /></el-icon>
          </div>
          <div>
            <div class="stat-label">高频关键词</div>
            <div class="stat-value" style="color:#e6a23c">{{ stats.hot_keyword || '-' }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 历史记录表格 -->
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">全局问答记录</span>
      </div>
      <el-table :data="history" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="question" label="问题" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            <span style="font-weight:500">{{ row.question }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户" width="120">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:6px">
              <div style="width:24px;height:24px;border-radius:6px;background:#ecf5ff;display:flex;align-items:center;justify-content:center">
                <span style="font-size:11px;font-weight:600;color:#409eff">{{ (row.username || '?')[0].toUpperCase() }}</span>
              </div>
              <span>{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="padding:16px;display:flex;justify-content:flex-end">
        <el-pagination v-model:current-page="page" :page-size="size" :total="total" layout="total,prev,pager,next" @current-change="loadHistory" />
      </div>
    </div>

    <!-- 对话详情弹窗 -->
    <el-dialog v-model="showDetail" title="对话详情" width="700">
      <div ref="detailChat" class="detail-chat">
        <div v-for="msg in detailMessages" :key="msg.id" :class="['detail-message', msg.role]">
          <div class="detail-bubble" :class="msg.role">
            <div v-html="renderMarkdown(msg.content)"></div>
            <div v-if="msg.sources && msg.sources.length" class="detail-sources">
              <div v-for="(s,i) in msg.sources" :key="i">{{ s.doc_name }} (相似度: {{ s.similarity }})</div>
            </div>
          </div>
        </div>
        <div v-if="detailMessages.length===0" style="text-align:center;color:#c0c4cc;padding:60px">暂无消息</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { Timer, Document, Search } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import { getAdminHistory } from '../../api/history'
import { getStats } from '../../api/dashboard'
import client from '../../api/client'

const md = new MarkdownIt()
const history = ref([])
const loading = ref(false)
const page = ref(1)
const size = 20
const total = ref(0)

const stats = reactive({
  today_questions: 0,
  hot_doc: '',
  hot_keyword: '',
})

const showDetail = ref(false)
const detailMessages = ref([])
const detailChat = ref(null)

onMounted(() => {
  loadHistory()
  loadStats()
})

async function loadStats() {
  try {
    const res = await getStats()
    stats.today_questions = res.data.today_questions || 0
    const typeCounts = res.data.type_counts || {}
    if (Object.keys(typeCounts).length > 0) {
      const hotType = Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0]
      stats.hot_doc = hotType[0] + ' (' + hotType[1] + '份)'
    }
  } catch {}
}

async function loadHistory() {
  loading.value = true
  try {
    const res = await getAdminHistory({ page: page.value, size })
    history.value = res.data.items || []
    total.value = res.data.total || 0
    if (history.value.length > 0) {
      const keywords = {}
      history.value.forEach(h => {
        const words = h.question.match(/[一-龥]{2,}/g) || []
        words.forEach(w => {
          if (w.length >= 2) keywords[w] = (keywords[w] || 0) + 1
        })
      })
      const sorted = Object.entries(keywords).sort((a, b) => b[1] - a[1])
      if (sorted.length > 0) stats.hot_keyword = sorted[0][0]
    }
  } catch {} finally {
    loading.value = false
  }
}

async function openDetail(row) {
  showDetail.value = true
  detailMessages.value = []
  try {
    const res = await client.get(`/qa/conversations/${row.conversation_id}/messages`)
    detailMessages.value = res.data || []
    await nextTick()
    if (detailChat.value) detailChat.value.scrollTop = detailChat.value.scrollHeight
  } catch {}
}

function renderMarkdown(text) {
  return md.render(text || '')
}
</script>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 18px 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border: 1px solid #f0f0f0;
  transition: all 0.2s ease;
}
.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transform: translateY(-2px);
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-label {
  font-size: 12px;
  color: #909399;
  line-height: 1;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin-top: 4px;
  line-height: 1;
}

.panel {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border: 1px solid #f0f0f0;
  overflow: hidden;
}
.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}
.panel-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.detail-chat {
  max-height: 500px;
  overflow-y: auto;
  padding: 16px;
}
.detail-message {
  margin-bottom: 16px;
  display: flex;
}
.detail-message.user {
  justify-content: flex-end;
}
.detail-message.bot {
  justify-content: flex-start;
}
.detail-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
}
.detail-bubble.user {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 4px;
}
.detail-bubble.bot {
  background: #f4f4f5;
  color: #303133;
  border-bottom-left-radius: 4px;
}
.detail-sources {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #ddd;
  font-size: 12px;
  color: #909399;
}
</style>
