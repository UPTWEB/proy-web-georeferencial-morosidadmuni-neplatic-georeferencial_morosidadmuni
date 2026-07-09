import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import MapaMorosidad from '../views/MapaMorosidad.vue'
import MisRutas from '../views/MisRutas.vue'
import Monitoreo from '../views/Monitoreo.vue'
import Soporte from '../views/Soporte.vue'

const routes = [
  { path: '/login', name: 'Login', component: Login, meta: { requiresAuth: false } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/mapa', name: 'MapaMorosidad', component: MapaMorosidad, meta: { requiresAuth: true } },
  { path: '/mis-rutas', name: 'MisRutas', component: MisRutas, meta: { requiresAuth: true } },
  { path: '/monitoreo', name: 'Monitoreo', component: Monitoreo, meta: { requiresAuth: true } },
  { path: '/soporte', name: 'Soporte', component: Soporte, meta: { requiresAuth: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

/**
 * Guardia de Rutas Global (Global Route Guard)
 * Implementa el Control de Acceso Basado en Roles (RBAC).
 * Redirige a los usuarios dependiendo de su rol ('NORMAL', 'SUPERVISOR', 'TI', 'ADMIN')
 * previniendo que accedan a páginas no autorizadas.
 */
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const usuario = JSON.parse(localStorage.getItem('usuario') || '{}')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    if (usuario.rol === 'NORMAL') next('/mis-rutas')
    else if (usuario.rol === 'SUPERVISOR') next('/monitoreo')
    else if (usuario.rol === 'TI' || usuario.rol === 'SOPORTE') next('/soporte')
    else next('/dashboard')
  } else if (to.meta.requiresAuth && token) {
    if (usuario.rol === 'NORMAL' && (to.path === '/dashboard' || to.path === '/mapa' || to.path === '/monitoreo')) {
      next('/mis-rutas')
    } else if (usuario.rol === 'SUPERVISOR' && to.path !== '/monitoreo') {
      next('/monitoreo')
    } else if (to.path === '/monitoreo' && !['ADMIN', 'SUPERVISOR', 'TI'].includes(usuario.rol)) {
      next('/dashboard')
    } else if (to.path === '/soporte' && !['ADMIN', 'TI', 'SOPORTE'].includes(usuario.rol)) {
      next('/dashboard')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router