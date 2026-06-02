<template>
  <div>
    <!-- 页面标题区域 -->
    <div style="background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);border-radius:12px;padding:24px 28px;margin-bottom:20px">
      <h2 style="color:#fff;margin:0;font-size:22px;font-weight:600">用户管理</h2>
      <p style="color:rgba(255,255,255,0.8);margin:6px 0 0;font-size:13px">管理系统用户账号、角色和权限</p>
    </div>

    <!-- 用户列表 -->
    <div class="panel">
      <div class="panel-header">
        <div style="display:flex;gap:12px;align-items:center">
          <el-input v-model="keyword" placeholder="搜索用户" style="width:200px" clearable @clear="loadUsers" @keyup.enter="loadUsers" />
        </div>
        <el-button type="primary" @click="showDialog = true">
          <el-icon style="margin-right:4px"><Plus /></el-icon>新增用户
        </el-button>
      </div>
      <el-table :data="users" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="150">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:10px">
              <div style="width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600"
                :style="{background: row.role === 'admin' ? '#fef0f0' : '#ecf5ff', color: row.role === 'admin' ? '#f56c6c' : '#409eff'}">
                {{ row.username[0].toUpperCase() }}
              </div>
              <span style="font-weight:500">{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" effect="dark" round size="small">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" effect="dark" round size="small">
              {{ row.status === 'active' ? '正常' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="warning" size="small" @click="handleResetPwd(row)">重置密码</el-button>
            <el-button link :type="row.status === 'active' ? 'danger' : 'success'" size="small" @click="handleToggleStatus(row)">
              {{ row.status === 'active' ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="padding:16px;display:flex;justify-content:flex-end">
        <el-pagination v-model:current-page="page" :page-size="size" :total="total" layout="total,prev,pager,next" @current-change="loadUsers" />
      </div>
    </div>

    <!-- 新增用户弹窗 -->
    <el-dialog v-model="showDialog" title="新增用户" width="400">
      <el-form :model="newUser" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="newUser.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="newUser.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="newUser.role" style="width:100%">
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
import { Plus } from '@element-plus/icons-vue'
import client from '../../api/client'

const keyword = ref('')
const showDialog = ref(false)
const users = ref([])
const loading = ref(false)
const page = ref(1)
const size = 20
const total = ref(0)
const newUser = ref({ username: '', password: '', role: 'user' })

onMounted(() => loadUsers())

async function loadUsers() {
  loading.value = true
  try {
    const res = await client.get('/users', { params: { page: page.value, size, keyword: keyword.value } })
    users.value = res.data.items || []
    total.value = res.data.total || 0
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

<style scoped>
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
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
