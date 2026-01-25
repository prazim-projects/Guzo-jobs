// src/router/index.ts
import { createRouter, createWebHistory } from '@ionic/vue-router'
import { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/userStore';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    component: () => import('@/components/bottomTabs.vue'),  // tabs wrapper
    children: [
      { path: '', redirect: '/home' },
      { path: 'home', component: () => import('@/views/HomePage.vue') },
      { path: 'myJobs', component: () => import('@/views/myJobs.vue'), meta: { requiresAuth: true } },
      { path: 'add', component: () => import('@/views/NotePage.vue'), meta: { requiresAuth: true } },
      { path: 'login', component: () => import('@/views/login.vue') },
      { path: 'signup', component: () => import('@/views/register.vue') },
      { path: 'profile', component: () => import('@/views/ProfilePage.vue'), meta: { requiresAuth: true } },
      { path: 'mapET', component: () => import('@/views/MapPage.vue'), meta: { requiresAuth: true } },
      {path: 'logout', component: () => import('@/views/logout.vue'), meta: { requiresAuth: true } },
      {path: 'postJob', component: () => import('@/views/createJobPost.vue'), meta: { requiresAuth: true } },
      {path: 'myJobs', component: () => import('@/views/myJobs.vue'), meta: { requiresAuth: true } },
    ]
  },
  {
    path: '/onboarding',
    component: () => import('@/views/Onboarding.vue')
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const userStore = useAuthStore();
  const isAuthenticated = userStore.isAuthenticated;
  const onboardingCompleted = localStorage.getItem('onboardingCompleted') === 'true';

  // If user hasn't completed onboarding and isn't already on onboarding page
  if (!onboardingCompleted && to.path !== '/onboarding') {
    next({ path: '/onboarding' });
    return;
  }

  // If user completed onboarding and is trying to access onboarding, redirect to home
  if (onboardingCompleted && to.path === '/onboarding') {
    next({ path: '/home' });
    return;
  }

  if (requiresAuth && !isAuthenticated) {
    // Redirect unauthenticated users to login page
    next({ path: '/login' });
  } else {
    next();
  }
});

export default router