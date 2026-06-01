<template>
  <div>
    <h2>工作台</h2>
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="6" v-for="item in stats" :key="item.label">
        <el-card shadow="hover">
          <div style="font-size:14px;color:#909399">{{ item.label }}</div>
          <div style="font-size:28px;font-weight:bold;margin-top:8px;color:#303133">{{ item.value }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStats } from '../../api/dashboard'

const stats = ref([
  { label: '文档总数', value: 0 },
  { label: '问答次数', value: 0 },
  { label: '用户数量', value: 0 },
  { label: '向量片段', value: 0 },
])

onMounted(async () => {
  try {
    const res = await getStats()
    stats.value[0].value = res.data.total_documents || 0
    stats.value[1].value = res.data.total_questions || 0
    stats.value[2].value = res.data.total_users || 0
    stats.value[3].value = res.data.total_chunks || 0
  } catch {}
})
</script>
