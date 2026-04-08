<template>
  <el-container class="shell">
    <el-aside width="250px" class="sidebar">
      <div class="brand">
        <div class="brand-mark">简</div>
        <div>
          <div class="brand-title">智能简历筛选系统</div>
          <div class="brand-subtitle">公平筛选 · 可解释匹配</div>
        </div>
      </div>

      <el-menu
        :default-active="route.path"
        class="nav-menu"
        router
        background-color="transparent"
        text-color="#dbe4f0"
        active-text-color="#fff7d6"
      >
        <el-menu-item index="/jobs">岗位管理</el-menu-item>
        <el-menu-item index="/analysis">简历分析</el-menu-item>
        <el-menu-item index="/dashboard">匹配驾驶舱</el-menu-item>
      </el-menu>

      <div class="sidebar-note">
        面向中文招聘场景的结构化筛选平台，支持岗位配置、简历分析与结果可视化展示。
      </div>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div>
          <div class="page-caption">中文招聘场景优先</div>
          <div class="page-title">{{ currentTitle }}</div>
        </div>
      </el-header>
      <el-main class="content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const titleMap = {
  '/jobs': '岗位管理与权重配置',
  '/analysis': '简历解析与模型分析',
  '/dashboard': '岗位匹配与结果可视化',
}

const currentTitle = computed(() => titleMap[route.path] || '智能简历筛选系统')
</script>

<style scoped>
.shell {
  min-height: 100vh;
}

.sidebar {
  background:
    radial-gradient(circle at top, rgba(255, 225, 140, 0.15), transparent 35%),
    linear-gradient(180deg, #18304b 0%, #102336 100%);
  color: #f7fafc;
  padding: 28px 18px 22px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 54px;
  height: 54px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 24px;
  color: #12304d;
  background: linear-gradient(135deg, #f9d55b 0%, #ffdca6 100%);
  box-shadow: 0 12px 22px rgba(0, 0, 0, 0.16);
}

.brand-title {
  font-size: 20px;
  font-weight: 700;
}

.brand-subtitle {
  font-size: 12px;
  color: #bfd0e2;
  margin-top: 4px;
}

.nav-menu {
  border-right: none;
}

.sidebar-note {
  margin-top: auto;
  padding: 14px;
  border-radius: 18px;
  line-height: 1.7;
  font-size: 13px;
  color: #dbe4f0;
  background: rgba(255, 255, 255, 0.08);
}

.topbar {
  min-height: 96px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 28px;
  background: rgba(255, 255, 255, 0.76);
  border-bottom: 1px solid rgba(24, 48, 75, 0.08);
  backdrop-filter: blur(14px);
}

.page-caption {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: #8a5b00;
}

.page-title {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 700;
  color: #18304b;
}

.content {
  padding: 28px;
}
</style>
