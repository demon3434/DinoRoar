import { createRouter, createWebHistory } from 'vue-router'
import AdminLayout from '@/components/layout/AdminLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/LoginView.vue')
    },
    {
      path: '/',
      redirect: '/admin/stickers'
    },
    {
      path: '/admin',
      component: AdminLayout,
      redirect: '/admin/stickers',
      children: [
        {
          path: 'users',
          name: 'Users',
          component: () => import('@/views/users/UserListView.vue')
        },
        {
          path: 'stickers',
          name: 'Stickers',
          component: () => import('@/views/stickers/StickerListView.vue')
        },
        {
          path: 'canvases',
          name: 'Canvases',
          component: () => import('@/views/canvases/CanvasListView.vue')
        },
        {
          path: 'promotions',
          name: 'Promotions',
          component: () => import('@/views/promotions/PromotionListView.vue')
        },
        {
          path: 'checkin',
          name: 'Checkin',
          component: () => import('@/views/settings/CheckinConfigView.vue')
        },
        {
          path: 'energy/ledger',
          name: 'EnergyLedger',
          component: () => import('@/views/energy/EnergyLedgerView.vue')
        },
        {
          path: 'maintenance',

          name: 'Maintenance',
          component: () => import('@/views/settings/MaintenanceView.vue')
        },

        {
          path: 'password',
          name: 'Password',
          component: () => import('@/views/settings/PasswordView.vue')
        },
        {
          path: 'theme',
          name: 'Theme',
          component: () => import('@/views/settings/ThemeView.vue')
        },
        {
          path: 'diaries',
          name: 'Diaries',
          component: () => import('@/views/diaries/DiaryListView.vue')
        },
        {
          path: 'persons',
          name: 'Persons',
          component: () => import('@/views/persons/PersonListView.vue')
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/admin/stickers'
    }
  ]
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token') || localStorage.getItem('dinoroar_token')
  if (to.path.startsWith('/admin') && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
