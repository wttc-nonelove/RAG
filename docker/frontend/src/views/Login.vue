<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">
          <el-icon :size="32" color="#fff"><ChatDotRound /></el-icon>
        </div>
        <h1 class="login-title">RAG 智能问答系统</h1>
        <p class="login-subtitle">基于私有知识库的企业级问答平台</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin" class="login-form">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" size="large" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" style="width:100%;height:44px;font-size:15px;font-weight:600" :loading="loading" native-type="submit">
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <span style="color:#909399;font-size:13px">还没有账号？</span>
        <el-link type="primary" @click="showRegister = true" style="font-size:13px">立即注册</el-link>
      </div>
    </div>

    <!-- 注册弹窗 -->
    <el-dialog v-model="showRegister" title="注册账号" width="400" center>
      <el-form ref="regFormRef" :model="regForm" :rules="regRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="regForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="regForm.password" type="password" placeholder="请输入密码（至少6位）" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegister = false">取消</el-button>
        <el-button type="primary" :loading="regLoading" @click="handleRegister">注册</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { login, register } from '../api/auth'

const router = useRouter()
const auth = useAuthStore()

const formRef = ref()
const regFormRef = ref()
const loading = ref(false)
const regLoading = ref(false)
const showRegister = ref(false)

const form = ref({ username: '', password: '' })
const regForm = ref({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}
const regRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少6位', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    const res = await login(form.value)
    auth.setAuth(res.data.access_token, res.data.user)
    ElMessage.success('登录成功')
    router.push(res.data.user.role === 'admin' ? '/dashboard' : '/qa')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  await regFormRef.value.validate()
  regLoading.value = true
  try {
    await register(regForm.value)
    ElMessage.success('注册成功，请登录')
    showRegister.value = false
    form.value.username = regForm.value.username
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
  } finally {
    regLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}
.login-container::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
  animation: pulse 8s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

.login-card {
  width: 420px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.logo-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}
.login-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 8px;
}
.login-subtitle {
  font-size: 13px;
  color: #909399;
  margin: 0;
}

.login-form {
  margin-bottom: 24px;
}
.login-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.login-form :deep(.el-button) {
  border-radius: 10px;
}

.login-footer {
  text-align: center;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
