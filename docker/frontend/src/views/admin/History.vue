<template>
  <div>
    <h2>问答历史</h2>
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
import { ref, onMounted, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import { getAdminHistory } from '../../api/history'
import client from '../../api/client'

const md = new MarkdownIt()
const history = ref([])
const loading = ref(false)
const page = ref(1)
const size = 20
const total = ref(0)

const showDetail = ref(false)
const detailMessages = ref([])
const detailChat = ref(null)

onMounted(() => loadHistory())

async function loadHistory() {
  loading.value = true
  try {
    const res = await getAdminHistory({ page: page.value, size })
    history.value = res.data.items || []
    total.value = res.data.total || 0
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
