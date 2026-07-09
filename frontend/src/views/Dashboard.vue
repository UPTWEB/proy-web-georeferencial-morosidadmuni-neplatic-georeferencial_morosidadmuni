<template>
  <div class="dashboard">
    <h1>Dashboard Gerencial</h1>
    
    <div class="filters-panel">
      <select v-model="filters.anio" @change="fetchData">
        <option :value="currentYear">{{ currentYear }} (Actual)</option>
        <option :value="currentYear - 1">{{ currentYear - 1 }}</option>
        <option :value="currentYear - 2">{{ currentYear - 2 }}</option>
        <option :value="currentYear - 3">{{ currentYear - 3 }}</option>
      </select>
      
      <select v-model="filters.periodo" @change="fetchData">
        <option value="ANUAL">Anual</option>
        <option value="S1">Primer Semestre (S1)</option>
        <option value="S2">Segundo Semestre (S2)</option>
        <option value="T1">Primer Trimestre (T1)</option>
        <option value="T2">Segundo Trimestre (T2)</option>
        <option value="T3">Tercer Trimestre (T3)</option>
        <option value="T4">Cuarto Trimestre (T4)</option>
        <option value="M1">Enero</option>
        <option value="M2">Febrero</option>
        <option value="M3">Marzo</option>
        <option value="M4">Abril</option>
        <option value="M5">Mayo</option>
        <option value="M6">Junio</option>
        <option value="M7">Julio</option>
        <option value="M8">Agosto</option>
        <option value="M9">Septiembre</option>
        <option value="M10">Octubre</option>
        <option value="M11">Noviembre</option>
        <option value="M12">Diciembre</option>
      </select>
    </div>

    <div class="kpi-grid" v-if="kpis">
      <div class="kpi-card">
        <h3>Deuda Total Pendiente</h3>
        <p class="value">S/ {{ formatNumber(kpis.deuda_total_pendiente) }}</p>
      </div>
      <div class="kpi-card coactiva">
        <h3>Deuda Coactiva</h3>
        <p class="value">S/ {{ formatNumber(kpis.deuda_coactiva) }}</p>
        <span class="percentage">{{ kpis.pct_deuda_coactiva }}% del total</span>
      </div>
      <div class="kpi-card">
        <h3>Total Contribuyentes Morosos</h3>
        <p class="value">{{ formatNumber(kpis.total_contribuyentes_morosos) }}</p>
      </div>
      <div class="kpi-card">
        <h3>Tasa de Efectividad</h3>
        <p class="value">{{ kpis.tasa_efectividad_real }}%</p>
      </div>
    </div>

    <div class="charts">
      <div class="chart-container">
        <h3>Evolución de Morosidad</h3>
        <div v-if="!hasEvolucionData" class="empty-state">
          No hay datos históricos de morosidad disponibles
        </div>
        <canvas v-show="hasEvolucionData" ref="evolucionChart"></canvas>
      </div>
      <div class="chart-container">
        <h3>Deuda por Sector</h3>
        <canvas ref="sectorChart"></canvas>
      </div>
      <div class="chart-container">
        <h3>Top 10 Deudores</h3>
        <table class="top-deudores">
          <thead>
            <tr>
              <th>Ranking</th>
              <th>Contribuyente</th>
              <th>DNI/RUC</th>
              <th>Sector</th>
              <th>Deuda Total</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="topDeudores.length === 0">
              <td colspan="6" class="text-center empty-state">Sin datos para los filtros seleccionados</td>
            </tr>
            <tr v-for="d in topDeudores" :key="d.ranking">
              <td>#{{ d.ranking }}</td>
              <td>{{ d.nombres }} {{ d.apellido_paterno }}</td>
              <td>{{ d.numero_documento }}</td>
              <td>{{ d.sectores || '-' }}</td>
              <td class="money">S/ {{ formatNumber(d.deuda_total) }}</td>
              <td>
                <button @click="verDetalle(d)" class="btn-sm">Ver detalle</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, shallowRef } from 'vue'
import Chart from 'chart.js/auto'
import api from '../api'

const kpis = ref(null)
const topDeudores = ref([])
const hasEvolucionData = ref(false)
const evolucionChart = ref(null)
const chartInstance = shallowRef(null)
const sectorChart = ref(null)
const sectorChartInstance = shallowRef(null)

const currentYear = new Date().getFullYear()

const filters = ref({
  anio: currentYear,
  periodo: 'ANUAL'
})

const formatNumber = (num) => {
  return num?.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'
}

const verDetalle = (deudor) => {
  alert(`Detalle del deudor: ${deudor.nombres} ${deudor.apellido_paterno}\nDNI/RUC: ${deudor.numero_documento}\nDeuda: S/ ${formatNumber(deudor.deuda_total)}`)
}

const renderChart = (data) => {
  if (chartInstance.value) {
    chartInstance.value.destroy()
  }

  if (!data || data.length === 0) {
    hasEvolucionData.value = false
    return
  }

  hasEvolucionData.value = true

  const labels = [...new Set(data.map(d => d.mes.substring(0, 7)))]
  
  // Transform data for coactiva vs ordinaria lines
  const coactivaData = labels.map(lbl => {
    const found = data.find(d => d.mes.startsWith(lbl) && d.estado === 'coactiva')
    return found ? parseFloat(found.saldo_total) : 0
  })

  const ordinariaData = labels.map(lbl => {
    const found = data.find(d => d.mes.startsWith(lbl) && d.estado === 'ordinaria')
    return found ? parseFloat(found.saldo_total) : 0
  })

  chartInstance.value = new Chart(evolucionChart.value, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Deuda Coactiva',
          data: coactivaData,
          borderColor: '#ff0000',
          backgroundColor: 'rgba(255, 0, 0, 0.1)',
          fill: true,
          tension: 0.4
        },
        {
          label: 'Deuda Ordinaria',
          data: ordinariaData,
          borderColor: '#800020',
          backgroundColor: 'rgba(128, 0, 32, 0.1)',
          fill: true,
          tension: 0.4
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: (value) => 'S/ ' + formatNumber(value)
          }
        }
      }
    }
  })
}

const fetchEvolucion = async () => {
  try {
    const evoRes = await api.get('/dashboard/evolucion')
    renderChart(evoRes.data.data)
  } catch (err) {
    console.error('Error fetching evolucion:', err)
  }
}

const fetchData = async () => {
  try {
    const query = `?anio=${filters.value.anio}&periodo=${filters.value.periodo}`
    
    // Ejecutar llamadas en paralelo
    const [kpisRes, topDeudoresRes, sectoresRes] = await Promise.all([
      api.get(`/dashboard/kpis${query}`),
      api.get(`/dashboard/top-deudores${query}`),
      api.get(`/mapa/sectores`) // Usamos este endpoint que ya tiene la data agrupada
    ])

    if (kpisRes.data.success) {
      kpis.value = kpisRes.data.data
    }
    if (topDeudoresRes.data.success) {
      topDeudores.value = topDeudoresRes.data.data
    }
    if (sectoresRes.data.success) {
      renderSectorChart(sectoresRes.data.data)
    }

  } catch (error) {
    console.error('Error fetching dashboard data:', error)
  }
}

const renderSectorChart = (sectoresData) => {
  if (!sectorChart.value) return;
  
  if (sectorChartInstance.value) {
    sectorChartInstance.value.destroy();
  }

  const labels = sectoresData.map(s => s.nombre_sector);
  const data = sectoresData.map(s => s.monto_total_pendiente);

  sectorChartInstance.value = new Chart(sectorChart.value, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Deuda Total Pendiente (S/)',
        data: data,
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
}

onMounted(() => {
  fetchEvolucion()
  fetchData()
})
</script>

<style scoped>
.dashboard h1 {
  margin-bottom: 2rem;
  color: #1a472a;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}
.kpi-card {
  background: white;
  padding: 1.5rem;
  border-radius: 10px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  text-align: center;
}
.kpi-card.coactiva {
  border-left: 4px solid #ff0000;
}
.kpi-card h3 {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.5rem;
}
.kpi-card .value {
  font-size: 1.8rem;
  font-weight: bold;
  color: #1a472a;
}
.kpi-card .percentage {
  display: inline-block;
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #ff0000;
}
.charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}
.chart-container {
  background: white;
  padding: 1.5rem;
  border-radius: 10px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.filters-panel {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.filters-panel select {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
  min-width: 200px;
}
.top-deudores {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}
.top-deudores th, .top-deudores td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}
.top-deudores th {
  background: #f5f5f5;
  color: #555;
}
.top-deudores .money {
  font-weight: 600;
  color: #1a472a;
}
.btn-sm {
  padding: 0.25rem 0.5rem;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}
.btn-sm:hover {
  background: #e0e0e0;
}
.empty-state {
  color: #888;
  font-style: italic;
  padding: 1rem;
}
.text-center {
  text-align: center !important;
}
</style>