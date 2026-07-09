<template>
  <div class="mapa-container">
    <h1>Análisis Topológico y de Rutas (ArcGIS + Google Maps)</h1>
    
    <div class="controls-panel">
      <div class="routing-box">
        <h3>Calcular Ruta Óptima (Google Maps)</h3>
        <p class="help-text">Haz clic en el mapa para establecer el Origen y luego el Destino.</p>
        <div class="route-info">
          <div><b>Origen:</b> {{ origenLatLng || 'Selecciona en el mapa' }}</div>
          <div><b>Destino:</b> {{ destinoLatLng || 'Selecciona en el mapa' }}</div>
        </div>
        <div class="route-actions">
          <button @click="calcularRuta" :disabled="!origen || !destino || calculando" class="btn">
            {{ calculando ? 'Calculando...' : 'Dibujar Ruta' }}
          </button>
          <button @click="limpiarRuta" class="btn btn-secondary">Limpiar</button>
        </div>
        <div v-if="rutaError" class="error-msg">{{ rutaError }}</div>
      </div>
      <div class="legend-box">
        <h3>Leyenda y Filtros</h3>
        <div class="filter-hint">Haz clic para mostrar/ocultar capas</div>
        <div
          class="legend-item filter-btn"
          :class="{ active: filtros.coactiva, inactive: !filtros.coactiva }"
          @click="toggleFiltro('coactiva')"
        >
          <span class="color-dot" style="background:rgba(220,0,0,0.85)"></span>
          Deuda Coactiva
          <span class="filter-icon">{{ filtros.coactiva ? '👁' : '🚫' }}</span>
        </div>
        <div
          class="legend-item filter-btn"
          :class="{ active: filtros.ordinaria, inactive: !filtros.ordinaria }"
          @click="toggleFiltro('ordinaria')"
        >
          <span class="color-dot" style="background:rgba(90,0,20,0.85)"></span>
          Deuda Ordinaria
          <span class="filter-icon">{{ filtros.ordinaria ? '👁' : '🚫' }}</span>
        </div>
        <div
          class="legend-item filter-btn"
          :class="{ active: filtros.sinProceso, inactive: !filtros.sinProceso }"
          @click="toggleFiltro('sinProceso')"
        >
          <span class="color-dot" style="background:rgba(0,0,220,0.85)"></span>
          Sin Proceso
          <span class="filter-icon">{{ filtros.sinProceso ? '👁' : '🚫' }}</span>
        </div>
        <hr style="margin: 0.5rem 0; border: none; border-top: 1px solid #eee;">
        <div class="legend-item"><span class="color-dot" style="background:#00FF00"></span> Origen Ruta</div>
        <div class="legend-item"><span class="color-dot" style="background:#FF0000; border-radius:0;"></span> Destino Ruta</div>
        <div class="legend-item"><span class="color-line"></span> Ruta Óptima</div>
      </div>
    </div>

    <div v-if="cargando" class="loading">Cargando motor geográfico...</div>
    <div ref="mapContainer" class="map" :class="{ 'cursor-crosshair': modoSeleccion }"></div>

    <!-- Modal Notificación -->
    <div v-if="showModal" class="modal-backdrop">
      <div class="modal-content">
        <h2>Registrar Notificación</h2>
        <p><b>Lote:</b> {{ selectedLote?.ObjectID }}</p>
        <p><b>Estado Actual:</b> {{ selectedLote?.estado }}</p>
        <div class="form-group">
          <label>Resultado de visita:</label>
          <select v-model="formNotificacion.estado">
            <option value="1">Notificado</option>
            <option value="2">Ausente</option>
            <option value="3">Se mudó</option>
            <option value="4">Fallecido</option>
            <option value="5">Dirección incorrecta</option>
          </select>
        </div>
        <div class="form-group">
          <label>Observaciones:</label>
          <textarea v-model="formNotificacion.observaciones" rows="3"></textarea>
        </div>
        <div class="modal-actions">
          <button @click="guardarNotificacion" class="btn" :disabled="guardando">
            {{ guardando ? 'Guardando...' : 'Guardar' }}
          </button>
          <button @click="showModal = false" class="btn btn-secondary" :disabled="guardando">Cancelar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'

export default {
  name: 'MapaMorosidad',
  data() {
    return {
      cargando: true,
      calculando: false,
      puntosCalor: [],
      
      // Routing state
      modoSeleccion: true,
      origen: null,
      destino: null,
      origenLatLng: '',
      destinoLatLng: '',
      rutaError: '',
      
      // Notificacion state
      showModal: false,
      selectedLote: null,
      guardando: false,
      formNotificacion: {
        estado: '1',
        observaciones: ''
      },

      // Filtros de capas
      filtros: {
        coactiva: true,
        ordinaria: true,
        sinProceso: true
      }
    }
  },
  created() {
    this.view = null;
    this.routeLayer = null;
    this.markersLayer = null;
    this.directionsService = null;
    // Referencias a las capas ArcGIS para poder ocultarlas/mostrarlas
    this._layerCoactiva = null;
    this._layerOrdinaria = null;
    this._layerSinProceso = null;
  },
  async mounted() {
    // Cargar Google Maps dinámicamente con la API Key de Vite
    await this.cargarGoogleMapsScript();
    if (window.google && window.google.maps) {
      this.directionsService = new window.google.maps.DirectionsService();
    } else {
      this.rutaError = "Google Maps no disponible. Verifica VITE_GOOGLE_MAPS_API_KEY en .env";
    }
    await this.cargarHeatmapData();
  },
  beforeUnmount() {
    if (this.view) {
      this.view.destroy()
    }
  },
  methods: {
    /**
     * Inyecta dinámicamente el script de Google Maps API en el documento HTML.
     * Es necesario para habilitar el servicio de enrutamiento (DirectionsService)
     * sin sobrecargar la carga inicial de la aplicación.
     * @returns {Promise} Se resuelve cuando el script carga exitosamente.
     */
    cargarGoogleMapsScript() {
      return new Promise((resolve) => {
        if (window.google && window.google.maps) { resolve(); return; }
        const existing = document.getElementById('google-maps-script');
        if (existing) { existing.addEventListener('load', resolve); existing.addEventListener('error', resolve); return; }
        const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
        if (!apiKey) { resolve(); return; }
        const script = document.createElement('script');
        script.id = 'google-maps-script';
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}`;
        script.async = true;
        script.defer = true;
        script.onload = resolve;
        script.onerror = resolve;
        document.head.appendChild(script);
      });
    },

    /**
     * Activa o desactiva la visibilidad de una capa de deuda en el mapa (ArcGIS).
     * @param {string} tipo Identificador del filtro ('coactiva', 'ordinaria', 'sinProceso')
     */
    toggleFiltro(tipo) {
      this.filtros[tipo] = !this.filtros[tipo];
      if (tipo === 'coactiva' && this._layerCoactiva) {
        this._layerCoactiva.visible = this.filtros.coactiva;
      } else if (tipo === 'ordinaria' && this._layerOrdinaria) {
        this._layerOrdinaria.visible = this.filtros.ordinaria;
      } else if (tipo === 'sinProceso' && this._layerSinProceso) {
        this._layerSinProceso.visible = this.filtros.sinProceso;
      }
    },

    /**
     * Realiza una petición GET al backend para obtener los datos agregados
     * de lotes con deuda y poder graficarlos como un mapa de calor (heatmap).
     */
    async cargarHeatmapData() {
      try {
        const response = await api.get('/mapa/heatmap')
        if (response.data && response.data.success && Array.isArray(response.data.data)) {
          this.puntosCalor = response.data.data
          this.inicializarMapa()
        } else {
          this.cargando = false
        }
      } catch (error) {
        console.error('Error cargando heatmap:', error)
        this.cargando = false
      }
    },
    /**
     * Inicializa el visor geográfico utilizando ArcGIS API for JavaScript.
     * Convierte los puntos de calor en "Graphics" y configura Renderizadores (HeatmapRenderer)
     * específicos para diferenciar visualmente los estados de deuda mediante colores.
     */
    inicializarMapa() {
      window.require([
        "esri/Map",
        "esri/views/MapView",
        "esri/Graphic",
        "esri/layers/GraphicsLayer",
        "esri/layers/FeatureLayer",
        "esri/symbols/SimpleMarkerSymbol",
        "esri/symbols/SimpleLineSymbol"
      ], (Map, MapView, Graphic, GraphicsLayer, FeatureLayer, SimpleMarkerSymbol, SimpleLineSymbol) => {
        
        const map = new Map({
          basemap: "dark-gray-vector" // Fondo oscuro para resaltar el heatmap
        });

        this.view = new MapView({
          container: this.$refs.mapContainer,
          map: map,
          center: [-70.2528, -18.0111], // Lng, Lat por defecto
          zoom: 14
        });

        this.routeLayer = new GraphicsLayer();
        this.markersLayer = new GraphicsLayer();
        
        // Convertir datos REST a Graphics de ArcGIS
        const graphics = this.puntosCalor.map(punto => {
          const estado = punto.estado_predominante || punto.estado || "";
          
          // Asignar un "peso térmico" para que el color represente el estado en el mapa de calor
          let pesoTermico = 10; // Azul (base baja)
          if (estado.includes("Coactiva")) {
            pesoTermico = 100; // Rojo (tope máximo)
          } else if (estado.includes("Ordinaria")) {
            pesoTermico = 60;  // Guinda (rango medio alto, para que no salte a rojo tan fácilmente)
          }

          return new Graphic({
            geometry: {
              type: "point",
              longitude: parseFloat(punto.longitud),
              latitude: parseFloat(punto.latitud)
            },
            attributes: {
              ObjectID: punto.id_lote,
              pesoTermico: pesoTermico,
              estado: estado,
              deuda_real: parseFloat(punto.intensidad)
            }
          });
        });

        // Separar graphics por estado
        const gCoactiva = graphics.filter(g => g.attributes.estado === "Cobranza Coactiva" || g.attributes.estado === "Coactiva");
        const gOrdinaria = graphics.filter(g => g.attributes.estado === "Cobranza Ordinaria" || g.attributes.estado === "Ordinaria");
        const gSinProceso = graphics.filter(g => g.attributes.estado === "Sin proceso" || g.attributes.estado === "Sin Proceso");

        const blurRadius = 20; // Difuminado amplio para mezclar suavemente
        const maxPixelIntensity = 30; // Un valor moderado para crear nubes difusas, no sólidos duros
        const minPixelIntensity = 0;

        // Renderizadores independientes: cada estado tiene SOLO su color
        const renderCoactiva = {
          type: "heatmap",
          colorStops: [
            { ratio: 0, color: "rgba(220, 0, 0, 0)" },
            { ratio: 0.5, color: "rgba(220, 0, 0, 0.7)" },
            { ratio: 1, color: "rgba(220, 0, 0, 1)" }
          ],
          blurRadius, maxPixelIntensity, minPixelIntensity
        };

        const renderOrdinaria = {
          type: "heatmap",
          colorStops: [
            { ratio: 0, color: "rgba(90, 0, 20, 0)" }, // Guinda más oscuro y profundo
            { ratio: 0.5, color: "rgba(90, 0, 20, 0.7)" },
            { ratio: 1, color: "rgba(90, 0, 20, 1)" }
          ],
          blurRadius, maxPixelIntensity, minPixelIntensity
        };

        const renderSinProceso = {
          type: "heatmap",
          colorStops: [
            { ratio: 0, color: "rgba(0, 0, 255, 0)" },
            { ratio: 0.5, color: "rgba(0, 0, 255, 0.7)" },
            { ratio: 1, color: "rgba(0, 0, 255, 1)" }
          ],
          blurRadius, maxPixelIntensity, minPixelIntensity
        };

        const popupTemplate = {
          title: "Lote: {ObjectID}",
          content: "<b>Estado:</b> {estado}<br><b>Deuda Pendiente:</b> S/ {deuda_real}",
          actions: [{
            title: "Registrar Notificación",
            id: "registrar-notificacion",
            className: "esri-icon-edit"
          }]
        };

        // blendMode: "screen" es el correcto para fondos oscuros. 
        // Suma la luz de los colores en vez de oscurecerlos, evitando el color negro y creando un brillo estilo neón o fuego al mezclarse.
        const layerSinProceso = new FeatureLayer({
          source: gSinProceso,
          objectIdField: "ObjectID",
          fields: [{ name: "ObjectID", type: "oid" }, { name: "estado", type: "string" }, { name: "deuda_real", type: "double" }],
          renderer: renderSinProceso,
          title: "Sin Proceso",
          popupTemplate,
          blendMode: "normal",
          visible: this.filtros.sinProceso
        });
        this._layerSinProceso = layerSinProceso;

        const layerOrdinaria = new FeatureLayer({
          source: gOrdinaria,
          objectIdField: "ObjectID",
          fields: [{ name: "ObjectID", type: "oid" }, { name: "estado", type: "string" }, { name: "deuda_real", type: "double" }],
          renderer: renderOrdinaria,
          title: "Deuda Ordinaria",
          popupTemplate,
          blendMode: "normal",
          visible: this.filtros.ordinaria
        });
        this._layerOrdinaria = layerOrdinaria;

        const layerCoactiva = new FeatureLayer({
          source: gCoactiva,
          objectIdField: "ObjectID",
          fields: [{ name: "ObjectID", type: "oid" }, { name: "estado", type: "string" }, { name: "deuda_real", type: "double" }],
          renderer: renderCoactiva,
          title: "Deuda Coactiva",
          popupTemplate,
          blendMode: "normal",
          visible: this.filtros.coactiva
        });
        this._layerCoactiva = layerCoactiva;

        map.addMany([layerSinProceso, layerOrdinaria, layerCoactiva, this.routeLayer, this.markersLayer]);

        // Configurar el click para capturar Origen y Destino de rutas
        this.view.on("click", (event) => {
          const lat = event.mapPoint.latitude;
          const lon = event.mapPoint.longitude;
          
          if (!this.origen) {
            this.origen = { lat, lng: lon };
            this.origenLatLng = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
            this.dibujarMarcador(lon, lat, [0, 255, 0], "Origen");
          } else if (!this.destino) {
            this.destino = { lat, lng: lon };
            this.destinoLatLng = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
            this.dibujarMarcador(lon, lat, [255, 0, 0], "Destino");
          } else {
            // Reiniciar si ambos existen
            this.limpiarRuta();
            this.origen = { lat, lng: lon };
            this.origenLatLng = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
            this.dibujarMarcador(lon, lat, [0, 255, 0], "Origen");
          }
        });

        this.view.popup.on("trigger-action", (event) => {
          if (event.action.id === "registrar-notificacion") {
            const attributes = this.view.popup.selectedFeature.attributes;
            this.selectedLote = attributes;
            this.formNotificacion.estado = '1';
            this.formNotificacion.observaciones = '';
            this.showModal = true;
          }
        });

        // Exponer funciones necesarias al scope de Vue para creación de elementos
        this._createGraphic = Graphic;
        this._createMarker = SimpleMarkerSymbol;
        this._createLine = SimpleLineSymbol;

        this.view.when(() => {
          if (graphics.length > 0) this.view.goTo(graphics).catch(()=>{});
          this.cargando = false;
        });
      });
    },
    dibujarMarcador(lon, lat, color, titulo) {
      if (!this.markersLayer || !this._createGraphic) return;
      
      const symbol = new this._createMarker({
        color: color,
        outline: { color: [255, 255, 255], width: 2 }
      });
      
      const graphic = new this._createGraphic({
        geometry: { type: "point", longitude: lon, latitude: lat },
        symbol: symbol,
        attributes: { name: titulo },
        popupTemplate: { title: "{name}" }
      });
      
      this.markersLayer.add(graphic);
    },
    /**
     * Consulta la API de Google Maps Directions para trazar la ruta óptima
     * en vehículo (DRIVING) entre los puntos de Origen y Destino seleccionados por el usuario.
     */
    calcularRuta() {
      if (!this.directionsService || !this.origen || !this.destino) return;
      
      this.calculando = true;
      this.rutaError = '';
      this.routeLayer.removeAll();

      const request = {
        origin: this.origen,
        destination: this.destino,
        travelMode: 'DRIVING' // DRIVING evita desvíos irregulares de zonas peatonales no mapeadas correctamente
      };

      this.directionsService.route(request, (response, status) => {
        this.calculando = false;
        if (status === 'OK') {
          // Extraer la polyline y decodificar a [lng, lat] para ArcGIS
          const path = response.routes[0].overview_path;
          const arcgisPath = path.map(point => [point.lng(), point.lat()]);
          
          this.dibujarLineaArcGIS(arcgisPath);
        } else {
          this.rutaError = 'No se pudo calcular la ruta: ' + status;
        }
      });
    },
    /**
     * Dibuja una polilínea sobre el mapa base de ArcGIS usando las coordenadas
     * devueltas previamente por el servicio de Google Maps.
     * @param {Array} paths Array de arrays con pares [lng, lat]
     */
    dibujarLineaArcGIS(paths) {
      if (!this.routeLayer || !this._createGraphic) return;
      
      const lineSymbol = new this._createLine({
        color: [0, 200, 255, 0.9], // Azul brillante ruta Google Maps
        width: 4
      });
      
      const routeGraphic = new this._createGraphic({
        geometry: {
          type: "polyline",
          paths: [paths]
        },
        symbol: lineSymbol
      });
      
      this.routeLayer.add(routeGraphic);
      this.view.goTo(this.routeLayer.graphics);
    },
    limpiarRuta() {
      this.origen = null;
      this.destino = null;
      this.origenLatLng = '';
      this.destinoLatLng = '';
      this.rutaError = '';
      if (this.routeLayer) this.routeLayer.removeAll();
      if (this.markersLayer) this.markersLayer.removeAll();
    },
    /**
     * Envía la notificación y observaciones ingresadas en el popup del mapa al backend,
     * actualizando el estado del lote en la base de datos PostgreSQL.
     */
    async guardarNotificacion() {
      if (!this.selectedLote) return;
      this.guardando = true;
      try {
        const payload = {
          id_lote: this.selectedLote.ObjectID,
          id_estado_notif: parseInt(this.formNotificacion.estado),
          observaciones: this.formNotificacion.observaciones
        };
        await api.post('/notificaciones/registrar', payload);
        alert('Notificación registrada correctamente');
        this.showModal = false;
      } catch (err) {
        console.error('Error guardando notificación', err);
        alert('Error guardando notificación');
      } finally {
        this.guardando = false;
      }
    }
  }
}
</script>

<style scoped>
.mapa-container {
  display: flex;
  flex-direction: column;
}
.mapa-container h1 {
  margin-bottom: 1rem;
  color: #1a472a;
}
.controls-panel {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.routing-box {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
  flex: 1;
}
.routing-box h3 { margin-top: 0; margin-bottom: 0.5rem; color: #333; }
.help-text { font-size: 0.85rem; color: #666; margin-bottom: 0.5rem; }
.route-info {
  display: flex;
  gap: 2rem;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}
.route-actions { display: flex; gap: 0.5rem; }
.btn {
  background: #1a472a;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}
.btn:disabled { background: #ccc; cursor: not-allowed; }
.btn-secondary { background: #6c757d; }
.error-msg { color: #dc3545; font-size: 0.85rem; margin-top: 0.5rem; font-weight: bold; }

/* Modal styles */
.modal-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  width: 400px;
  max-width: 90%;
}
.modal-content h2 {
  margin-top: 0;
}
.form-group {
  margin-bottom: 1rem;
}
.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}
.form-group select, .form-group textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.legend-box {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
  min-width: 220px;
}
.legend-box h3 { margin-top: 0; margin-bottom: 0.25rem; color: #333; font-size: 1rem; }
.filter-hint { font-size: 0.72rem; color: #aaa; margin-bottom: 0.6rem; }
.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
  font-size: 0.85rem;
}
.filter-btn {
  cursor: pointer;
  padding: 0.3rem 0.5rem;
  border-radius: 6px;
  border: 1px solid transparent;
  transition: all 0.18s;
  user-select: none;
  justify-content: space-between;
}
.filter-btn.active {
  background: #f0fdf4;
  border-color: #86efac;
  font-weight: 600;
}
.filter-btn.inactive {
  background: #f9fafb;
  border-color: #e5e7eb;
  opacity: 0.55;
  text-decoration: line-through;
}
.filter-btn:hover {
  transform: translateX(2px);
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}
.filter-icon {
  margin-left: auto;
  font-size: 0.75rem;
}
.color-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.2);
  flex-shrink: 0;
}
.color-line {
  display: inline-block;
  width: 16px;
  height: 4px;
  background: #00c8ff;
}

.map {
  width: 100%;
  height: 600px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  outline: none;
}
.cursor-crosshair { cursor: crosshair !important; }
.loading { text-align: center; padding: 2rem; color: #666; }
</style>