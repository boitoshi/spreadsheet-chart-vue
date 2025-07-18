<template>
  <div id="app">
    <header>
      <h1>📊 投資ポートフォリオ</h1>
    </header>
    
    <main>
      <!-- エラー表示 -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
      
      <!-- ローディング表示 -->
      <div v-if="isLoading" class="loading-message">
        データを読み込み中...
      </div>
      
      <!-- サマリーカード -->
      <section class="summary" v-if="!isLoading && !error">
        <div class="card">
          <h3>総評価額</h3>
          <p class="big-number">{{ totalValue.toLocaleString() }}円</p>
        </div>
        <div class="card">
          <h3>総損益</h3>
          <p class="big-number" :class="totalProfit >= 0 ? 'profit' : 'loss'">
            {{ totalProfit >= 0 ? '+' : '' }}{{ totalProfit.toLocaleString() }}円
          </p>
        </div>
      </section>
      
      <!-- 保有銘柄一覧 -->
      <section class="holdings" v-if="!isLoading && !error">
        <h2>保有銘柄</h2>
        <table>
          <thead>
            <tr>
              <th>銘柄</th>
              <th>保有数</th>
              <th>取得価格</th>
              <th>現在価格</th>
              <th>評価額</th>
              <th>損益</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="stock in stocks" :key="stock.name">
              <tr class="stock-row" @click="toggleDetails(stock.name)">
                <td>
                  {{ stock.name }}
                  <span class="expand-icon">{{ expandedStock === stock.name ? '▼' : '▶' }}</span>
                </td>
                <td>{{ stock.quantity }}株</td>
                <td>{{ stock.averagePrice.toLocaleString() }}円</td>
                <td>{{ stock.currentPrice.toLocaleString() }}円</td>
                <td>{{ stock.currentValue.toLocaleString() }}円</td>
                <td :class="stock.profit >= 0 ? 'profit' : 'loss'">
                  {{ stock.profit >= 0 ? '+' : '' }}{{ stock.profit.toLocaleString() }}円
                </td>
              </tr>
              
              <!-- 詳細表示（展開時） -->
              <tr v-if="expandedStock === stock.name" class="detail-row">
                <td colspan="6">
                  <div class="transaction-details">
                    <h4>取引履歴</h4>
                    <div v-for="transaction in stock.transactions" :key="transaction.date" class="transaction">
                      <span class="date">{{ transaction.date }}</span>
                      <span class="amount">{{ transaction.quantity }}株</span>
                      <span class="price">@{{ transaction.price.toLocaleString() }}円</span>
                      <span class="total">{{ (transaction.quantity * transaction.price).toLocaleString() }}円</span>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </section>
      
      <!-- チャートエリア -->
      <section class="charts" v-if="!isLoading && !error">
        <div class="chart-container">
          <h3>ポートフォリオ構成</h3>
          <canvas ref="pieChart"></canvas>
        </div>
        
        <div class="chart-container">
          <h3>総損益推移</h3>
          <div class="chart-controls">
            <button @click="changePeriod('6months')" :class="{ active: selectedPeriod === '6months' }">6ヶ月</button>
            <button @click="changePeriod('1year')" :class="{ active: selectedPeriod === '1year' }">1年</button>
            <button @click="changePeriod('all')" :class="{ active: selectedPeriod === 'all' }">全期間</button>
          </div>
          <canvas ref="lineChart"></canvas>
        </div>
        
        <div class="chart-container">
          <h3>銘柄別損益推移</h3>
          <div class="chart-controls">
            <button @click="changeStock('all')" :class="{ active: selectedStock === 'all' }">全銘柄</button>
            <button v-for="stock in stocks" :key="stock.name" @click="changeStock(stock.name)" :class="{ active: selectedStock === stock.name }">
              {{ stock.name }}
            </button>
          </div>
          <canvas ref="stockChart"></canvas>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
/**
 * 投資ポートフォリオ管理アプリ
 * 
 * 機能：
 * - 保有銘柄の表示と損益計算
 * - 複数回購入（買い増し）対応
 * - ポートフォリオ構成円グラフ
 * - 総損益推移グラフ（期間選択可能）
 * - 銘柄別損益推移グラフ（取得時期ベース）
 * - 銘柄クリックで詳細取引履歴表示
 */
import { ref, computed, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'
import { apiService } from './utils/api.js'

// Chart.jsのすべてのコンポーネントを登録
Chart.register(...registerables)

// ===== データ定義セクション =====

/**
 * 保有銘柄データ（APIから取得）
 * 
 * 各銘柄の構造：
 * - name: 銘柄名
 * - currentPrice: 現在の株価
 * - transactions: 取引履歴の配列（買い増し対応）
 *   - date: 購入日（YYYY/MM/DD形式）
 *   - quantity: 購入株数
 *   - price: その時の購入価格
 */
const stocks = ref([])
const isLoading = ref(false)
const error = ref(null)

// ===== UI制御用の変数 =====

/**
 * 詳細表示の制御
 * - null: 何も展開していない
 * - 銘柄名: その銘柄の詳細を展開中
 */
const expandedStock = ref(null)

/**
 * 銘柄行をクリックした時の詳細表示切り替え
 * @param {string} stockName - 銘柄名
 */
const toggleDetails = (stockName) => {
  expandedStock.value = expandedStock.value === stockName ? null : stockName
}

/**
 * 期間選択の変更
 * @param {string} period - 期間（'6months', '1year', 'all'）
 */
const changePeriod = (period) => {
  selectedPeriod.value = period
  updateLineChart()
}

/**
 * 銘柄選択の変更
 * @param {string} stockName - 銘柄名（'all'または具体的な銘柄名）
 */
const changeStock = (stockName) => {
  selectedStock.value = stockName
  updateStockChart()
}

// ===== チャート関連の設定 =====

/**
 * チャートのDOM要素への参照
 */
const pieChart = ref(null)      // ポートフォリオ構成円グラフ
const lineChart = ref(null)     // 総損益推移線グラフ  
const stockChart = ref(null)    // 銘柄別損益推移グラフ

/**
 * ユーザー選択状態
 */
const selectedPeriod = ref('6months') // 損益推移の期間選択
const selectedStock = ref('all')       // 銘柄別グラフの銘柄選択

/**
 * Chart.jsインスタンス（データ更新用）
 */
let lineChartInstance = null   // 総損益推移グラフのインスタンス
let stockChartInstance = null  // 銘柄別損益グラフのインスタンス

// 期間別データ（APIから取得）
const profitData = ref({
  '6months': {
    labels: [],
    data: []
  },
  '1year': {
    labels: [],
    data: []
  },
  'all': {
    labels: [],
    data: []
  }
})

const updateLineChart = () => {
  if (lineChartInstance) {
    const currentData = profitData.value[selectedPeriod.value]
    lineChartInstance.data.labels = currentData.labels
    lineChartInstance.data.datasets[0].data = currentData.data
    lineChartInstance.update()
  }
}

// 銘柄別損益データ（APIから取得）
const stockProfitData = ref({})

const updateStockChart = () => {
  if (stockChartInstance) {
    if (selectedStock.value === 'all') {
      // 全銘柄表示（共通の月次軸を使用）
      const commonLabels = ['1月', '2月', '3月', '4月', '5月', '6月']
      const datasets = stocks.value.map((stock, index) => {
        const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
        return {
          label: stock.name,
          data: stockProfitData.value[stock.name]?.data || [],
          borderColor: colors[index % colors.length],
          backgroundColor: colors[index % colors.length] + '20',
          fill: false,
          tension: 0.4
        }
      })
      
      stockChartInstance.data.labels = commonLabels
      stockChartInstance.data.datasets = datasets
      
      // 軸の設定を更新
      stockChartInstance.options.scales.x.title.text = '期間'
    } else {
      // 個別銘柄表示（実際の取得時期を表示）
      const stockData = stockProfitData.value[selectedStock.value]
      const stockInfo = stocks.value.find(s => s.name === selectedStock.value)
      const color = stockInfo?.profit >= 0 ? '#28a745' : '#dc3545'
      
      if (stockData) {
        stockChartInstance.data.labels = stockData.labels
        stockChartInstance.data.datasets = [{
          label: selectedStock.value + ' 損益推移',
          data: stockData.data,
          borderColor: color,
          backgroundColor: color + '20',
          fill: true,
          tension: 0.4,
          pointBackgroundColor: stockData.acquisitions?.map((acq, index) => 
            acq !== '' ? '#ff6b35' : color
          ) || [],
          pointRadius: stockData.acquisitions?.map((acq, index) => 
            acq !== '' ? 8 : 4
          ) || [],
          pointHoverRadius: stockData.acquisitions?.map((acq, index) => 
            acq !== '' ? 10 : 6
          ) || []
        }]
      }
      
      // 軸の設定を更新
      stockChartInstance.options.scales.x.title.text = '取得時期からの経過'
    }
    stockChartInstance.update()
  }
}

// ===== API関数 =====

/**
 * ポートフォリオデータをAPIから取得
 */
const loadPortfolioData = async () => {
  try {
    isLoading.value = true
    error.value = null
    
    const response = await apiService.getPortfolioData()
    stocks.value = response.data.stocks || []
    
    // 推移データも取得
    const historyResponse = await apiService.getProfitHistory()
    const historyData = historyResponse.data
    
    // 期間別データの設定
    profitData.value = {
      '6months': historyData.periods?.sixMonths || { labels: [], data: [] },
      '1year': historyData.periods?.oneYear || { labels: [], data: [] },
      'all': historyData.periods?.all || { labels: [], data: [] }
    }
    
    // 銘柄別データの設定
    stockProfitData.value = historyData.stocks || {}
    
  } catch (err) {
    console.error('ポートフォリオデータの取得に失敗しました:', err)
    error.value = 'データの取得に失敗しました。バックエンドサーバーが起動していることを確認してください。'
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  // データ取得
  await loadPortfolioData()
  
  // ポートフォリオ構成（円グラフ）
  new Chart(pieChart.value, {
    type: 'pie',
    data: {
      labels: stocks.value.map(stock => stock.name),
      datasets: [{
        data: stocks.value.map(stock => stock.currentValue || 0),
        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'bottom'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const total = context.dataset.data.reduce((sum, value) => sum + value, 0)
              const percentage = ((context.parsed / total) * 100).toFixed(1)
              return context.label + ': ' + context.parsed.toLocaleString() + '円 (' + percentage + '%)'
            }
          }
        },
        datalabels: {
          display: true,
          color: 'white',
          font: {
            weight: 'bold',
            size: 12
          },
          formatter: (value, context) => {
            const total = context.dataset.data.reduce((sum, val) => sum + val, 0)
            const percentage = ((value / total) * 100).toFixed(1)
            return percentage + '%'
          }
        }
      }
    }
  })

  // 損益推移（線グラフ）
  const initialData = profitData.value[selectedPeriod.value]
  lineChartInstance = new Chart(lineChart.value, {
    type: 'line',
    data: {
      labels: initialData.labels,
      datasets: [{
        label: '総損益',
        data: initialData.data,
        borderColor: '#36A2EB',
        backgroundColor: 'rgba(54, 162, 235, 0.1)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return value.toLocaleString() + '円'
            }
          }
        }
      }
    }
  })

  // 銘柄別損益グラフ
  const initialStockData = stocks.value.map((stock, index) => {
    const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
    return {
      label: stock.name,
      data: stockProfitData.value[stock.name]?.data || [],
      borderColor: colors[index % colors.length],
      backgroundColor: colors[index % colors.length] + '20',
      fill: false,
      tension: 0.4
    }
  })

  stockChartInstance = new Chart(stockChart.value, {
    type: 'line',
    data: {
      labels: ['1月', '2月', '3月', '4月', '5月', '6月'], // 初期は共通軸
      datasets: initialStockData
    },
    options: {
      responsive: true,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      scales: {
        x: {
          title: {
            display: true,
            text: '期間'
          }
        },
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return value.toLocaleString() + '円'
            }
          }
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function(context) {
              return context.dataset.label + ': ' + context.parsed.y.toLocaleString() + '円'
            },
            afterLabel: function(context) {
              // 個別銘柄の場合、取得タイミング情報を表示
              if (selectedStock.value !== 'all') {
                const stockData = stockProfitData.value[selectedStock.value]
                const acquisition = stockData?.acquisitions?.[context.dataIndex]
                return acquisition !== '' ? '📍 ' + acquisition : ''
              }
              return ''
            }
          }
        }
      }
    }
  })
})

// ===== 計算用のComputed Properties =====

/**
 * 総評価額の計算
 */
const totalValue = computed(() => {
  return stocks.value.reduce((sum, stock) => sum + stock.currentValue, 0)
})

/**
 * 総損益の計算
 */
const totalProfit = computed(() => {
  return stocks.value.reduce((sum, stock) => sum + stock.profit, 0)
})

/**
 * 総コスト（投資元本）の計算
 */
const totalCost = computed(() => {
  return stocks.value.reduce((sum, stock) => sum + stock.cost, 0)
})

/**
 * 総損益率の計算
 */
const totalProfitRatio = computed(() => {
  return totalCost.value > 0 ? (totalProfit.value / totalCost.value) * 100 : 0
})

</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background-color: #f5f5f5;
  color: #333;
}

#app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

header {
  text-align: center;
  margin-bottom: 30px;
}

header h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 10px;
}

.summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: center;
}

.card h3 {
  color: #666;
  margin-bottom: 10px;
}

.big-number {
  font-size: 1.5rem;
  font-weight: bold;
}

.profit {
  color: #28a745;
}

.loss {
  color: #dc3545;
}

.holdings {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.holdings h2 {
  margin-bottom: 20px;
  color: #2c3e50;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #666;
}

.stock-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.stock-row:hover {
  background-color: #f8f9fa;
}

.expand-icon {
  margin-left: 10px;
  color: #007bff;
  font-size: 0.8rem;
}

.detail-row {
  background: #f8f9fa !important;
}

.detail-row:hover {
  background: #f8f9fa !important;
}

.transaction-details {
  padding: 15px;
  border-left: 3px solid #007bff;
}

.transaction-details h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 1rem;
}

.transaction {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
  font-size: 0.9rem;
}

.transaction:last-child {
  border-bottom: none;
}

.transaction .date {
  color: #666;
  font-weight: 500;
}

.transaction .amount {
  color: #333;
  font-weight: 600;
}

.transaction .price {
  color: #007bff;
}

.transaction .total {
  color: #333;
  font-weight: 500;
}

.charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-top: 30px;
}

.chart-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chart-container h3 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.chart-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.chart-controls button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.chart-controls button:hover {
  background: #f8f9fa;
}

.chart-controls button.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid #f5c6cb;
}

.loading-message {
  background: #d1ecf1;
  color: #0c5460;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid #bee5eb;
  text-align: center;
}

@media (max-width: 768px) {
  .summary {
    grid-template-columns: 1fr;
  }
  
  .charts {
    grid-template-columns: 1fr;
  }
  
  .chart-container {
    min-width: auto;
  }
  
  table {
    font-size: 0.9rem;
  }
  
  th, td {
    padding: 8px;
  }
}
</style>