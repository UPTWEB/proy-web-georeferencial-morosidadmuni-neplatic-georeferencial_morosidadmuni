<template>
  <div id="app">
    <nav v-if="isAuthenticated && $route.path !== '/login'" class="navbar">
      <div class="nav-brand">
        <h2>Neplatic</h2>
        <span>Sistema Georeferencial de Morosidad</span>
      </div>
      <div class="nav-links">
        <router-link v-if="['ADMIN', 'TI'].includes(usuario.rol)" to="/dashboard">Dashboard</router-link>
        <router-link v-if="['ADMIN', 'TI'].includes(usuario.rol)" to="/mapa">Mapa de Calor</router-link>
        <router-link v-if="['ADMIN', 'SUPERVISOR', 'TI'].includes(usuario.rol)" to="/monitoreo">Monitoreo</router-link>
        <router-link v-if="['ADMIN', 'TI', 'SOPORTE'].includes(usuario.rol)" to="/soporte">Soporte TI</router-link>
        <router-link v-if="usuario.rol === 'NORMAL'" to="/mis-rutas">Mis Rutas</router-link>
      </div>
      <div class="nav-user">
        <span>{{ usuario.nombres }} {{ usuario.apellidos }}</span>
        <button @click="logout" class="btn-logout">Cerrar Sesión</button>
      </div>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const token = localStorage.getItem('token')
const usuario = JSON.parse(localStorage.getItem('usuario') || '{}')
const isAuthenticated = computed(() => !!token)

const logout = () => {
  console.log('Cerrando sesión...')  // para depurar
  localStorage.removeItem('token')
  localStorage.removeItem('usuario')
  // Fuerza recarga completa para limpiar estado y evitar datos en caché
  window.location.href = '/login'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f5f5f5;
}

.navbar {
  background: linear-gradient(135deg, #1a472a, #0d2818);
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.nav-brand h2 {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.nav-brand span {
  font-size: 0.8rem;
  opacity: 0.8;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-links a {
  color: white;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.3s;
}

.nav-links a:hover {
  opacity: 0.8;
}

.nav-links a.router-link-active {
  border-bottom: 2px solid #ffd700;
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.btn-logout {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-logout:hover {
  background: rgba(255,255,255,0.3);
}

main {
  padding: 2rem;
}
</style>