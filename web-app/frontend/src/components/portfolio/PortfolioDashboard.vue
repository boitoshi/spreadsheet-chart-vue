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
import { onMounted } from 'vue'
import { usePortfolioData } from '../../composables/usePortfolioData.js'

const {
  holdings,
  loading,
  error,
  portfolioSummary,
  holdingsWithCalc,
  fetchPortfolioData
} = usePortfolioData()

/**
 * 通貨フォーマット
 */
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency: 'JPY'
  }).format(amount)
}

onMounted(() => {
  fetchPortfolioData()
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
