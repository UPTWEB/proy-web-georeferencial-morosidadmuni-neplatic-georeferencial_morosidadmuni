<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Solucionar problema de iconos de Leaflet con Vite
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
})

const props = defineProps({
  center: {
    type: Object,
    default: () => ({ lat: -18.0111, lng: -70.2528 })
  },
  zoom: {
    type: Number,
    default: 14
  },
  tileUrl: {
    type: String,
    default: import.meta.env.VITE_MAP_TILE_URL
  },
  attribution: {
    type: String,
    default: import.meta.env.VITE_MAP_ATTRIBUTION
  }
})

const emit = defineEmits(['map-ready', 'map-click', 'layer-add', 'layer-remove'])

const mapContainer = ref(null)
let map = null

onMounted(() => {
  if (!mapContainer.value) return

  map = L.map(mapContainer.value).setView([props.center.lat, props.center.lng], props.zoom)

  L.tileLayer(props.tileUrl, {
    attribution: props.attribution
  }).addTo(map)

  map.on('click', (e) => {
    emit('map-click', { lat: e.latlng.lat, lng: e.latlng.lng })
  })

  emit('map-ready', map)
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})

watch(() => props.center, (newCenter) => {
  if (map) {
    map.setView([newCenter.lat, newCenter.lng], props.zoom)
  }
})

// Exponer el mapa para que otros componentes puedan usarlo
defineExpose({ getMap: () => map })
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
  border-radius: 8px;
  z-index: 1;
}
</style>