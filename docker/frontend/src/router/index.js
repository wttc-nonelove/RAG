import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../components/layout/Sidebar.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/qa' },
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/admin/Dashboard.vue'), meta: { role: 'admin' } },
      { path: 'knowledge', name: 'Knowledge', component: () => import('../views/admin/Knowledge.vue'), meta: { role: 'admin' } },
      { path: 'graph', name: 'Graph', component: () => import('../views/admin/Graph.vue'), meta: { role: 'admin' } },
      { path: 'users', name: 'Users', component: () => import('../views/admin/Users.vue'), meta: { role: 'admin' } },
      { path: 'history', name: 'History', component: () => import('../views/admin/History.vue'), meta: { role: 'admin' } },
      { path: 'model', name: 'Model', component: () => import('../views/admin/Model.vue'), meta: { role: 'admin' } },
      { path: 'config', name: 'Config', component: () => import('../views/admin/Config.vue'), meta: { role: 'admin' } },
      { path: 'qa', name: 'QA', component: () => import('../views/user/QA.vue') },
      { path: 'my-history', name: 'MyHistory', component: () => import('../views/user/MyHistory.vue') },
      { path: 'profile', name: 'Profile', component: () => import('../views/user/Profile.vue') },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  const user = userStr ? JSON.parse(userStr) : null

  if (to.meta.requiresAuth !== false && !token) {
    return next('/login')
  }

  if (to.path === '/login' && token) {
    return next(user?.role === 'admin' ? '/dashboard' : '/qa')
  }

  if (to.meta.role && user?.role !== to.meta.role) {
    return next('/qa')
  }

  next()
})

export default router
