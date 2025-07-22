<template>
  <div id="app">
    <header>
      <h1>📊 投資ポートフォリオ</h1>
    </header>
    
    <main>
      <!-- エラー表示 -->
      <div v-if="error" class="error-message">
        <div class="error-content">
          <div class="error-text">{{ error }}</div>
          <button @click="retryDataLoad" class="retry-button" :disabled="isLoading">
            {{ isLoading ? '更新中...' : 'データを再取得' }}
          </button>
        </div>
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
                <td>{{ stock.avgPrice.toLocaleString() }}円</td>
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
            <button @click="changePeriod('3months')" :class="{ active: selectedPeriod === '3months' }">3ヶ月</button>
            <button @click="changePeriod('6months')" :class="{ active: selectedPeriod === '6months' }">6ヶ月</button>
            <button @click="changePeriod('1year')" :class="{ active: selectedPeriod === '1year' }">1年</button>
            <button @click="changePeriod('2years')" :class="{ active: selectedPeriod === '2years' }">2年</button>
            <button @click="changePeriod('3years')" :class="{ active: selectedPeriod === '3years' }">3年</button>
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

<script setup>
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
 * @param period - 期間（'6months', '1year', 'all'）
 */
const changePeriod = (period) => {
  selectedPeriod.value = period
  updateLineChart()
}

/**
 * 銘柄選択の変更
 * @param stockName - 銘柄名（'all'または具体的な銘柄名）
 */
const changeStock = async (stockName) => {
  selectedStock.value = stockName
  await updateStockChart()
}

/**
 * データ再取得機能
 * エラー時にユーザーがワンクリックでリトライできる
 */
const retryDataLoad = async () => {
  console.log('データ再取得を開始...')
  error.value = null  // エラーメッセージをクリア
  await loadPortfolioData()
  console.log('データ再取得完了')
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
  '3months': {
    labels: [],
    data: []
  },
  '6months': {
    labels: [],
    data: []
  },
  '1year': {
    labels: [],
    data: []
  },
  '2years': {
    labels: [],
    data: []
  },
  '3years': {
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
    lineChartInstance.data.datasets[0].data = currentData.cumulativeInvestments  // 累積投資額推移
    lineChartInstance.data.datasets[1].data = currentData.values     // 評価額推移
    lineChartInstance.data.datasets[2].data = currentData.profits    // 損益推移
    lineChartInstance.update()
  }
}

// 銘柄別損益データ（APIから取得）
const stockProfitData = ref({})

const updateStockChart = async () => {
  if (!stockChartInstance) {
    console.error('stockChartInstance が初期化されていません')
    return
  }
  
  if (selectedStock.value === 'all') {
    // 全銘柄表示（共通の月次軸を使用）
    console.log('全銘柄表示モードでチャート更新中...')
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
    // 個別銘柄表示（取得時期以降の正確な時系列データを使用）
    console.log(`個別銘柄「${selectedStock.value}」のデータを取得中...`)
    
    try {
      const response = await apiService.getStockHistory(selectedStock.value)
      console.log('API レスポンス:', response)
      
      if (!response.data) {
        throw new Error('APIレスポンスにdataプロパティがありません')
      }
      
      const stockDetail = response.data
      const timeSeries = stockDetail.timeSeries
      
      console.log('銘柄詳細データ:', stockDetail)
      console.log('時系列データ:', timeSeries)
      
      const stockInfo = stocks.value.find(s => s.name === selectedStock.value)
      const color = stockInfo?.profit >= 0 ? '#28a745' : '#dc3545'
      
      if (timeSeries && timeSeries.labels && timeSeries.labels.length > 0) {
        console.log(`時系列データあり: ${timeSeries.labels.length}件のデータポイント`)
        
        stockChartInstance.data.labels = timeSeries.labels
        stockChartInstance.data.datasets = [
          {
            label: '取得価格推移',
            data: timeSeries.acquisitionPrices || [],
            borderColor: '#FF6384',
            backgroundColor: 'rgba(255, 99, 132, 0.1)',
            fill: false,
            tension: 0.4,
            pointRadius: 3
          },
          {
            label: '評価額推移',
            data: timeSeries.values || [],
            borderColor: '#36A2EB',
            backgroundColor: 'rgba(54, 162, 235, 0.1)',
            fill: false,
            tension: 0.4,
            pointRadius: 3
          },
          {
            label: '損益推移',
            data: timeSeries.profits || [],
            borderColor: color,
            backgroundColor: color + '20',
            fill: true,
            tension: 0.4,
            pointBackgroundColor: timeSeries.acquisitionMarkers?.map((marker) => 
              marker !== '' ? '#ff6b35' : color
            ) || [],
            pointRadius: timeSeries.acquisitionMarkers?.map((marker) => 
              marker !== '' ? 8 : 4
            ) || [],
            pointHoverRadius: timeSeries.acquisitionMarkers?.map((marker) => 
              marker !== '' ? 10 : 6
            ) || []
          }
        ]
        
        console.log('チャートデータが設定されました')
      } else {
        console.warn('時系列データが空です')
        // データがない場合は空のグラフを表示
        stockChartInstance.data.labels = ['データなし']
        stockChartInstance.data.datasets = [{
          label: selectedStock.value + ' (データなし)',
          data: [0],
          borderColor: color,
          backgroundColor: color + '20'
        }]
      }
    } catch (err) {
      console.error('個別銘柄データ取得エラー詳細:', {
        error: err,
        message: err.message,
        stack: err.stack,
        selectedStock: selectedStock.value
      })
      
      // エラー詳細を画面に表示（個別銘柄エラー）
      console.warn(`銘柄「${selectedStock.value}」のデータ取得に失敗:`, err.message)
      
      // エラー時は明確にエラーを示すチャートを表示
      stockChartInstance.data.labels = ['データ取得エラー']
      stockChartInstance.data.datasets = [{
        label: selectedStock.value + ' (API接続失敗)',
        data: [0],
        borderColor: '#dc3545',
        backgroundColor: 'rgba(220, 53, 69, 0.2)'
      }]
      
      // 全体エラーとしては設定しない（銘柄切り替えで回復可能）
    }
    
    // 軸の設定を更新
    stockChartInstance.options.scales.x.title.text = '取得時期からの経過'
  }
  
  // チャート更新
  try {
    stockChartInstance.update()
    console.log('チャート更新完了')
  } catch (updateErr) {
    console.error('チャート更新エラー:', updateErr)
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
    
    console.log('ポートフォリオデータの並列取得を開始...')
    
    // メインデータと履歴データを並列取得
    const [portfolioResponse, historyResponse, spreadsheetResponse] = await Promise.allSettled([
      apiService.getPortfolioData(),
      apiService.getProfitHistory(),
      apiService.getSpreadsheetData()
    ])
    
    // ポートフォリオデータの処理
    if (portfolioResponse.status === 'fulfilled') {
      stocks.value = portfolioResponse.value.data.stocks || []
      console.log(`ポートフォリオデータ取得成功: ${stocks.value.length}銘柄`)
    } else {
      console.error('ポートフォリオデータ取得失敗:', portfolioResponse.reason)
      throw new Error(`ポートフォリオデータ取得エラー: ${portfolioResponse.reason?.message}`)
    }
    
    // 履歴データの処理
    let historyData = { periods: [], totalProfits: [], totalValues: [], totalCosts: [], avgPurchasePrices: [] }
    if (historyResponse.status === 'fulfilled') {
      historyData = historyResponse.value.data
      console.log(`履歴データ取得成功: ${historyData.periods?.length || 0}期間`)
    } else {
      console.error('履歴データ取得失敗:', historyResponse.reason)
      // 履歴データは必須ではないため、警告のみでエラーにしない
    }
    
    // APIレスポンスを期間別データに変換
    const allLabels = historyData.periods || []
    const allProfits = historyData.totalProfits || []
    const allValues = historyData.totalValues || []
    const allCosts = historyData.totalCosts || []
    const allCumulativeInvestments = historyData.cumulativeInvestments || historyData.totalCosts || []  // 累積投資額（後方互換性あり）
    
    // 期間別データの設定（証券アプリスタイル：累積投資額＋評価額）
    profitData.value = {
      '3months': {
        labels: allLabels.slice(-3),
        profits: allProfits.slice(-3),
        values: allValues.slice(-3),
        costs: allCosts.slice(-3),
        cumulativeInvestments: allCumulativeInvestments.slice(-3)  // 累積投資額
      },
      '6months': {
        labels: allLabels.slice(-6),
        profits: allProfits.slice(-6),
        values: allValues.slice(-6),
        costs: allCosts.slice(-6),
        cumulativeInvestments: allCumulativeInvestments.slice(-6)
      },
      '1year': {
        labels: allLabels.slice(-12),
        profits: allProfits.slice(-12),
        values: allValues.slice(-12),
        costs: allCosts.slice(-12),
        cumulativeInvestments: allCumulativeInvestments.slice(-12)
      },
      '2years': {
        labels: allLabels.slice(-24),
        profits: allProfits.slice(-24),
        values: allValues.slice(-24),
        costs: allCosts.slice(-24),
        cumulativeInvestments: allCumulativeInvestments.slice(-24)
      },
      '3years': {
        labels: allLabels.slice(-36),
        profits: allProfits.slice(-36),
        values: allValues.slice(-36),
        costs: allCosts.slice(-36),
        cumulativeInvestments: allCumulativeInvestments.slice(-36)
      },
      'all': {
        labels: allLabels,
        profits: allProfits,
        values: allValues,
        costs: allCosts,
        cumulativeInvestments: allCumulativeInvestments
      }
    }
    
    // 銘柄別データの設定（並列取得結果を使用）
    if (spreadsheetResponse.status === 'fulfilled') {
      const spreadsheetData = spreadsheetResponse.value.data.data || []
      console.log(`スプレッドシートデータ取得成功: ${spreadsheetData.length}レコード`)
      
      // 銘柄別にデータを集計
      const stockDataMap = {}
      spreadsheetData.forEach(row => {
        const stockCode = row.stock
        const date = row.label
        const profit = row.pl_value
        
        if (!stockDataMap[stockCode]) {
          stockDataMap[stockCode] = { labels: [], data: [] }
        }
        
        // 重複する日付は最新のものを使用
        const existingIndex = stockDataMap[stockCode].labels.indexOf(date)
        if (existingIndex !== -1) {
          stockDataMap[stockCode].data[existingIndex] = profit
        } else {
          stockDataMap[stockCode].labels.push(date)
          stockDataMap[stockCode].data.push(profit)
        }
      })
      
      // ソートして最新6ヶ月分のデータを使用
      Object.keys(stockDataMap).forEach(stockCode => {
        const stockData = stockDataMap[stockCode]
        const sortedIndices = stockData.labels
          .map((label, index) => ({ label, index }))
          .sort((a, b) => new Date(a.label) - new Date(b.label))
        
        stockData.labels = sortedIndices.slice(-6).map(item => item.label)
        stockData.data = sortedIndices.slice(-6).map(item => stockData.data[item.index])
      })
      
      stockProfitData.value = stockDataMap
    } else {
      console.error('銘柄別データ取得失敗:', spreadsheetResponse.reason)
      // エラー時も最小限のダミーデータを設定
      stockProfitData.value = stocks.value.reduce((acc, stock) => {
        acc[stock.name] = {
          labels: allLabels.slice(-6),
          data: Array(Math.min(6, allLabels.length)).fill(0)
        }
        return acc
      }, {})
    }
    
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

  // 損益推移（証券アプリスタイル：累積投資額＋評価額＋損益）
  const initialData = profitData.value[selectedPeriod.value]
  lineChartInstance = new Chart(lineChart.value, {
    type: 'line',
    data: {
      labels: initialData.labels,
      datasets: [
        {
          label: '累積投資額',
          data: initialData.cumulativeInvestments,
          borderColor: '#FF6384',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          fill: false,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6
        },
        {
          label: '評価額推移',
          data: initialData.values,
          borderColor: '#36A2EB',
          backgroundColor: 'rgba(54, 162, 235, 0.1)',
          fill: false,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6
        },
        {
          label: '損益推移',
          data: initialData.profits,
          borderColor: '#4BC0C0',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 5
        }
      ]
    },
    options: {
      responsive: true,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      scales: {
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

.error-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
}

.error-text {
  flex: 1;
}

.retry-button {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
  white-space: nowrap;
}

.retry-button:hover:not(:disabled) {
  background: #c82333;
}

.retry-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
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