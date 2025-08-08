<template>
  <div class="skeleton-container">
    <!-- ポートフォリオサマリー用スケルトン -->
    <div v-if="type === 'summary'" class="skeleton-summary">
      <div class="skeleton-cards">
        <div v-for="i in 3" :key="i" class="skeleton-card">
          <div class="skeleton-text skeleton-title"></div>
          <div class="skeleton-text skeleton-amount"></div>
        </div>
      </div>
    </div>
    
    <!-- テーブル用スケルトン -->
    <div v-if="type === 'table'" class="skeleton-table">
      <div class="skeleton-table-header">
        <div v-for="i in columns" :key="i" class="skeleton-text skeleton-header"></div>
      </div>
      <div v-for="row in rows" :key="row" class="skeleton-table-row">
        <div v-for="col in columns" :key="col" class="skeleton-text skeleton-cell"></div>
      </div>
    </div>
    
    <!-- チャート用スケルトン -->
    <div v-if="type === 'chart'" class="skeleton-chart">
      <div class="skeleton-chart-container">
        <div class="skeleton-chart-bars">
          <div v-for="i in 12" :key="i" class="skeleton-bar" :style="{ height: getRandomHeight() }"></div>
        </div>
        <div class="skeleton-chart-axis">
          <div v-for="i in 6" :key="i" class="skeleton-axis-label"></div>
        </div>
      </div>
    </div>
    
    <!-- テキスト用スケルトン -->
    <div v-if="type === 'text'" class="skeleton-text-block">
      <div v-for="line in lines" :key="line" 
           class="skeleton-text" 
           :style="{ width: line === lines ? '60%' : '100%' }"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'text',
    validator: value => ['summary', 'table', 'chart', 'text'].includes(value)
  },
  rows: {
    type: Number,
    default: 5
  },
  columns: {
    type: Number,
    default: 4
  },
  lines: {
    type: Number,
    default: 3
  }
})

// チャート用のランダムな高さ生成
const getRandomHeight = () => {
  return `${Math.floor(Math.random() * 60) + 20}%`
}
</script>

<style scoped>
/* 基本的なスケルトンアニメーション */
@keyframes skeleton-loading {
  0% {
    background-color: #e5e7eb;
  }
  50% {
    background-color: #f3f4f6;
  }
  100% {
    background-color: #e5e7eb;
  }
}

.skeleton-container {
  width: 100%;
}

.skeleton-text {
  height: 1em;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite ease-in-out;
  border-radius: 4px;
}

/* サマリーカード用スケルトン */
.skeleton-summary {
  margin-bottom: 30px;
}

.skeleton-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.skeleton-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.skeleton-title {
  width: 60%;
  margin-bottom: 15px;
}

.skeleton-amount {
  width: 80%;
  height: 1.8em;
}

/* テーブル用スケルトン */
.skeleton-table {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.skeleton-table-header {
  display: grid;
  grid-template-columns: repeat(var(--columns, 4), 1fr);
  gap: 12px;
  padding: 16px;
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.skeleton-header {
  width: 80%;
  height: 1.2em;
}

.skeleton-table-row {
  display: grid;
  grid-template-columns: repeat(var(--columns, 4), 1fr);
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.skeleton-cell {
  width: 70%;
  height: 1em;
}

/* チャート用スケルトン */
.skeleton-chart {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.skeleton-chart-container {
  height: 300px;
  position: relative;
}

.skeleton-chart-bars {
  display: flex;
  align-items: end;
  justify-content: space-between;
  height: 80%;
  padding: 0 10px;
}

.skeleton-bar {
  width: 6%;
  background: linear-gradient(180deg, #d1d5db 0%, #e5e7eb 100%);
  border-radius: 2px;
  animation: skeleton-loading 1.5s infinite ease-in-out;
}

.skeleton-chart-axis {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  margin-top: 10px;
}

.skeleton-axis-label {
  width: 60px;
  height: 1em;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite ease-in-out;
  border-radius: 4px;
}

/* テキストブロック用スケルトン */
.skeleton-text-block {
  background: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.skeleton-text-block .skeleton-text {
  margin-bottom: 12px;
}

.skeleton-text-block .skeleton-text:last-child {
  margin-bottom: 0;
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
  .skeleton-cards {
    grid-template-columns: 1fr;
  }
  
  .skeleton-table-header,
  .skeleton-table-row {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    padding: 12px;
  }
  
  .skeleton-chart-container {
    height: 250px;
  }
}
</style>