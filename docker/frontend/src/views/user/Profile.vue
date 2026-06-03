<template>
  <div>
    <div class="clay-hero" style="background:linear-gradient(135deg,#a18cd1,#fbc2eb)">
      <h2 class="clay-hero-title">个人中心</h2>
      <p class="clay-hero-subtitle">管理您的账号信息和安全设置</p>
    </div>

    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="8">
        <div class="clay-card" style="text-align:center;padding:32px 24px">
          <!-- 头像 -->
          <div style="position:relative;display:inline-block;margin-bottom:16px">
            <div class="avatar-wrapper">
              <span v-if="!avatarUrl">{{ (auth.user?.username||'?')[0].toUpperCase() }}</span>
              <img v-else :src="avatarUrl" style="width:100%;height:100%;object-fit:cover;border-radius:20px" />
            </div>
            <div class="avatar-upload" @click="triggerAvatarUpload">
              <el-icon :size="16" color="#fff"><UploadFilled /></el-icon>
            </div>
            <input ref="avatarInput" type="file" accept="image/*" style="display:none" @change="handleAvatarUpload" />
          </div>
          <!-- 用户名 -->
          <div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:8px">
            <div v-if="!editingUsername" style="font-size:20px;font-weight:700;color:#1a1a2e">{{ auth.user?.username }}</div>
            <el-input v-else v-model="newUsername" size="small" style="width:150px" @keyup.enter="saveUsername" @keyup.escape="editingUsername = false" />
            <el-icon v-if="!editingUsername" style="cursor:pointer;color:#909399" @click="startEditUsername"><Edit /></el-icon>
            <template v-else>
              <el-icon style="cursor:pointer;color:#10b981" @click="saveUsername"><Check /></el-icon>
              <el-icon style="cursor:pointer;color:#ef4444" @click="editingUsername = false"><Close /></el-icon>
            </template>
          </div>
          <el-tag :type="auth.user?.role==='admin'?'danger':'primary'" effect="dark" round>{{ auth.user?.role==='admin'?'管理员':'普通用户' }}</el-tag>
          <!-- 统计 -->
          <div style="display:flex;gap:24px;justify-content:center;margin-top:24px;padding-top:24px;border-top:2px solid #f0f0f0">
            <div style="text-align:center">
              <div style="font-size:24px;font-weight:700;color:#667eea">{{ userStats.qa_count }}</div>
              <div style="font-size:12px;color:#909399;margin-top:4px">问答次数</div>
            </div>
            <div style="text-align:center">
              <div style="font-size:24px;font-weight:700;color:#10b981">{{ userStats.doc_count }}</div>
              <div style="font-size:12px;color:#909399;margin-top:4px">文档数量</div>
            </div>
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Lock, Edit, Check, Close, UploadFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { changePassword } from '../../api/auth'
import client from '../../api/client'

const auth = useAuthStore()
const form = ref({ old_password: '', new_password: '' })
const userStats = reactive({ qa_count: 0, doc_count: 0 })

// 用户名编辑
const editingUsername = ref(false)
const newUsername = ref('')

// 头像
const avatarUrl = ref('')
const avatarInput = ref(null)

// 初始化头像
function initAvatar() {
  if (auth.user?.id) {
    const savedAvatar = localStorage.getItem('avatar_' + auth.user.id)
    if (savedAvatar) {
      avatarUrl.value = savedAvatar
    }
  }
}

// 初始化时加载头像
initAvatar()

onMounted(async () => {
  // 加载用户统计
  try {
    const res = await client.get('/auth/stats')
    userStats.qa_count = res.data.qa_count || 0
    userStats.doc_count = res.data.doc_count || 0
  } catch {}
})

function startEditUsername() {
  newUsername.value = auth.user?.username || ''
  editingUsername.value = true
}

async function saveUsername() {
  if (!newUsername.value.trim()) return ElMessage.warning('用户名不能为空')
  if (newUsername.value === auth.user?.username) { editingUsername.value = false; return }
  try {
    const res = await client.put('/auth/username', { username: newUsername.value })
    auth.user.username = res.data.username
    localStorage.setItem('user', JSON.stringify(auth.user))
    editingUsername.value = false
    ElMessage.success('用户名修改成功')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '修改失败')
  }
}

function triggerAvatarUpload() {
  avatarInput.value?.click()
}

function handleAvatarUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) return ElMessage.error('头像大小不能超过 2MB')

  const reader = new FileReader()
  reader.onload = (e) => {
    const avatarData = e.target.result
    avatarUrl.value = avatarData

    // 保存到 localStorage
    try {
      if (auth.user?.id) {
        localStorage.setItem('avatar_' + auth.user.id, avatarData)
        ElMessage.success('头像更新成功')
      } else {
        ElMessage.error('用户信息未加载，无法保存头像')
      }
    } catch (error) {
      console.error('保存头像失败:', error)
      ElMessage.error('头像保存失败，可能存储空间不足')
    }
  }
  reader.onerror = () => {
    ElMessage.error('读取头像文件失败')
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

async function handleChangePassword() {
  if (!form.value.old_password || !form.value.new_password) return ElMessage.warning('请填写完整')
  if (form.value.new_password.length < 6) return ElMessage.warning('新密码至少6位')
  try { await changePassword(form.value); ElMessage.success('密码修改成功'); form.value = { old_password: '', new_password: '' } } catch (e) { ElMessage.error(e.response?.data?.detail || '修改失败') }
}
</script>

<style scoped>
.avatar-wrapper {
  width: 80px; height: 80px; border-radius: 20px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex; align-items: center; justify-content: center;
  font-size: 32px; font-weight: 700; color: #fff;
  border: 3px solid rgba(255,255,255,0.3);
  box-shadow: 0 6px 0 rgba(0,0,0,0.1);
  overflow: hidden;
}
.avatar-upload {
  position: absolute; bottom: -4px; right: -4px;
  width: 28px; height: 28px; border-radius: 8px;
  background: #667eea; display: flex; align-items: center; justify-content: center;
  cursor: pointer; border: 2px solid #fff;
  box-shadow: 0 2px 0 rgba(0,0,0,0.1);
  transition: all 0.2s;
}
.avatar-upload:hover { transform: scale(1.1); background: #764ba2; }
</style>
