<template>
  <div>
    <div class="clay-hero" style="background:linear-gradient(135deg,#f093fb,#f5576c)">
      <h2 class="clay-hero-title">问答历史</h2>
      <p class="clay-hero-subtitle">查看所有用户的问答记录和统计信息</p>
    </div>

    <el-row :gutter="16" style="margin-top:20px;margin-bottom:20px">
      <el-col :span="8">
        <div class="clay-card">
          <div class="clay-stat">
            <div class="clay-stat-icon" style="background:#ecf0ff;border-color:#667eea"><el-icon :size="22" color="#667eea"><Timer /></el-icon></div>
            <div><div class="clay-stat-label">今日问答数</div><div class="clay-stat-value" style="color:#667eea">{{ stats.today_questions }}</div></div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="clay-card">
          <div class="clay-stat">
            <div class="clay-stat-icon" style="background:#ecfdf5;border-color:#10b981"><el-icon :size="22" color="#10b981"><Document /></el-icon></div>
            <div><div class="clay-stat-label">最热门文档</div><div class="clay-stat-value" style="color:#10b981;font-size:14px;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ stats.hot_doc || '-' }}</div></div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="clay-card">
          <div class="clay-stat">
            <div class="clay-stat-icon" style="background:#fffbeb;border-color:#f59e0b"><el-icon :size="22" color="#f59e0b"><Search /></el-icon></div>
            <div><div class="clay-stat-label">高频关键词</div><div class="clay-stat-value" style="color:#f59e0b">{{ stats.hot_keyword || '-' }}</div></div>
          </div>
        </div>
      </el-col>
    </el-row>

    <div class="clay-panel">
      <div class="clay-panel-header"><span class="clay-panel-title">全局问答记录</span></div>
      <el-table :data="history" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="question" label="问题" min-width="300" show-overflow-tooltip>
          <template #default="{ row }"><span style="font-weight:500">{{ row.question }}</span></template>
        </el-table-column>
        <el-table-column prop="username" label="用户" width="120">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:6px">
              <div style="width:28px;height:28px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;background:#ecf0ff;color:#667eea">{{ (row.username||'?')[0].toUpperCase() }}</div>
              <span>{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }"><el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button></template>
        </el-table-column>
      </el-table>
      <div style="padding:16px;display:flex;justify-content:flex-end" class="clay-pagination">
        <el-pagination v-model:current-page="page" :page-size="size" :total="total" layout="total,prev,pager,next" @current-change="loadHistory" />
      </div>
    </div>

    <el-dialog v-model="showDetail" title="对话详情" width="700" class="clay-dialog">
      <div ref="detailChat" style="max-height:500px;overflow-y:auto;padding:16px">
        <div v-for="msg in detailMessages" :key="msg.id" :style="{display:'flex',justifyContent:msg.role==='user'?'flex-end':'flex-start',marginBottom:'16px'}">
          <div :style="{maxWidth:'75%',padding:'12px 16px',borderRadius:'16px',lineHeight:'1.7',background:msg.role==='user'?'linear-gradient(135deg,#667eea,#764ba2)':'#fff',color:msg.role==='user'?'#fff':'#303133',border:msg.role==='bot'?'2px solid #f0f0f0':'none',boxShadow:msg.role==='bot'?'0 3px 0 #f0f0f0':'none'}">
            <div v-html="renderMarkdown(msg.content)"></div>
            <div v-if="msg.sources && msg.sources.length" style="margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.2);font-size:12px;opacity:0.8">
              <div v-for="(s,i) in msg.sources" :key="i">{{ s.doc_name }} (相似度: {{ s.similarity }})</div>
            </div>
          </div>
        </div>
        <div v-if="detailMessages.length===0" class="clay-empty"><div class="clay-empty-icon" style="background:#f5f3ff"><el-icon :size="32" color="#8b5cf6"><ChatDotRound /></el-icon></div><div class="clay-empty-desc">暂无消息</div></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { Timer, Document, Search, ChatDotRound } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import { getAdminHistory } from '../../api/history'
import { getStats } from '../../api/dashboard'
import client from '../../api/client'

const md = new MarkdownIt()
const history = ref([]); const loading = ref(false); const page = ref(1); const size = 20; const total = ref(0)
const stats = reactive({ today_questions: 0, hot_doc: '', hot_keyword: '' })
const showDetail = ref(false); const detailMessages = ref([]); const detailChat = ref(null)

onMounted(() => { loadHistory(); loadStats() })

async function loadStats() {
  try {
    const res = await getStats(); stats.today_questions = res.data.today_questions || 0
    const typeCounts = res.data.type_counts || {}
    if (Object.keys(typeCounts).length > 0) { const hotType = Object.entries(typeCounts).sort((a,b) => b[1]-a[1])[0]; stats.hot_doc = hotType[0]+' ('+hotType[1]+'份)' }
  } catch {}
}

async function loadHistory() {
  loading.value = true
  try {
    const res = await getAdminHistory({ page: page.value, size }); history.value = res.data.items || []; total.value = res.data.total || 0
    if (history.value.length > 0) {
      const keywords = {}
      history.value.forEach(h => { const words = h.question.match(/[一-龥]{2,}/g) || []; words.forEach(w => { if (w.length >= 2) keywords[w] = (keywords[w]||0)+1 }) })
      const sorted = Object.entries(keywords).sort((a,b) => b[1]-a[1]); if (sorted.length > 0) stats.hot_keyword = sorted[0][0]
    }
  } catch {} finally { loading.value = false }
}

async function openDetail(row) { showDetail.value = true; detailMessages.value = []; try { const res = await client.get(`/qa/conversations/${row.conversation_id}/messages`); detailMessages.value = res.data || []; await nextTick(); if (detailChat.value) detailChat.value.scrollTop = detailChat.value.scrollHeight } catch {} }
function renderMarkdown(text) { return md.render(text || '') }
</script>
