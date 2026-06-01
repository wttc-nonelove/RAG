<template>
  <div>
    <h2>用户管理</h2>
    <el-card style="margin-top:20px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div style="display:flex;gap:12px">
            <el-input v-model="keyword" placeholder="搜索用户" style="width:200px" clearable @clear="loadUsers" @keyup.enter="loadUsers" />
          </div>
          <el-button type="primary" @click="showDialog = true">新增用户</el-button>
        </div>
      </template>
      <el-table :data="users" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : ''">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button link type="warning" size="small" @click="handleResetPwd(row)">重置密码</el-button>
            <el-button link :type="row.status === 'active' ? 'danger' : 'success'" size="small" @click="handleToggleStatus(row)">
              {{ row.status === 'active' ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showDialog" title="新增用户" width="400">
      <el-form :model="newUser" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="newUser.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="newUser.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="newUser.role">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '../../api/client'

const keyword = ref('')
const showDialog = ref(false)
const users = ref([])
const loading = ref(false)
const newUser = ref({ username: '', password: '', role: 'user' })

onMounted(() => loadUsers())

async function loadUsers() {
  loading.value = true
  try {
    const res = await client.get('/users', { params: { page: 1, size: 50, keyword: keyword.value } })
    users.value = res.data.items || []
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!newUser.value.username || !newUser.value.password) return ElMessage.warning('请填写完整')
  try {
    await client.post('/users', newUser.value)
    ElMessage.success('创建成功')
    showDialog.value = false
    newUser.value = { username: '', password: '', role: 'user' }
    loadUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  }
}

async function handleResetPwd(row) {
  try {
    await ElMessageBox.confirm(`确定重置 ${row.username} 的密码为 123456？`, '提示')
    await client.put(`/users/${row.id}/reset-password`, { new_password: '123456' })
    ElMessage.success('密码已重置为 123456')
  } catch {}
}

async function handleToggleStatus(row) {
  try {
    const res = await client.put(`/users/${row.id}/status`)
    row.status = res.data.status
    ElMessage.success('状态已更新')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}
</script>
