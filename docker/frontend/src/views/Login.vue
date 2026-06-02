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
          <el-button type="primary" size="large" class="login-btn" :loading="loading" native-type="submit">
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <span style="color:#909399;font-size:13px">还没有账号？</span>
        <el-link type="primary" @click="showRegister = true" style="font-size:13px">立即注册</el-link>
      </div>
    </div>

    <div class="login-deco deco-1"></div>
    <div class="login-deco deco-2"></div>
    <div class="login-deco deco-3"></div>

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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  position: relative;
  overflow: hidden;
}

.login-card {
  width: 420px;
  background: rgba(255,255,255,0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 40px;
  border: 3px solid rgba(255,255,255,0.3);
  box-shadow: 0 8px 0 rgba(0,0,0,0.06), 0 20px 60px rgba(0,0,0,0.15);
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
  border-radius: 18px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  border: 3px solid rgba(255,255,255,0.3);
  box-shadow: 0 6px 0 rgba(0,0,0,0.1);
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

.login-form { margin-bottom: 24px; }
.login-form :deep(.el-input__wrapper) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  box-shadow: 0 3px 0 #e8e8e8;
}
.login-form :deep(.el-input__wrapper:focus-within) {
  border-color: #667eea;
  box-shadow: 0 3px 0 #667eea;
}

.login-btn {
  width: 100%;
  height: 46px;
  font-size: 15px;
  font-weight: 700;
  border-radius: 12px;
  border: 2px solid transparent;
  box-shadow: 0 4px 0 #4f5bd5;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 0 #4f5bd5;
}
.login-btn:active {
  transform: translateY(1px);
  box-shadow: 0 2px 0 #4f5bd5;
}

.login-footer {
  text-align: center;
  padding-top: 16px;
  border-top: 2px solid #f0f0f0;
}

.login-deco {
  position: absolute;
  border-radius: 50%;
  opacity: 0.12;
  background: #fff;
}
.deco-1 { width: 300px; height: 300px; top: -80px; left: -80px; animation: clay-float 8s ease-in-out infinite; }
.deco-2 { width: 200px; height: 200px; bottom: -60px; right: -40px; animation: clay-float 6s ease-in-out infinite reverse; }
.deco-3 { width: 120px; height: 120px; top: 50%; right: 15%; animation: clay-float 7s ease-in-out infinite; }

@keyframes clay-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-15px); }
}
</style>
