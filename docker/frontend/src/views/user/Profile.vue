<template>
  <div>
    <h2>个人中心</h2>
    <el-card style="margin-top:20px;max-width:500px">
      <el-form label-width="100px">
        <el-form-item label="用户名">
          <el-input :value="auth.user?.username" disabled />
        </el-form-item>
        <el-form-item label="角色">
          <el-tag>{{ auth.user?.role }}</el-tag>
        </el-form-item>
        <el-divider />
        <el-form-item label="原密码">
          <el-input v-model="form.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="form.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleChangePassword">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import { changePassword } from '../../api/auth'

const auth = useAuthStore()
const form = ref({ old_password: '', new_password: '' })

async function handleChangePassword() {
  try {
    await changePassword(form.value)
    ElMessage.success('密码修改成功')
    form.value = { old_password: '', new_password: '' }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '修改失败')
  }
}
</script>
