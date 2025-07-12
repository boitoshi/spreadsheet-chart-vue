<!-- filepath: frontend/src/components/PortfolioDashboard.vue -->
<template>
  <div class="portfolio-dashboard">
    <h1>📊 ポートフォリオダッシュボード</h1>
    
    <!-- サマリーカード -->
    <div v-if="portfolioSummary" class="summary-cards">
      <div class="summary-card">
        <h3>総評価額</h3>
        <p class="amount">{{ formatCurrency(portfolioSummary.totalCurrent) }}</p>
      </div>
      <div class="summary-card">
        <h3>総損益</h3>
        <p :class="['amount', portfolioSummary.totalProfitLoss >= 0 ? 'profit' : 'loss']">
          {{ formatCurrency(portfolioSummary.totalProfitLoss) }}
        </p>
      </div>
      <div class="summary-card">
        <h3>損益率</h3>
        <p :class="['rate', portfolioSummary.totalProfitLoss >= 0 ? 'profit' : 'loss']">
          {{ portfolioSummary.totalProfitLossRate.toFixed(2) }}%
        </p>
      </div>
    </div>
    
    <!-- 保有銘柄一覧 -->
    <div class="holdings-table">
      <h2>💼 保有銘柄</h2>
      <table v-if="holdingsWithCalc.length">
        <thead>
          <tr>
            <th>銘柄</th>
            <th>保有数</th>
            <th>取得価格</th>
            <th>現在価格</th>
            <th>評価額</th>
            <th>損益</th>
            <th>損益率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="holding in holdingsWithCalc" :key="holding.stock">
            <td>{{ holding.stock }}</td>
            <td>{{ holding.quantity }}</td>
            <td>{{ formatCurrency(holding.purchasePrice) }}</td>
            <td>{{ formatCurrency(holding.currentPrice) }}</td>
            <td>{{ formatCurrency(holding.totalCurrent) }}</td>
            <td :class="holding.profitLoss >= 0 ? 'profit' : 'loss'">
              {{ formatCurrency(holding.profitLoss) }}
            </td>
            <td :class="holding.profitLoss >= 0 ? 'profit' : 'loss'">
              {{ holding.profitLossRate.toFixed(2) }}%
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- ローディング・エラー表示 -->
    <div v-if="loading" class="loading">📈 データ読み込み中...</div>
    <div v-if="error" class="error">❌ エラー: {{ error }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// composableを使わずに直接定義
const loading = ref(false)
const error = ref(null)
const holdings = ref([])

// 計算ロジックを直接定義
const holdingsWithCalc = computed(() => {
  return holdings.value.map(holding => {
    const totalPurchase = holding.purchasePrice * holding.quantity
    const totalCurrent = holding.currentPrice * holding.quantity
    const profitLoss = totalCurrent - totalPurchase
    const profitLossRate = ((profitLoss / totalPurchase) * 100)
    
    return {
      ...holding,
      totalPurchase,
      totalCurrent,
      profitLoss,
      profitLossRate
    }
  })
})

const portfolioSummary = computed(() => {
  if (!holdings.value.length) return null
  
  const summary = holdingsWithCalc.value.reduce((acc, holding) => {
    acc.totalPurchase += holding.totalPurchase
    acc.totalCurrent += holding.totalCurrent
    acc.totalProfitLoss += holding.profitLoss
    return acc
  }, {
    totalPurchase: 0,
    totalCurrent: 0,
    totalProfitLoss: 0
  })
  
  summary.totalProfitLossRate = (summary.totalProfitLoss / summary.totalPurchase) * 100
  return summary
})

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency: 'JPY'
  }).format(amount)
}

onMounted(() => {
  console.log('PortfolioDashboard mounted - 簡素版')
  // 即座にダミーデータを設定
  holdings.value = [
    { stock: 'トヨタ自動車', quantity: 100, purchasePrice: 2500, currentPrice: 2800 },
    { stock: 'ソフトバンク', quantity: 200, purchasePrice: 1200, currentPrice: 1150 },
    { stock: '任天堂', quantity: 50, purchasePrice: 5600, currentPrice: 6200 },
    { stock: 'DeNA', quantity: 150, purchasePrice: 2100, currentPrice: 2350 }
  ]
  console.log('データ設定完了:', holdings.value)
})
</script>

<style scoped>
.portfolio-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.summary-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: center;
}

.amount {
  font-size: 1.5em;
  font-weight: bold;
  margin: 10px 0;
}

.profit { color: #22c55e; }
.loss { color: #ef4444; }

.holdings-table table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.holdings-table th,
.holdings-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.holdings-table th {
  background-color: #f9fafb;
  font-weight: 600;
}

.loading, .error {
  text-align: center;
  padding: 20px;
  font-size: 1.1em;
}
</style>
