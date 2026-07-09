<template>
  <div class="monitoreo-container">
    <div class="monitoreo-header">
      <h1>🗺️ Monitoreo de Notificadores</h1>
      <p>Ubicación en tiempo real de los notificadores activos en campo.</p>
    </div>

    <!-- Estado del sistema -->
    <div class="status-bar">
      <div class="status-item">
        <span class="dot" :class="mapLoaded ? 'online' : 'loading-dot'"></span>
        {{ mapLoaded ? 'Mapa activo' : 'Cargando mapa...' }}
      </div>
      <div class="status-item">
        <span class="dot" :class="notificadores.length > 0 ? 'online' : 'offline'"></span>
        {{ notificadores.length }} notificador(es) en campo
      </div>
      <div class="status-item update-info">
        🔄 Actualiza cada 10s
        <span v-if="ultimaActualizacion"> · {{ ultimaActualizacion }}</span>
      </div>
    </div>

    <!-- Error de carga del mapa -->
    <div v-if="errorMapa" class="error-banner">
      ⚠️ {{ errorMapa }}
    </div>

    <!-- Spinner de carga inicial -->
    <div v-if="!mapLoaded && !errorMapa" class="loading-overlay">
      <div class="spinner"></div>
      <p>Iniciando Google Maps...</p>
    </div>

    <!-- Mapa -->
    <div class="map-wrapper" :class="{ 'hidden': !mapLoaded }">
      <div id="monitoreo-map" ref="mapRef" class="map-canvas"></div>
    </div>

    <!-- Lista de notificadores activos -->
    <div v-if="mapLoaded" class="notificadores-panel">
      <h3>Notificadores activos</h3>
      <div v-if="notificadores.length === 0" class="empty-state">
        No hay notificadores con ubicación activa en este momento.
      </div>
      <div v-else class="notificadores-list">
        <div
          v-for="n in notificadores"
          :key="n.nombres + n.apellidos"
          class="notificador-card"
          @click="centrarEnNotificador(n)"
        >
          <div class="notificador-avatar">{{ iniciales(n) }}</div>
          <div class="notificador-info">
            <div class="notificador-nombre">{{ n.nombres }} {{ n.apellidos }}</div>
            <div class="notificador-tiempo">
              🕒 Última ubicación: {{ formatTiempo(n.timestamp) }}
            </div>
            <div class="notificador-coords">
              📍 {{ parseFloat(n.lat).toFixed(4) }}, {{ parseFloat(n.lng).toFixed(4) }}
            </div>
          </div>
          <div class="notificador-status online-badge">EN CAMPO</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import api from '../api'

const mapRef = ref(null)
const mapLoaded = ref(false)
const errorMapa = ref('')
const notificadores = ref([])
const ultimaActualizacion = ref('')

// Variables globales para la instancia de Google Maps y temporizador
let map = null
let markers = {}
let intervalId = null

/**
 * Carga dinámica del script de Google Maps usando la variable de entorno de Vite.
 * Inyecta el script en el DOM solo si no existe, previniendo bloqueos en el render inicial.
 * @returns {Promise} Se resuelve cuando Google Maps está listo.
 */
const cargarGoogleMapsScript = () => {
  return new Promise((resolve, reject) => {
    // Si ya está cargado, resolver inmediatamente
    if (window.google && window.google.maps) {
      resolve()
      return
    }

    // Si ya existe el script (cargándose), esperar a que termine
    const existingScript = document.getElementById('google-maps-script')
    if (existingScript) {
      existingScript.addEventListener('load', resolve)
      existingScript.addEventListener('error', reject)
      return
    }

    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY
    if (!apiKey) {
      reject(new Error('VITE_GOOGLE_MAPS_API_KEY no está configurada en el .env'))
      return
    }

    const script = document.createElement('script')
    script.id = 'google-maps-script'
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}`
    script.async = true
    script.defer = true
    script.onload = resolve
    script.onerror = () => reject(new Error('No se pudo cargar Google Maps. Verifica la API Key.'))
    document.head.appendChild(script)
  })
}

/**
 * Inicializa el mapa base de Google Maps, establece estilos personalizados
 * y arranca el ciclo de actualización de ubicaciones de notificadores cada 10 segundos.
 */
const initMap = async () => {
  try {
    await cargarGoogleMapsScript()

    map = new window.google.maps.Map(mapRef.value, {
      center: { lat: -17.9700, lng: -70.2300 },
      zoom: 14,
      mapTypeId: 'roadmap',
      styles: [
        { featureType: 'poi', stylers: [{ visibility: 'off' }] },
        { featureType: 'transit', stylers: [{ visibility: 'simplified' }] }
      ]
    })

    mapLoaded.value = true
    await fetchUbicaciones()
    intervalId = setInterval(fetchUbicaciones, 10000)
  } catch (err) {
    errorMapa.value = err.message || 'Error al inicializar el mapa'
    console.error('[Monitoreo] Error al cargar mapa:', err)
  }
}

/**
 * Realiza un polling (petición periódica) al backend para consultar Redis
 * y obtener las coordenadas GPS más recientes enviadas por los notificadores activos.
 */
const fetchUbicaciones = async () => {
  try {
    const res = await api.get('/rutas/ubicaciones-activas')
    if (res.data.success && res.data.data) {
      notificadores.value = res.data.data
      actualizarMarcadores(res.data.data)
      ultimaActualizacion.value = new Date().toLocaleTimeString('es-PE')
    }
  } catch (error) {
    console.error('[Monitoreo] Error fetching ubicaciones:', error)
  }
}

/**
 * Refresca la capa de marcadores (Markers) en Google Maps.
 * Identifica a los notificadores, mueve su marcador a la nueva posición usando `setPosition`
 * o crea uno nuevo si recién se conectaron. Además, limpia los desconectados.
 * @param {Array} ubicaciones Lista de coordenadas y datos recibidos desde el backend.
 */
const actualizarMarcadores = (ubicaciones) => {
  if (!map || !window.google) return

  const actualizados = new Set()

  ubicaciones.forEach(ub => {
    const key = ub.nombres + ub.apellidos
    actualizados.add(key)

    const latlng = new window.google.maps.LatLng(parseFloat(ub.lat), parseFloat(ub.lng))

    if (markers[key]) {
      markers[key].marker.setPosition(latlng)
      // Actualizar contenido del InfoWindow
      markers[key].infoWindow.setContent(buildInfoContent(ub))
    } else {
      const marker = new window.google.maps.Marker({
        position: latlng,
        map: map,
        title: `${ub.nombres} ${ub.apellidos}`,
        icon: {
          url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png',
          scaledSize: new window.google.maps.Size(36, 36)
        },
        animation: window.google.maps.Animation.DROP
      })

      const infoWindow = new window.google.maps.InfoWindow({
        content: buildInfoContent(ub)
      })

      marker.addListener('click', () => {
        // Cerrar todos los demás InfoWindows
        Object.values(markers).forEach(m => m.infoWindow.close())
        infoWindow.open(map, marker)
      })

      markers[key] = { marker, infoWindow }
    }
  })

  // Borrar marcadores de notificadores que ya no están activos
  Object.keys(markers).forEach(key => {
    if (!actualizados.has(key)) {
      markers[key].marker.setMap(null)
      delete markers[key]
    }
  })
}

const buildInfoContent = (ub) => {
  const tiempo = formatTiempo(ub.timestamp)
  return `
    <div style="font-family: 'Segoe UI', sans-serif; padding: 4px; min-width: 180px;">
      <b style="font-size: 1rem;">👤 ${ub.nombres} ${ub.apellidos}</b>
      <hr style="margin: 6px 0; border: none; border-top: 1px solid #eee;">
      <div style="font-size: 0.85rem; color: #555;">🕒 Última ubicación: <b>${tiempo}</b></div>
      <div style="font-size: 0.85rem; color: #555;">📍 ${parseFloat(ub.lat).toFixed(5)}, ${parseFloat(ub.lng).toFixed(5)}</div>
    </div>
  `
}

/**
 * Realiza un "Pan & Zoom" hacia la ubicación exacta de un notificador seleccionado
 * desde la lista lateral y abre su globo de información (InfoWindow).
 * @param {Object} n Notificador seleccionado
 */
const centrarEnNotificador = (n) => {
  if (!map) return
  const key = n.nombres + n.apellidos
  const latlng = new window.google.maps.LatLng(parseFloat(n.lat), parseFloat(n.lng))
  map.panTo(latlng)
  map.setZoom(16)
  if (markers[key]) {
    Object.values(markers).forEach(m => m.infoWindow.close())
    markers[key].infoWindow.open(map, markers[key].marker)
  }
}

const iniciales = (n) => {
  const a = (n.nombres || '').charAt(0).toUpperCase()
  const b = (n.apellidos || '').charAt(0).toUpperCase()
  return a + b
}

const formatTiempo = (timestamp) => {
  if (!timestamp) return 'Desconocido'
  return new Date(timestamp * 1000).toLocaleTimeString('es-PE')
}

onMounted(() => {
  initMap()
})

onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<style scoped>
.monitoreo-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.monitoreo-header h1 {
  margin-bottom: 0.4rem;
  color: #1a472a;
  font-size: 1.8rem;
}

.monitoreo-header p {
  margin-bottom: 1.2rem;
  color: #666;
}

/* Status bar */
.status-bar {
  display: flex;
  gap: 1.5rem;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  font-size: 0.9rem;
  color: #333;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.update-info {
  margin-left: auto;
  color: #888;
  font-size: 0.8rem;
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot.online { background: #10b981; box-shadow: 0 0 6px #10b981; }
.dot.offline { background: #ef4444; }
.dot.loading-dot {
  background: #f59e0b;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* Error banner */
.error-banner {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #b91c1c;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-weight: 500;
}

/* Loading overlay */
.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  color: #666;
  gap: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #1a472a;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Map */
.map-wrapper {
  background: white;
  padding: 0.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  margin-bottom: 1.5rem;
}

.map-wrapper.hidden { display: none; }

.map-canvas {
  height: 520px;
  width: 100%;
  border-radius: 6px;
}

/* Notificadores panel */
.notificadores-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  padding: 1.25rem;
}

.notificadores-panel h3 {
  margin: 0 0 1rem;
  color: #1a472a;
  font-size: 1.1rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #aaa;
  font-style: italic;
}

.notificadores-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.notificador-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.notificador-card:hover {
  background: #f0fdf4;
  border-color: #1a472a;
  box-shadow: 0 2px 8px rgba(26,71,42,0.12);
  transform: translateY(-1px);
}

.notificador-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1a472a, #2d7a48);
  color: white;
  font-weight: bold;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.notificador-info {
  flex: 1;
}

.notificador-nombre {
  font-weight: 600;
  color: #111;
  margin-bottom: 0.2rem;
}

.notificador-tiempo,
.notificador-coords {
  font-size: 0.78rem;
  color: #666;
}

.online-badge {
  background: #d1fae5;
  color: #065f46;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.25rem 0.6rem;
  border-radius: 20px;
  letter-spacing: 0.05em;
}
</style>
