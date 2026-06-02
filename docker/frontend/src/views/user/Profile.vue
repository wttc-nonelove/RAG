<template>
  <div>
    <!-- 页面标题区域 -->
    <div style="background:linear-gradient(135deg,#a18cd1 0%,#fbc2eb 100%);border-radius:12px;padding:24px 28px;margin-bottom:20px">
      <h2 style="color:#fff;margin:0;font-size:22px;font-weight:600">个人中心</h2>
      <p style="color:rgba(255,255,255,0.8);margin:6px 0 0;font-size:13px">管理您的账号信息和安全设置</p>
    </div>

    <el-row :gutter="20">
      <!-- 用户信息卡片 -->
      <el-col :span="8">
        <div class="profile-card">
          <div class="profile-avatar">
            <span>{{ (auth.user?.username || '?')[0].toUpperCase() }}</span>
          </div>
          <div class="profile-name">{{ auth.user?.username }}</div>
          <el-tag :type="auth.user?.role === 'admin' ? 'danger' : 'primary'" effect="dark" round>
            {{ auth.user?.role === 'admin' ? '管理员' : '普通用户' }}
          </el-tag>
          <div class="profile-stats">
            <div class="profile-stat">
              <div class="profile-stat-value">-</div>
              <div class="profile-stat-label">问答次数</div>
            </div>
            <div class="profile-stat">
              <div class="profile-stat-value">-</div>
              <div class="profile-stat-label">文档数量</div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 修改密码 -->
      <el-col :span="16">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title">修改密码</span>
          </div>
          <div style="padding:24px;max-width:400px">
            <el-form label-width="80px">
              <el-form-item label="用户名">
                <el-input :value="auth.user?.username" disabled />
              </el-form-item>
              <el-form-item label="角色">
                <el-tag :type="auth.user?.role === 'admin' ? 'danger' : 'primary'" effect="dark" round>
                  {{ auth.user?.role === 'admin' ? '管理员' : '普通用户' }}
                </el-tag>
              </el-form-item>
              <el-divider />
              <el-form-item label="原密码">
                <el-input v-model="form.old_password" type="password" placeholder="请输入原密码" show-password />
              </el-form-item>
              <el-form-item label="新密码">
                <el-input v-model="form.new_password" type="password" placeholder="请输入新密码（至少6位）" show-password />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleChangePassword" style="width:100%">
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
  if (!form.value.old_password || !form.value.new_password) {
    return ElMessage.warning('请填写完整')
  }
  if (form.value.new_password.length < 6) {
    return ElMessage.warning('新密码至少6位')
  }
  try {
    await changePassword(form.value)
    ElMessage.success('密码修改成功')
    form.value = { old_password: '', new_password: '' }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '修改失败')
  }
}
</script>

<style scoped>
.profile-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  border: 1px solid #f0f0f0;
  padding: 32px 24px;
  text-align: center;
}
.profile-avatar {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}
.profile-name {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}
.profile-stats {
  display: flex;
  gap: 24px;
  justify-content: center;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}
.profile-stat {
  text-align: center;
}
.profile-stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}
.profile-stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

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
}
.panel-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}
</style>
