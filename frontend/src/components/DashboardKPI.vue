<template>
  <div class="kpi-grid">
    <div v-for="(item, index) in items" :key="index" class="kpi-card" :class="item.type">
      <div class="kpi-icon" v-if="item.icon">
        <i :class="item.icon"></i>
      </div>
      <div class="kpi-content">
        <h3>{{ item.title }}</h3>
        <p class="value">{{ formatValue(item.value, item.format) }}</p>
        <p v-if="item.subtitle" class="subtitle">{{ item.subtitle }}</p>
        <span v-if="item.percentage" class="percentage" :class="{ positive: item.percentage > 0, negative: item.percentage < 0 }">
          {{ item.percentage > 0 ? '+' : '' }}{{ item.percentage }}%
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  items: {
    type: Array,
    required: true,
    validator: (items) => items.every(item => item.title && item.value !== undefined)
  }
})

const formatValue = (value, format = 'number') => {
  if (value === undefined || value === null) return 'N/A'

  switch (format) {
    case 'currency':
      return `S/ ${value.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    case 'percentage':
      return `${value.toFixed(1)}%`
    case 'number':
      return value.toLocaleString('es-PE')
    case 'integer':
      return Math.round(value).toLocaleString('es-PE')
    default:
      return value
  }
}
</script>

<style scoped>
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.kpi-card {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
  overflow: hidden;
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.12);
}

.kpi-card.coactiva {
  border-left: 4px solid #ff0000;
}
.kpi-card.ordinaria {
  border-left: 4px solid #800020;
}
.kpi-card.sin-proceso {
  border-left: 4px solid #0000ff;
}
.kpi-card.warning {
  border-left: 4px solid #ffc107;
}
.kpi-card.success {
  border-left: 4px solid #28a745;
}

.kpi-icon {
  font-size: 2rem;
  color: #1a472a;
  min-width: 48px;
  text-align: center;
}

.kpi-content {
  flex: 1;
}

.kpi-content h3 {
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #6c757d;
  margin-bottom: 0.5rem;
}

.kpi-content .value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1a472a;
  line-height: 1.2;
  margin-bottom: 0.25rem;
}

.kpi-content .subtitle {
  font-size: 0.7rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.kpi-content .percentage {
  position: absolute;
  top: 1rem;
  right: 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.5rem;
  border-radius: 20px;
}

.percentage.positive {
  background: #d4edda;
  color: #155724;
}

.percentage.negative {
  background: #f8d7da;
  color: #721c24;
}

@media (max-width: 768px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  .kpi-content .value {
    font-size: 1.4rem;
  }
}
</style>