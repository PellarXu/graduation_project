<template>
  <div class="chart-shell">
    <template v-if="chartType === 'bar'">
      <div class="bar-chart">
        <div v-for="(item, index) in barItems" :key="`${item.name}-${index}`" class="bar-item">
          <div class="bar-track">
            <div class="bar-fill" :style="{ height: `${item.value}%` }"></div>
          </div>
          <div class="bar-name">{{ item.name }}</div>
          <div class="bar-value">{{ item.value }}</div>
        </div>
      </div>
    </template>

    <template v-else>
      <svg viewBox="0 0 360 320" class="radar-svg">
        <g transform="translate(180,160)">
          <polygon
            v-for="level in 4"
            :key="level"
            :points="buildPolygonPoints((level / 4) * 100)"
            class="radar-grid"
          />
          <line
            v-for="(indicator, index) in indicators"
            :key="indicator.name"
            x1="0"
            y1="0"
            :x2="axisPoint(index).x"
            :y2="axisPoint(index).y"
            class="radar-axis"
          />
          <polygon :points="dataPoints" class="radar-data" />
          <text
            v-for="(indicator, index) in indicators"
            :key="indicator.name"
            :x="labelPoint(index).x"
            :y="labelPoint(index).y"
            class="radar-label"
          >
            {{ indicator.name }}
          </text>
        </g>
      </svg>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  option: {
    type: Object,
    required: true,
  },
})

const chartType = computed(() => props.option?.series?.[0]?.type || 'bar')

const barItems = computed(() => {
  const names = props.option?.xAxis?.data || []
  const values = props.option?.series?.[0]?.data || []
  return names.map((name, index) => ({
    name,
    value: Number(values[index] || 0),
  }))
})

const indicators = computed(() => props.option?.radar?.indicator || [])
const radarValues = computed(() => props.option?.series?.[0]?.data?.[0]?.value || [])

const getCoordinate = (index, score) => {
  const angle = ((Math.PI * 2) / Math.max(indicators.value.length, 1)) * index - Math.PI / 2
  const radius = 110 * (Number(score || 0) / 100)
  return {
    x: Math.cos(angle) * radius,
    y: Math.sin(angle) * radius,
  }
}

const buildPolygonPoints = (score) =>
  indicators.value
    .map((_, index) => {
      const point = getCoordinate(index, score)
      return `${point.x},${point.y}`
    })
    .join(' ')

const axisPoint = (index) => getCoordinate(index, 100)
const labelPoint = (index) => getCoordinate(index, 122)

const dataPoints = computed(() =>
  indicators.value
    .map((_, index) => {
      const point = getCoordinate(index, radarValues.value[index] || 0)
      return `${point.x},${point.y}`
    })
    .join(' ')
)
</script>

<style scoped>
.chart-shell {
  width: 100%;
  min-height: 320px;
}

.bar-chart {
  min-height: 320px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(88px, 1fr));
  gap: 14px;
  align-items: end;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.bar-track {
  width: 100%;
  height: 220px;
  border-radius: 18px;
  display: flex;
  align-items: flex-end;
  padding: 10px;
  background: linear-gradient(180deg, #f0f4f8 0%, #d9e2ec 100%);
}

.bar-fill {
  width: 100%;
  border-radius: 14px;
  background: linear-gradient(180deg, #f0bf52 0%, #c98210 100%);
  transition: height 0.3s ease;
}

.bar-name {
  font-size: 12px;
  color: #43566b;
  text-align: center;
  word-break: break-word;
}

.bar-value {
  font-size: 16px;
  font-weight: 700;
  color: #18304b;
}

.radar-svg {
  width: 100%;
  height: 320px;
}

.radar-grid {
  fill: rgba(24, 48, 75, 0.04);
  stroke: rgba(24, 48, 75, 0.15);
}

.radar-axis {
  stroke: rgba(24, 48, 75, 0.15);
}

.radar-data {
  fill: rgba(212, 157, 42, 0.28);
  stroke: #18304b;
  stroke-width: 2;
}

.radar-label {
  fill: #18304b;
  font-size: 14px;
  font-weight: 700;
  text-anchor: middle;
}
</style>
