<template>
  <div style="display: none;"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import 'leaflet.heat'

const props = defineProps({
  map: {
    type: Object,
    required: true
  },
  points: {
    type: Array,
    default: () => []
  },
  radius: {
    type: Number,
    default: 25
  },
  blur: {
    type: Number,
    default: 15
  },
  maxZoom: {
    type: Number,
    default: 17
  },
  minOpacity: {
    type: Number,
    default: 0.3
  },
  gradient: {
    type: Object,
    default: () => ({
      0.2: '#0000FF',  // azul (sin proceso)
      0.4: '#800020',  // guinda (ordinaria)
      0.8: '#FF0000',  // rojo (coactiva)
      1.0: '#FF4500'   // naranja (máxima)
    })
  }
})

let heatLayer = null

const addHeatLayer = () => {
  if (!props.map || !props.points.length) return

  // Convertir puntos a formato leaflet.heat: [lat, lng, intensidad]
  const heatData = props.points.map(p => [p.latitud, p.longitud, p.intensidad || 1])

  heatLayer = L.heatLayer(heatData, {
    radius: props.radius,
    blur: props.blur,
    maxZoom: props.maxZoom,
    minOpacity: props.minOpacity,
    gradient: props.gradient
  })

  heatLayer.addTo(props.map)
}

const removeHeatLayer = () => {
  if (heatLayer && props.map) {
    props.map.removeLayer(heatLayer)
    heatLayer = null
  }
}

const updateHeatLayer = () => {
  removeHeatLayer()
  addHeatLayer()
}

watch(() => props.points, () => {
  updateHeatLayer()
}, { deep: true })

watch(() => props.radius, () => updateHeatLayer())
watch(() => props.blur, () => updateHeatLayer())
watch(() => props.maxZoom, () => updateHeatLayer())
watch(() => props.minOpacity, () => updateHeatLayer())
watch(() => props.gradient, () => updateHeatLayer(), { deep: true })

onMounted(() => {
  if (props.map && props.points.length) {
    addHeatLayer()
  }
})

onUnmounted(() => {
  removeHeatLayer()
})
</script>