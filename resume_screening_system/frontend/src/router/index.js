import { createRouter, createWebHistory } from 'vue-router'

import JobManagementPage from '../pages/JobManagementPage.vue'
import MatchDashboardPage from '../pages/MatchDashboardPage.vue'
import ResumeAnalysisPage from '../pages/ResumeAnalysisPage.vue'

const routes = [
  { path: '/', redirect: '/jobs' },
  { path: '/jobs', component: JobManagementPage },
  { path: '/analysis', component: ResumeAnalysisPage },
  { path: '/dashboard', component: MatchDashboardPage },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
