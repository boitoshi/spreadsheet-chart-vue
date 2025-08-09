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
            <td>{{ formatCurrency(holding.avgPrice) }}</td>
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
    
    <!-- データ品質ステータス表示 -->
    <div v-if="validationStatus" class="data-quality-status" :class="validationStatus.level">
      <span class="status-icon">{{ validationStatus.icon }}</span>
      <span class="status-message">{{ validationStatus.message }}</span>
      <button v-if="criticalIssues.length > 0" @click="showValidationDetails = !showValidationDetails" 
              class="toggle-details">
        {{ showValidationDetails ? '詳細を隠す' : '詳細を表示' }}
      </button>
    </div>
    
    <!-- 詳細な検証結果表示 -->
    <div v-if="showValidationDetails && criticalIssues.length > 0" class="validation-details">
      <h3>🔍 データ品質の詳細</h3>
      <div v-for="issue in criticalIssues" :key="issue.message" class="validation-issue" :class="issue.type">
        <span class="issue-severity">{{ issue.severity === 'high' ? '🚨' : '⚠️' }}</span>
        <div class="issue-content">
          <p class="issue-message">{{ issue.message }}</p>
          <p v-if="issue.action" class="issue-action">{{ issue.action }}</p>
        </div>
      </div>
    </div>
    
    <!-- 投資データサマリー -->
    <div v-if="dataSummary" class="data-summary">
      <h3>📊 データサマリー</h3>
      <div class="summary-grid">
        <div class="summary-item">
          <span class="summary-label">保有銘柄数:</span>
          <span class="summary-value">{{ dataSummary.totalStocks }}銘柄</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">取引履歴:</span>
          <span class="summary-value">{{ dataSummary.totalTransactions }}件</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">価格データ:</span>
          <span class="summary-value">{{ dataSummary.totalPriceRecords }}件</span>
        </div>
        <div v-if="dataSummary.lastValidated" class="summary-item">
          <span class="summary-label">最終検証:</span>
          <span class="summary-value">{{ dataSummary.lastValidated }}</span>
        </div>
      </div>
    </div>

    <!-- スケルトンローディング表示 -->
    <template v-if="loading">
      <SkeletonLoader type="summary" />
      <SkeletonLoader type="table" :columns="7" :rows="5" />
      <SkeletonLoader type="text" :lines="2" />
    </template>
    
    <!-- エラー表示 -->
    <ErrorDisplay
      v-if="error && !loading"
      :message="error"
      :type="errorType"
      :details="errorDetails"
      :retryable="true"
      :retrying="loading"
      @retry="handleRetry"
      @dismiss="clearError"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { usePortfolioData } from '../../composables/usePortfolioData.js'
import { useDataValidation } from '../../composables/useDataValidation.js'
import SkeletonLoader from '../ui/SkeletonLoader.vue'
import ErrorDisplay from '../ui/ErrorDisplay.vue'

// ポートフォリオデータ管理
const {
  holdings,
  loading,
  error,
  portfolioSummary,
  holdingsWithCalc,
  fetchPortfolioData,
  updatePrice
} = usePortfolioData()

// データ検証・品質保証機能
const {
  validationStatus,
  criticalIssues,
  dataSummary,
  validateData,
  checkInvestmentAnomalies
} = useDataValidation()

// UI状態管理
const showValidationDetails = ref(false)

// エラータイプとエラー詳細の判定
const errorType = computed(() => {
  if (!error.value) return 'generic'
  
  const errorMessage = error.value.toLowerCase()
  
  if (errorMessage.includes('network') || errorMessage.includes('timeout') || errorMessage.includes('fetch')) {
    return 'network'
  }
  if (errorMessage.includes('auth') || errorMessage.includes('permission') || errorMessage.includes('401')) {
    return 'auth'
  }
  if (errorMessage.includes('data') || errorMessage.includes('validation') || errorMessage.includes('sheets')) {
    return 'data'
  }
  
  return 'generic'
})

const errorDetails = computed(() => {
  if (!error.value) return null
  return `Error details: ${error.value}\nTimestamp: ${new Date().toISOString()}`
})

// エラーハンドリング用メソッド
const handleRetry = async () => {
  console.log('データ再取得を実行中...')
  try {
    await Promise.all([
      fetchPortfolioData(),
      validateData()
    ])
  } catch (retryError) {
    console.error('再試行でもエラーが発生:', retryError)
  }
}

const clearError = () => {
  // PortfolioDataのComposableでエラーをクリア
  if (error.value) {
    error.value = null
  }
}

// 通貨フォーマット用のユーティリティ関数
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency: 'JPY'
  }).format(amount)
}

// ポートフォリオデータが更新された際に投資指標の異常値をチェック
watch(holdingsWithCalc, (newData) => {
  if (newData && newData.length > 0) {
    const portfolioData = {
      stocks: newData.map(stock => ({
        name: stock.stock || stock.name,
        currentPrice: stock.currentPrice,
        profit: stock.profitLoss,
        totalCost: stock.totalPurchase,
        transactions: stock.transactions || []
      }))
    }
    
    const anomalies = checkInvestmentAnomalies(portfolioData)
    if (anomalies.length > 0) {
      console.warn('投資指標で異常値を検出:', anomalies)
    }
  }
}, { deep: true })

// コンポーネントマウント時にデータを取得
onMounted(async () => {
  console.log('PortfolioDashboard mounted - 統合データ品質チェック機能付き')
  
  try {
    // ポートフォリオデータとデータ検証を並列実行
    await Promise.all([
      fetchPortfolioData(),
      validateData()
    ])
    
    console.log('データ取得・検証完了')
    console.log('保有銘柄数:', holdings.value.length)
    console.log('総損益:', portfolioSummary.value?.totalProfitLoss)
    console.log('データ品質ステータス:', validationStatus.value?.level)
    
  } catch (err) {
    console.error('データ取得・検証でエラーが発生:', err)
  }
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

/* データ品質ステータス */
.data-quality-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-weight: 500;
}

.data-quality-status.success {
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.data-quality-status.warning {
  background-color: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
}

.data-quality-status.error {
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
}

.status-icon {
  font-size: 1.2em;
}

.toggle-details {
  margin-left: auto;
  background: transparent;
  border: 1px solid currentColor;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 0.9em;
  color: inherit;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-details:hover {
  background-color: currentColor;
  color: white;
}

/* 検証詳細 */
.validation-details {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.validation-details h3 {
  margin: 0 0 12px 0;
  color: #374151;
}

.validation-issue {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px;
  margin: 8px 0;
  border-radius: 6px;
}

.validation-issue.error {
  background-color: #fef2f2;
  border-left: 4px solid #ef4444;
}

.validation-issue.warning {
  background-color: #fffbeb;
  border-left: 4px solid #f59e0b;
}

.issue-severity {
  font-size: 1.1em;
  margin-top: 2px;
}

.issue-content {
  flex: 1;
}

.issue-message {
  margin: 0 0 4px 0;
  font-weight: 500;
}

.issue-action {
  margin: 0;
  font-size: 0.9em;
  color: #6b7280;
}

/* データサマリー */
.data-summary {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.data-summary h3 {
  margin: 0 0 12px 0;
  color: #374151;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background-color: #f9fafb;
  border-radius: 4px;
}

.summary-label {
  font-size: 0.9em;
  color: #6b7280;
}

.summary-value {
  font-weight: 600;
  color: #374151;
}
</style>
