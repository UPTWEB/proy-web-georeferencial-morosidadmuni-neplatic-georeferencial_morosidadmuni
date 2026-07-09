<template>
  <div class="rutas-container">
    <h1>Mis Rutas de Notificación</h1>
    
    <div class="header-controls">
      <div class="fecha-selector">
        <label>Fecha:</label>
        <input type="date" v-model="fecha" @change="cargarRuta" />
      </div>
      <div class="sync-info" v-if="ultimaSincronizacion">
        <span class="dot connected"></span> Sincronizado: {{ ultimaSincronizacion }}
      </div>
    </div>

    <!-- Banner de geolocalización -->
    <div v-if="geoEstado === 'solicitando'" class="geo-banner geo-pending">
      📡 Solicitando acceso a tu ubicación... Por favor acepta el permiso en el navegador.
    </div>
    <div v-else-if="geoEstado === 'activo'" class="geo-banner geo-ok">
      ✅ Ubicación activa — tu posición se está enviando en tiempo real.
    </div>
    <div v-else-if="geoEstado === 'denegado'" class="geo-banner geo-error">
      ⚠️ Acceso a ubicación denegado. Ve a la configuración del navegador y activa el permiso de ubicación para este sitio.
    </div>
    <div v-else-if="geoEstado === 'noSoportado'" class="geo-banner geo-error">
      ⚠️ Tu navegador no soporta geolocalización. Usa un navegador moderno (Chrome, Firefox, Edge).
    </div>
    <div v-else-if="geoEstado === 'noHttps'" class="geo-banner geo-error">
      🔒 La geolocalización requiere una conexión segura (HTTPS). Contacta al administrador.
    </div>
    
    <div v-if="loading" class="loading">Cargando datos de ruta...</div>
    
    <div v-else-if="ruta && ruta.estado_ruta !== 'SIN_RUTA'" class="ruta-card">
      <div class="ruta-header">
        <h2>Ruta del {{ formatFecha(ruta.fecha_ruta) }}</h2>
        <span :class="['estado', ruta.estado_ruta.toLowerCase()]">{{ ruta.estado_ruta }}</span>
      </div>
      
      <div class="ruta-stats">
        <div class="stat">
          <span class="label">Total Deudas:</span>
          <span class="value">{{ ruta.total_deudas }}</span>
        </div>
        <div class="stat">
          <span class="label">Atendidas:</span>
          <span class="value">{{ ruta.deudas_atendidas }}</span>
        </div>
        <div class="stat">
          <span class="label">Efectivas:</span>
          <span class="value">{{ ruta.deudas_efectivas }}</span>
        </div>
        <div class="stat">
          <span class="label">Distancia estimada:</span>
          <span class="value">{{ ruta.distancia_estimada_km }} km</span>
        </div>
      </div>
      
      <div class="deudas-list">
        <h3>Deudas a notificar</h3>
        <div v-for="deuda in ruta.deudas" :key="deuda.id_deuda" class="deuda-item">
          <div class="deuda-orden">{{ deuda.orden }}</div>
          <div class="deuda-info">
            <div class="contribuyente">{{ deuda.nombres_contribuyente }} {{ deuda.apellidos_contribuyente }}</div>
            <div class="direccion">📍 {{ deuda.direccion }}</div>
            <div class="detalles-extra">
              <span class="doc">DNI/RUC: {{ deuda.numero_documento || 'No disp.' }}</span>
            </div>
            <div class="monto">Monto: S/ {{ formatNumber(deuda.monto_pendiente) }}</div>
          </div>
          <div :class="['estado-badge', deuda.estado_cobranza.toLowerCase()]">
            {{ deuda.estado_cobranza }}
          </div>
          <div class="botones-deuda">
            <button v-if="!deuda.fue_visitado" class="btn-notificar" @click="abrirModalNotificar(deuda)">
              Notificar Visita
            </button>
            <button class="btn-navegar" @click="abrirNavegacion(deuda)">
              📍 Navegar
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="sin-ruta">
      <div class="icon-empty">📭</div>
      <h3>No tienes ruta asignada para esta fecha</h3>
      <p>Las rutas de notificación son generadas y asignadas desde la <b>Aplicación de Escritorio</b> del sistema NEPLATIC.</p>
      <p class="text-muted">Si crees que esto es un error, por favor comunícate con el administrador del sistema. La información se sincroniza en tiempo real automáticamente.</p>
    </div>

    <!-- Modal Notificar Visita -->
    <div v-if="mostrarModal" class="modal-overlay" @click.self="cerrarModal">
      <div class="modal-content">
        <h3>Registrar Visita</h3>
        <p><strong>Contribuyente:</strong> {{ deudaSeleccionada?.nombres_contribuyente }} {{ deudaSeleccionada?.apellidos_contribuyente }}</p>
        
        <div class="form-group">
          <label>Resultado de Notificación:</label>
          <select v-model="formNotificacion.resultado" required>
            <option value="">Seleccione un resultado</option>
            <option value="NOTIFICADO_TITULAR">Notificado al Titular</option>
            <option value="NOTIFICADO_TERCERO">Notificado a Tercero</option>
            <option value="PUERTA_CERRADA">Puerta Cerrada (Bajo Puerta)</option>
            <option value="RECHAZO_RECEPCION">Rechazo de Recepción</option>
            <option value="DIRECCION_INCORRECTA">Dirección Incorrecta</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>Observaciones:</label>
          <textarea v-model="formNotificacion.observacion" rows="3" placeholder="Opcional..."></textarea>
        </div>
        
        <div class="modal-actions">
          <button class="btn-cancelar" @click="cerrarModal">Cancelar</button>
          <button class="btn-guardar" @click="guardarNotificacion" :disabled="guardando">
            {{ guardando ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const loading = ref(false)
const ruta = ref(null)
const fecha = ref(new Date().toISOString().split('T')[0])
const ultimaSincronizacion = ref('')
const geoEstado = ref('idle') // idle | solicitando | activo | denegado | noSoportado | noHttps

const formatNumber = (num) => {
  return num?.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'
}

const formatFecha = (fechaStr) => {
  return new Date(fechaStr).toLocaleDateString('es-PE')
}

const mostrarModal = ref(false)
const guardando = ref(false)
const deudaSeleccionada = ref(null)
const formNotificacion = ref({
  resultado: '',
  observacion: ''
})

const abrirModalNotificar = (deuda) => {
  deudaSeleccionada.value = deuda
  formNotificacion.value = { resultado: '', observacion: '' }
  mostrarModal.value = true
}

const cerrarModal = () => {
  mostrarModal.value = false
  deudaSeleccionada.value = null
}

/**
 * Envía el resultado de la notificación (ej. Notificado, Ausente) al backend.
 * Cierra el modal y recarga la lista de rutas para mostrar el progreso en tiempo real.
 */
const guardarNotificacion = async () => {
  if (!formNotificacion.value.resultado) {
    alert('Seleccione un resultado de notificación')
    return
  }
  
  guardando.value = true
  try {
    await api.post('/rutas/notificar', {
      id_ruta: ruta.value.id_ruta,
      id_deuda: deudaSeleccionada.value.id_deuda,
      resultado: formNotificacion.value.resultado,
      observacion: formNotificacion.value.observacion
    })
    alert('Notificación registrada exitosamente')
    cerrarModal()
    cargarRuta() // Recargar para ver los cambios
  } catch (error) {
    console.error('Error guardando notificación:', error)
    alert('Hubo un error al guardar la notificación')
  } finally {
    guardando.value = false
  }
}

/**
 * Extrae la latitud y longitud del lote asociado a la deuda y abre
 * una nueva pestaña de Google Maps con la ruta (Directions) desde la posición actual.
 * @param {Object} deuda Objeto de la deuda que incluye las coordenadas del lote.
 */
const abrirNavegacion = (deuda) => {
  const lat = deuda.latitud || deuda.lat;
  const lng = deuda.longitud || deuda.lng;
  
  if (lat && lng) {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`
    window.open(url, '_blank')
  } else {
    alert('Esta deuda no tiene coordenadas geográficas registradas.')
  }
}

/**
 * Descarga las deudas programadas en la fecha seleccionada para el notificador actual.
 * Se alimenta de la respuesta cacheadad por el backend (Redis) para una carga ultrarrápida.
 */
const cargarRuta = async () => {
  loading.value = true
  try {
    const response = await api.get(`/rutas/mis-rutas?fecha=${fecha.value}`)
    ruta.value = response.data.data
    ultimaSincronizacion.value = new Date().toLocaleTimeString('es-PE')
  } catch (error) {
    console.error('Error cargando ruta:', error)
  } finally {
    loading.value = false
  }
}

let geoWatchId = null;

/**
 * Solicita permisos de Geolocalización al navegador e inicia un "watchPosition".
 * Envía la posición del notificador periódicamente al backend (Redis) para
 * alimentar el panel de Monitoreo de los Supervisores/Admins en tiempo real.
 * NOTA: Requiere entorno HTTPS activo en producción.
 */
const iniciarGeolocalizacion = () => {
  // En VPS, la geolocalización requiere HTTPS
  if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
    geoEstado.value = 'noHttps'
    console.warn('[MisRutas] Geolocalización requiere HTTPS en producción')
    return
  }

  if (!navigator.geolocation) {
    geoEstado.value = 'noSoportado'
    return
  }

  geoEstado.value = 'solicitando'

  geoWatchId = navigator.geolocation.watchPosition(
    async (position) => {
      geoEstado.value = 'activo'
      try {
        await api.post('/rutas/ubicacion', {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        })
      } catch (error) {
        console.error('Error enviando ubicación:', error)
      }
    },
    (error) => {
      console.error('Error obteniendo ubicación:', error)
      if (error.code === 1) {
        // PERMISSION_DENIED
        geoEstado.value = 'denegado'
      } else {
        geoEstado.value = 'denegado'
      }
    },
    { enableHighAccuracy: true, maximumAge: 10000, timeout: 10000 }
  )
}

onMounted(() => {
  cargarRuta()
  iniciarGeolocalizacion()
})

import { onBeforeUnmount } from 'vue'

onBeforeUnmount(() => {
  if (geoWatchId !== null && navigator.geolocation) {
    navigator.geolocation.clearWatch(geoWatchId);
  }
})
</script>

<style scoped>
.rutas-container h1 {
  margin-bottom: 1.5rem;
  color: #1a472a;
}
.header-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}
.fecha-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.sync-info {
  font-size: 0.85rem;
  color: #666;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.dot.connected {
  display: inline-block;
  width: 8px;
  height: 8px;
  background-color: #10b981;
  border-radius: 50%;
  box-shadow: 0 0 5px #10b981;
}
.fecha-selector label {
  font-weight: bold;
}
.fecha-selector input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 5px;
}
.ruta-card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  overflow: hidden;
}
.ruta-header {
  background: #1a472a;
  color: white;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.ruta-header .estado {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
}
.estado.planificada { background: #ffc107; color: #333; }
.estado.en_curso { background: #17a2b8; color: white; }
.estado.completada { background: #28a745; color: white; }
.ruta-stats {
  display: flex;
  gap: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}
.stat .label {
  font-size: 0.8rem;
  color: #666;
}
.stat .value {
  font-size: 1.2rem;
  font-weight: bold;
  color: #1a472a;
}
.deudas-list {
  padding: 1rem;
}
.deudas-list h3 {
  margin-bottom: 1rem;
  color: #333;
}
.deuda-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid #eee;
}
.deuda-orden {
  width: 30px;
  height: 30px;
  background: #1a472a;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}
.deuda-info {
  flex: 1;
}
.contribuyente {
  font-weight: bold;
  color: #333;
}
.direccion {
  font-size: 0.85rem;
  color: #555;
  margin-top: 0.2rem;
}
.detalles-extra {
  font-size: 0.75rem;
  color: #888;
  margin-top: 0.2rem;
  margin-bottom: 0.2rem;
}
.monto {
  font-size: 0.9rem;
  color: #1a472a;
  font-weight: bold;
}
.estado-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: bold;
}
.estado-badge.coactiva { background: #ff0000; color: white; }
.estado-badge.ordinaria { background: #800020; color: white; }
.estado-badge.sin_proceso { background: #0000ff; color: white; }
.visitado-badge {
  background: #28a745;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
}

/* Geo banner */
.geo-banner {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  font-weight: 500;
}
.geo-pending {
  background: #fef3c7;
  border: 1px solid #fcd34d;
  color: #92400e;
}
.geo-ok {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
}
.geo-error {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #b91c1c;
}
.sin-ruta {
  text-align: center;
  padding: 4rem 2rem;
  background: white;
  border-radius: 10px;
  color: #333;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}
.icon-empty {
  font-size: 3rem;
  margin-bottom: 1rem;
}
.text-muted {
  color: #888;
  font-size: 0.9rem;
  max-width: 600px;
  margin: 0 auto;
}
.loading {
  text-align: center;
  padding: 2rem;
}
.btn-notificar {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
}
.btn-notificar:hover {
  background: #1d4ed8;
}
.botones-deuda {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 120px;
}
.btn-navegar {
  background: #10b981;
  color: white;
  border: none;
  padding: 0.5rem;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  text-align: center;
}
.btn-navegar:hover {
  background: #059669;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 10px;
  width: 90%;
  max-width: 450px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.modal-content h3 {
  margin-top: 0;
  color: #1a472a;
}
.form-group {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
}
.form-group label {
  font-weight: bold;
  margin-bottom: 0.5rem;
}
.form-group select, .form-group textarea {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-family: inherit;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}
.btn-cancelar {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  cursor: pointer;
}
.btn-cancelar:hover {
  background: #e2e8f0;
}
.btn-guardar {
  background: #10b981;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
}
.btn-guardar:hover:not(:disabled) {
  background: #059669;
}
.btn-guardar:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
</style>