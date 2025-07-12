<template>
  <div id="app">
    <header>
      <h1>📊 投資ポートフォリオ</h1>
    </header>
    
    <main>
      <!-- サマリーカード -->
      <section class="summary">
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
      <section class="holdings">
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
                  <span v-if="stock.transactions.length > 1" class="detail-icon">📊</span>
                </td>
                <td>{{ stock.quantity }}株</td>
                <td>{{ stock.avgPrice.toLocaleString() }}円</td>
                <td>{{ stock.currentPrice.toLocaleString() }}円</td>
                <td>{{ (stock.currentPrice * stock.quantity).toLocaleString() }}円</td>
                <td :class="stock.profit >= 0 ? 'profit' : 'loss'">
                  {{ stock.profit >= 0 ? '+' : '' }}{{ stock.profit.toLocaleString() }}円
                </td>
              </tr>
              <!-- 詳細履歴表示 -->
              <tr v-if="expandedStock === stock.name" class="detail-row">
                <td colspan="6">
                  <div class="transaction-details">
                    <h4>取引履歴</h4>
                    <div v-for="(transaction, index) in stock.transactions" :key="index" class="transaction">
                      <span class="date">{{ transaction.date }}</span>
                      <span class="amount">{{ transaction.quantity }}株</span>
                      <span class="price">@{{ transaction.price.toLocaleString() }}円</span>
                      <span class="total">小計: {{ (transaction.quantity * transaction.price).toLocaleString() }}円</span>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </section>
      
      <!-- グラフ表示 -->
      <section class="charts">
        <div class="chart-container">
          <h2>ポートフォリオ構成</h2>
          <canvas ref="pieChart" width="400" height="200"></canvas>
        </div>
        <div class="chart-container">
          <h2>総損益推移</h2>
          <div class="chart-controls">
            <label>期間選択：</label>
            <select v-model="selectedPeriod" @change="updateLineChart">
              <option value="6months">過去6ヶ月</option>
              <option value="1year">過去1年</option>
              <option value="all">全期間</option>
            </select>
          </div>
          <canvas ref="lineChart" width="400" height="200"></canvas>
        </div>
      </section>
      
      <!-- 銘柄別損益グラフ -->
      <section class="charts">
        <div class="chart-container full-width">
          <h2>銘柄別損益推移</h2>
          <div class="chart-controls">
            <label>銘柄選択：</label>
            <select v-model="selectedStock" @change="updateStockChart">
              <option value="all">全銘柄</option>
              <option v-for="stock in stocks" :key="stock.name" :value="stock.name">
                {{ stock.name }}
              </option>
            </select>
          </div>
          <canvas ref="stockChart" width="800" height="300"></canvas>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
/**
 * 投資ポートフォリオ管理ダッシュボード
 * 
 * 主要機能：
 * - 保有銘柄一覧と損益表示
 * - ポートフォリオ構成円グラフ（パーセンテージ表示付き）
 * - 総損益推移グラフ（期間選択可能）
 * - 銘柄別損益推移グラフ（取得時期ベース）
 * - 銘柄クリックで詳細取引履歴表示
 */
import { ref, computed, onMounted } from 'vue'
import { Chart, registerables } from 'chart.js'

// Chart.jsのすべてのコンポーネントを登録
Chart.register(...registerables)

// ===== データ定義セクション =====

/**
 * 保有銘柄データ（ダミーデータ）
 * 
 * 各銘柄の構造：
 * - name: 銘柄名
 * - currentPrice: 現在の株価
 * - transactions: 取引履歴の配列（買い増し対応）
 *   - date: 購入日（YYYY/MM/DD形式）
 *   - quantity: 購入株数
 *   - price: その時の購入価格
 * 
 * 注意：実際のデータに変更する場合は、この部分を修正してください
 */
const stocks = ref([
  {
    name: 'トヨタ自動車',
    currentPrice: 2800, // 現在の株価
    transactions: [
      { date: '2024/01/15', quantity: 50, price: 2400 }, // 1回目購入
      { date: '2024/03/10', quantity: 30, price: 2600 }, // 2回目購入（買い増し）
      { date: '2024/05/20', quantity: 20, price: 2700 }  // 3回目購入（買い増し）
    ]
  },
  {
    name: 'ソフトバンク', 
    currentPrice: 1150,
    transactions: [
      { date: '2024/02/01', quantity: 100, price: 1200 }, // 1回目購入
      { date: '2024/04/15', quantity: 100, price: 1200 }  // 2回目購入（同価格）
    ]
  },
  {
    name: '任天堂',
    currentPrice: 6200,
    transactions: [
      { date: '2024/01/30', quantity: 50, price: 5600 } // 1回のみ購入
    ]
  },
  {
    name: 'DeNA',
    currentPrice: 2350,
    transactions: [
      { date: '2024/03/01', quantity: 100, price: 2000 }, // 1回目購入
      { date: '2024/06/01', quantity: 50, price: 2400 }   // 2回目購入（値上がり後）
    ]
  }
])

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

// ===== データ計算処理 =====

/**
 * 各銘柄の計算処理（平均価格、総数量、損益）
 * 
 * 複数回の買い増しがある場合：
 * - quantity: 全取引の合計株数
 * - avgPrice: 加重平均価格（総投資額 ÷ 総株数）
 * - profit: 現在価値 - 総投資額
 */
stocks.value.forEach(stock => {
  // 総数量計算（全ての取引の株数を合計）
  stock.quantity = stock.transactions.reduce((sum, t) => sum + t.quantity, 0)
  
  // 平均価格計算（加重平均）
  const totalCost = stock.transactions.reduce((sum, t) => sum + (t.quantity * t.price), 0)
  stock.avgPrice = Math.round(totalCost / stock.quantity)
  
  // 損益計算（現在価値 - 投資額）
  const totalCurrent = stock.currentPrice * stock.quantity
  stock.profit = totalCurrent - totalCost
})

// ===== 集計値の計算（リアクティブ） =====

/**
 * ポートフォリオ全体の評価額
 * @returns {number} 全銘柄の現在価値の合計
 */
const totalValue = computed(() => {
  return stocks.value.reduce((sum, stock) => sum + (stock.currentPrice * stock.quantity), 0)
})

/**
 * ポートフォリオ全体の損益
 * @returns {number} 全銘柄の損益の合計
 */
const totalProfit = computed(() => {
  return stocks.value.reduce((sum, stock) => sum + stock.profit, 0)
})

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

// 期間別ダミーデータ
const profitData = {
  '6months': {
    labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
    data: [10000, 25000, 15000, 35000, 45000, totalProfit.value]
  },
  '1year': {
    labels: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
    data: [-5000, 10000, 25000, 15000, 35000, 45000, 55000, 40000, 60000, 70000, 80000, totalProfit.value]
  },
  'all': {
    labels: ['2023年1月', '2023年6月', '2023年12月', '2024年6月'],
    data: [-20000, 30000, 50000, totalProfit.value]
  }
}

const updateLineChart = () => {
  if (lineChartInstance) {
    const currentData = profitData[selectedPeriod.value]
    lineChartInstance.data.labels = currentData.labels
    lineChartInstance.data.datasets[0].data = currentData.data
    lineChartInstance.update()
  }
}

// 銘柄別損益ダミーデータ（取得時期ベース）
const stockProfitData = {
  'トヨタ自動車': {
    labels: ['2024/01/15', '2024/02/15', '2024/03/15', '2024/04/15', '2024/05/15', '2024/06/15'],
    data: [-6000, -3000, 12000, 18000, 24000, 28000],
    acquisitions: ['1回目購入', '', '2回目購入', '', '3回目購入', '']
  },
  'ソフトバンク': {
    labels: ['2024/02/01', '2024/03/01', '2024/04/01', '2024/04/15', '2024/05/01', '2024/06/01'],
    data: [0, -5000, -8000, -12000, -10000, -10000],
    acquisitions: ['1回目購入', '', '', '2回目購入', '', '']
  },
  '任天堂': {
    labels: ['2024/01/30', '2024/02/28', '2024/03/31', '2024/04/30', '2024/05/31', '2024/06/30'],
    data: [10000, 15000, 20000, 25000, 28000, 30000],
    acquisitions: ['購入', '', '', '', '', '']
  },
  'DeNA': {
    labels: ['2024/03/01', '2024/04/01', '2024/05/01', '2024/06/01', '2024/06/15', '2024/06/30'],
    data: [5000, 8000, 15000, 25000, 35000, 39500],
    acquisitions: ['1回目購入', '', '', '2回目購入', '', '']
  }
}

const updateStockChart = () => {
  if (stockChartInstance) {
    if (selectedStock.value === 'all') {
      // 全銘柄表示（共通の月次軸を使用）
      const commonLabels = ['1月', '2月', '3月', '4月', '5月', '6月']
      const datasets = stocks.value.map((stock, index) => {
        const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
        return {
          label: stock.name,
          data: stockProfitData[stock.name].data,
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
      const stockData = stockProfitData[selectedStock.value]
      const stockInfo = stocks.value.find(s => s.name === selectedStock.value)
      const color = stockInfo.profit >= 0 ? '#28a745' : '#dc3545'
      
      stockChartInstance.data.labels = stockData.labels
      stockChartInstance.data.datasets = [{
        label: selectedStock.value + ' 損益推移',
        data: stockData.data,
        borderColor: color,
        backgroundColor: color + '20',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: stockData.acquisitions.map((acq, index) => 
          acq !== '' ? '#ff6b35' : color
        ),
        pointRadius: stockData.acquisitions.map((acq, index) => 
          acq !== '' ? 8 : 4
        ),
        pointHoverRadius: stockData.acquisitions.map((acq, index) => 
          acq !== '' ? 10 : 6
        )
      }]
      
      // 軸の設定を更新
      stockChartInstance.options.scales.x.title.text = '取得時期からの経過'
    }
    stockChartInstance.update()
  }
}

onMounted(() => {
  // ポートフォリオ構成（円グラフ）
  new Chart(pieChart.value, {
    type: 'pie',
    data: {
      labels: stocks.value.map(stock => stock.name),
      datasets: [{
        data: stocks.value.map(stock => stock.currentPrice * stock.quantity),
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
              const value = context.parsed.toLocaleString()
              return context.label + ': ' + value + '円 (' + percentage + '%)'
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
  const initialData = profitData[selectedPeriod.value]
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
      interaction: {
        intersect: false,
        mode: 'index'
      },
      scales: {
        y: {
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
      data: stockProfitData[stock.name].data,
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
          title: {
            display: true,
            text: '損益'
          },
          ticks: {
            callback: function(value) {
              return value.toLocaleString() + '円'
            }
          }
        }
      },
      plugins: {
        legend: {
          position: 'bottom'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return context.dataset.label + ': ' + context.parsed.y.toLocaleString() + '円'
            },
            afterLabel: function(context) {
              // 個別銘柄の場合、取得タイミング情報を表示
              if (selectedStock.value !== 'all') {
                const stockData = stockProfitData[selectedStock.value]
                const acquisition = stockData.acquisitions[context.dataIndex]
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
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Arial, sans-serif;
  background: #f5f5f5;
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

h1 {
  color: #333;
  font-size: 2rem;
}

.summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
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
  color: #333;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background: #f8f9fa;
  font-weight: bold;
  color: #333;
}

tbody tr:hover {
  background: #f8f9fa;
}

.stock-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.stock-row:hover {
  background: #e3f2fd !important;
}

.detail-icon {
  margin-left: 5px;
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
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 30px;
}

.chart-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chart-container.full-width {
  grid-column: 1 / -1;
}

.chart-container h2 {
  margin-bottom: 20px;
  color: #333;
  text-align: center;
}

.chart-controls {
  margin-bottom: 15px;
  text-align: center;
}

.chart-controls label {
  margin-right: 10px;
  font-weight: 500;
}

.chart-controls select {
  padding: 5px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
}

@media (max-width: 768px) {
  .summary {
    grid-template-columns: 1fr;
  }
  
  .charts {
    grid-template-columns: 1fr;
  }
  
  table {
    font-size: 0.9rem;
  }
  
  th, td {
    padding: 8px;
  }
}
</style>