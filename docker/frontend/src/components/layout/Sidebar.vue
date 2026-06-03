<template>
  <el-container style="height: 100vh">
    <el-aside :width="isCollapse ? '64px' : '220px'" style="background:#001529;transition:width 0.3s">
      <div class="logo" :style="{ padding: isCollapse ? '16px 8px' : '16px 20px' }">
        <div class="logo-icon">
          <el-icon :size="isCollapse ? 20 : 24" color="#fff"><ChatDotRound /></el-icon>
        </div>
        <div v-if="!isCollapse" class="logo-text">
          <div class="logo-title">RAG</div>
          <div class="logo-subtitle">智能问答系统</div>
        </div>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="isCollapse"
        background-color="#001529"
        text-color="#ffffffb3"
        active-text-color="#409eff"
        router
      >
        <template v-if="auth.isAdmin">
          <!-- 工作空间 -->
          <div v-if="!isCollapse" class="menu-group">工作空间</div>
          <el-menu-item index="/dashboard">
            <el-icon><Monitor /></el-icon>
            <span>工作台</span>
          </el-menu-item>
          <el-menu-item index="/qa">
            <el-icon><ChatDotRound /></el-icon>
            <span>智能问答</span>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <span>问答历史</span>
          </el-menu-item>

          <!-- 知识管理 -->
          <div v-if="!isCollapse" class="menu-group">知识管理</div>
          <el-menu-item index="/knowledge">
            <el-icon><Document /></el-icon>
            <span>知识库管理</span>
          </el-menu-item>
          <el-menu-item index="/graph">
            <el-icon><Share /></el-icon>
            <span>知识图谱</span>
          </el-menu-item>

          <!-- 系统管理 -->
          <div v-if="!isCollapse" class="menu-group">系统管理</div>
          <el-menu-item index="/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/model">
            <el-icon><Setting /></el-icon>
            <span>模型管理</span>
          </el-menu-item>
          <el-menu-item index="/config">
            <el-icon><Tools /></el-icon>
            <span>系统配置</span>
          </el-menu-item>
        </template>

        <template v-else>
          <div v-if="!isCollapse" class="menu-group">功能</div>
          <el-menu-item index="/qa">
            <el-icon><ChatDotRound /></el-icon>
            <span>智能问答</span>
          </el-menu-item>
          <el-menu-item index="/my-history">
            <el-icon><Clock /></el-icon>
            <span>我的历史</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e8e8e8;background:#fff">
        <el-icon style="cursor:pointer;font-size:20px" @click="isCollapse = !isCollapse">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
        <div style="display:flex;align-items:center;gap:16px">
          <el-tooltip content="全屏" placement="bottom">
            <el-icon style="cursor:pointer;font-size:18px;color:#909399" @click="toggleFullscreen"><FullScreen /></el-icon>
          </el-tooltip>
          <el-dropdown @command="handleCommand">
            <div style="display:flex;align-items:center;gap:10px;cursor:pointer">
              <div class="header-avatar">
                <span v-if="!avatarUrl">{{ (auth.user?.username||'?')[0].toUpperCase() }}</span>
                <img v-else :src="avatarUrl" style="width:100%;height:100%;object-fit:cover;border-radius:50%" />
              </div>
              <span style="font-size:14px;font-weight:500">{{ auth.user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main style="background:#f0f2f5;padding:20px">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import {
  Monitor, Document, Share, User, Clock, Setting, Tools,
  ChatDotRound, Fold, Expand, ArrowDown, FullScreen
} from '@element-plus/icons-vue'

const router = useRouter()
const auth = useAuthStore()
const isCollapse = ref(false)
const avatarUrl = ref('')

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

function toggleFullscreen() {
  const el = document.documentElement
  if (!document.fullscreenElement) {
    if (el.requestFullscreen) el.requestFullscreen()
    else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen()
  } else {
    if (document.exitFullscreen) document.exitFullscreen()
    else if (document.webkitExitFullscreen) document.webkitExitFullscreen()
  }
}

function handleCommand(cmd) {
  if (cmd === 'logout') {
    auth.logout()
    router.push('/login')
  } else if (cmd === 'profile') {
    router.push('/profile')
  }
}
</script>

<style scoped>
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.logo-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 0 rgba(0,0,0,0.2);
}
.logo-text {
  display: flex;
  flex-direction: column;
}
.logo-title {
  color: #fff;
  font-size: 18px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: 1px;
}
.logo-subtitle {
  color: rgba(255,255,255,0.6);
  font-size: 10px;
  margin-top: 2px;
}
.menu-group {
  padding: 16px 20px 8px;
  font-size: 11px;
  color: #ffffff60;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.header-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  overflow: hidden;
  flex-shrink: 0;
}
</style>
