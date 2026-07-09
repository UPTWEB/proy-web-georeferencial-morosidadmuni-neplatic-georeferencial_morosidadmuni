<template>
  <div class="soporte-container">
    <div class="soporte-header">
      <h1>🛠️ Panel de TI y Soporte</h1>
      <p>Gestión del sistema, caché y monitorización de servicios</p>
    </div>

    <div class="grid-dashboard">
      <!-- Tarjeta de Estado del Sistema -->
      <div class="card card-estado">
        <h2>Estado del Sistema</h2>
        <div v-if="loadingEstado" class="loading">Comprobando servicios...</div>
        <div v-else class="servicios-list">
          <div class="servicio-item">
            <span class="servicio-name">PostgreSQL (Base de Datos)</span>
            <span :class="['status-badge', estadoSistema.db_conectado ? 'ok' : 'error']">
              {{ estadoSistema.db_conectado ? 'CONECTADO' : 'ERROR' }}
            </span>
          </div>
          <div class="servicio-item">
            <span class="servicio-name">Redis (Caché y Mensajería)</span>
            <span :class="['status-badge', estadoSistema.redis_conectado ? 'ok' : 'error']">
              {{ estadoSistema.redis_conectado ? 'CONECTADO' : 'ERROR' }}
            </span>
          </div>
          <div class="servicio-item">
            <span class="servicio-name">Latencia de API</span>
            <span class="status-badge info">{{ estadoSistema.tiempo_respuesta_ms }} ms</span>
          </div>
        </div>
        <button @click="cargarEstado" class="btn btn-outline" :disabled="loadingEstado">
          Actualizar Estado
        </button>
      </div>

      <!-- Tarjeta de Gestión de Caché -->
      <div class="card card-cache">
        <h2>Gestión de Caché</h2>
        <p class="desc">
          Si los datos en el dashboard o las rutas de los usuarios no se actualizan, puedes limpiar la caché de Redis manualmente.
        </p>
        <button @click="limpiarCache" class="btn btn-danger" :disabled="limpiandoCache">
          {{ limpiandoCache ? 'Limpiando...' : '🧹 Limpiar Caché General' }}
        </button>
        <div v-if="mensajeCache" class="alert success">{{ mensajeCache }}</div>
      </div>
    </div>

    <!-- Lista de Usuarios -->
    <div class="card card-usuarios">
      <h2>Directorio de Usuarios Activos</h2>
      <div v-if="loadingUsuarios" class="loading">Cargando usuarios...</div>
      <table v-else class="table-usuarios">
        <thead>
          <tr>
            <th>ID</th>
            <th>Usuario</th>
            <th>Nombres</th>
            <th>Rol</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in usuarios" :key="user.id_usuario">
            <td>{{ user.id_usuario }}</td>
            <td><strong>{{ user.username }}</strong></td>
            <td>{{ user.nombres }} {{ user.apellidos }}</td>
            <td><span :class="['rol-badge', user.rol_codigo.toLowerCase()]">{{ user.rol_nombre }}</span></td>
            <td>
              <span :class="['estado-badge', user.estado ? 'activo' : 'inactivo']">
                {{ user.estado ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
          </tr>
          <tr v-if="usuarios.length === 0">
            <td colspan="5" class="empty">No se encontraron usuarios.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const estadoSistema = ref({ db_conectado: false, redis_conectado: false, tiempo_respuesta_ms: 0 })
const loadingEstado = ref(true)

const limpiandoCache = ref(false)
const mensajeCache = ref('')

const usuarios = ref([])
const loadingUsuarios = ref(true)

/**
 * Consulta el endpoint de Health Check del backend.
 * Evalúa si PostgreSQL y Redis están en línea y calcula la latencia
 * aproximada de la respuesta de la API.
 */
const cargarEstado = async () => {
  loadingEstado.value = true
  try {
    const res = await api.get('/soporte/estado')
    estadoSistema.value = res.data.data
  } catch (err) {
    console.error('Error cargando estado:', err)
  } finally {
    loadingEstado.value = false
  }
}

/**
 * Solicita al backend la purga manual de la base de datos Redis.
 * Es crítico cuando los usuarios (App C# o Web) modificaron datos masivos y 
 * la caché quedó desincronizada.
 */
const limpiarCache = async () => {
  if (!confirm('¿Estás seguro de limpiar la caché? Esto borrará las ubicaciones guardadas y forzará la recarga de datos para todos los usuarios.')) return
  
  limpiandoCache.value = true
  mensajeCache.value = ''
  try {
    const res = await api.post('/soporte/limpiar-cache')
    mensajeCache.value = res.data.message
    setTimeout(() => { mensajeCache.value = '' }, 5000)
  } catch (err) {
    console.error('Error limpiando caché:', err)
    alert('Error al limpiar caché')
  } finally {
    limpiandoCache.value = false
  }
}

/**
 * Extrae la lista completa de usuarios del sistema desde PostgreSQL.
 * Este listado se utiliza únicamente con fines de auditoría por TI/Soporte.
 */
const cargarUsuarios = async () => {
  loadingUsuarios.value = true
  try {
    const res = await api.get('/soporte/usuarios')
    usuarios.value = res.data.data
  } catch (err) {
    console.error('Error cargando usuarios:', err)
  } finally {
    loadingUsuarios.value = false
  }
}

onMounted(() => {
  cargarEstado()
  cargarUsuarios()
})
</script>

<style scoped>
.soporte-container {
  max-width: 1200px;
  margin: 0 auto;
}
.soporte-header {
  margin-bottom: 2rem;
}
.soporte-header h1 {
  color: #1a472a;
}
.grid-dashboard {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}
.card {
  background: white;
  padding: 1.5rem;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}
.card h2 {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: #333;
  border-bottom: 2px solid #f0f0f0;
  padding-bottom: 0.5rem;
}
.servicios-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.servicio-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}
.servicio-name {
  font-weight: 500;
  color: #555;
}
.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: bold;
}
.status-badge.ok { background: #10b981; color: white; }
.status-badge.error { background: #ef4444; color: white; }
.status-badge.info { background: #3b82f6; color: white; }

.btn {
  padding: 0.5rem 1rem;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 500;
  border: none;
  transition: all 0.2s;
}
.btn-outline {
  background: transparent;
  border: 1px solid #1a472a;
  color: #1a472a;
}
.btn-outline:hover { background: #f0fdf4; }
.btn-danger {
  background: #ef4444;
  color: white;
}
.btn-danger:hover { background: #dc2626; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }

.desc {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 1.5rem;
}

.alert {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 5px;
  font-size: 0.9rem;
}
.alert.success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #34d399;
}

.table-usuarios {
  width: 100%;
  border-collapse: collapse;
}
.table-usuarios th, .table-usuarios td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}
.table-usuarios th {
  background: #f8f9fa;
  font-weight: 600;
  color: #444;
}
.rol-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  background: #e2e8f0;
  color: #334155;
}
.rol-badge.admin { background: #fef3c7; color: #92400e; }
.rol-badge.supervisor { background: #e0e7ff; color: #3730a3; }
.rol-badge.normal { background: #d1fae5; color: #065f46; }
.estado-badge {
  font-size: 0.8rem;
  font-weight: 500;
}
.estado-badge.activo { color: #10b981; }
.estado-badge.inactivo { color: #ef4444; }
.empty { text-align: center; color: #888; padding: 2rem; }
</style>
