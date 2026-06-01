<template>
  <div>
    <h2>我的问答历史</h2>
    <el-card style="margin-top:20px">
      <el-table :data="history" stripe v-loading="loading">
        <el-table-column prop="question" label="问题" />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>
      <div style="margin-top:16px;display:flex;justify-content:flex-end">
        <el-pagination v-model:current-page="page" :page-size="size" :total="total" layout="total,prev,pager,next" @current-change="loadHistory" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getMyHistory } from '../../api/history'

const history = ref([])
const loading = ref(false)
const page = ref(1)
const size = 20
const total = ref(0)

onMounted(() => loadHistory())

async function loadHistory() {
  loading.value = true
  try {
    const res = await getMyHistory({ page: page.value, size })
    history.value = res.data.items || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}
</script>
