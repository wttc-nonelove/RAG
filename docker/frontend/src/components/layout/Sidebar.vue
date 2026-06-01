<template>
  <el-container style="height: 100vh">
    <el-aside :width="isCollapse ? '64px' : '220px'" style="background:#001529;transition:width 0.3s">
      <div class="logo" :style="{ padding: isCollapse ? '16px 8px' : '16px 20px' }">
        <span v-if="!isCollapse" style="color:#fff;font-size:16px;font-weight:bold">RAG 智能问答</span>
        <span v-else style="color:#fff;font-size:18px">R</span>
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
        <el-dropdown @command="handleCommand">
          <span style="cursor:pointer">
            {{ auth.user?.username }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
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
  ChatDotRound, Fold, Expand, ArrowDown
} from '@element-plus/icons-vue'

const router = useRouter()
const auth = useAuthStore()
const isCollapse = ref(false)

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
}
.menu-group {
  padding: 16px 20px 8px;
  font-size: 11px;
  color: #ffffff60;
  text-transform: uppercase;
  letter-spacing: 1px;
}
</style>
