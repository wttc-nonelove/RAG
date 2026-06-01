<template>
  <div>
    <h2>问答历史</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="8">
        <el-card shadow="hover" body-style="padding:20px">
          <div style="font-size:13px;color:#909399">今日问答数</div>
          <div style="font-size:28px;font-weight:bold;color:#409eff;margin-top:8px">{{ stats.today_questions }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" body-style="padding:20px">
          <div style="font-size:13px;color:#909399">最热门文档</div>
          <div style="font-size:16px;font-weight:bold;color:#67c23a;margin-top:8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ stats.hot_doc || '-' }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" body-style="padding:20px">
          <div style="font-size:13px;color:#909399">高频关键词</div>
          <div style="font-size:16px;font-weight:bold;color:#e6a23c;margin-top:8px">{{ stats.hot_keyword || '-' }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top:20px">
      <el-table :data="history" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="question" label="问题" min-width="300" show-overflow-tooltip />
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top:16px;display:flex;justify-content:flex-end">
        <el-pagination v-model:current-page="page" :page-size="size" :total="total" layout="total,prev,pager,next" @current-change="loadHistory" />
      </div>
    </el-card>

    <el-dialog v-model="showDetail" title="对话详情" width="700">
      <div ref="detailChat" style="max-height:500px;overflow-y:auto;padding:10px">
        <div v-for="msg in detailMessages" :key="msg.id" :style="{ display:'flex', justifyContent: msg.role==='user'?'flex-end':'flex-start', marginBottom:'12px' }">
          <div :style="{ maxWidth:'75%', padding:'10px 16px', borderRadius:'12px', lineHeight:'1.6', background: msg.role==='user'?'#409eff':'#f4f4f5', color: msg.role==='user'?'#fff':'#303133' }">
            <div v-html="renderMarkdown(msg.content)"></div>
            <div v-if="msg.sources && msg.sources.length" style="margin-top:8px;border-top:1px solid #ddd;padding-top:8px;font-size:12px;color:#909399">
              <div v-for="(s,i) in msg.sources" :key="i">{{ s.doc_name }} (相似度: {{ s.similarity }})</div>
            </div>
          </div>
        </div>
        <div v-if="detailMessages.length===0" style="text-align:center;color:#c0c4cc;padding:40px">暂无消息</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
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
    // 获取最热门文档（从文档类型推断）
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
    // 从历史记录中提取高频关键词
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
