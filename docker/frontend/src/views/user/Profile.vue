<template>
  <div>
    <div class="clay-hero" style="background:linear-gradient(135deg,#a18cd1,#fbc2eb)">
      <h2 class="clay-hero-title">个人中心</h2>
      <p class="clay-hero-subtitle">管理您的账号信息和安全设置</p>
    </div>

    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="8">
        <div class="clay-card" style="text-align:center;padding:32px 24px">
          <div style="width:80px;height:80px;border-radius:20px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;margin:0 auto 16px;font-size:32px;font-weight:700;color:#fff;border:3px solid rgba(255,255,255,0.3);box-shadow:0 6px 0 rgba(0,0,0,0.1)">{{ (auth.user?.username||'?')[0].toUpperCase() }}</div>
          <div style="font-size:20px;font-weight:700;color:#1a1a2e;margin-bottom:8px">{{ auth.user?.username }}</div>
          <el-tag :type="auth.user?.role==='admin'?'danger':'primary'" effect="dark" round>{{ auth.user?.role==='admin'?'管理员':'普通用户' }}</el-tag>
          <div style="display:flex;gap:24px;justify-content:center;margin-top:24px;padding-top:24px;border-top:2px solid #f0f0f0">
            <div style="text-align:center"><div style="font-size:24px;font-weight:700;color:#1a1a2e">-</div><div style="font-size:12px;color:#909399;margin-top:4px">问答次数</div></div>
            <div style="text-align:center"><div style="font-size:24px;font-weight:700;color:#1a1a2e">-</div><div style="font-size:12px;color:#909399;margin-top:4px">文档数量</div></div>
          </div>
        </div>
      </el-col>
      <el-col :span="16">
        <div class="clay-panel">
          <div class="clay-panel-header"><span class="clay-panel-title">修改密码</span></div>
          <div style="padding:24px;max-width:400px">
            <el-form label-width="80px">
              <el-form-item label="用户名"><el-input :value="auth.user?.username" disabled /></el-form-item>
              <el-form-item label="角色"><el-tag :type="auth.user?.role==='admin'?'danger':'primary'" effect="dark" round>{{ auth.user?.role==='admin'?'管理员':'普通用户' }}</el-tag></el-form-item>
              <el-divider />
              <el-form-item label="原密码"><el-input v-model="form.old_password" type="password" placeholder="请输入原密码" show-password /></el-form-item>
              <el-form-item label="新密码"><el-input v-model="form.new_password" type="password" placeholder="请输入新密码（至少6位）" show-password /></el-form-item>
              <el-form-item>
                <el-button type="primary" class="clay-btn" @click="handleChangePassword" style="width:100%;background:linear-gradient(135deg,#a18cd1,#fbc2eb);border:none">
                  <el-icon style="margin-right:4px"><Lock /></el-icon>修改密码
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { changePassword } from '../../api/auth'

const auth = useAuthStore()
const form = ref({ old_password: '', new_password: '' })

async function handleChangePassword() {
  if (!form.value.old_password || !form.value.new_password) return ElMessage.warning('请填写完整')
  if (form.value.new_password.length < 6) return ElMessage.warning('新密码至少6位')
  try { await changePassword(form.value); ElMessage.success('密码修改成功'); form.value = { old_password: '', new_password: '' } } catch (e) { ElMessage.error(e.response?.data?.detail || '修改失败') }
}
</script>
