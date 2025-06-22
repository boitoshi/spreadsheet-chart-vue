<template>
  <div class="currency-pie-chart">
    <div class="chart-header">
      <h3>🥧 通貨別ポートフォリオ構成</h3>
      <div class="chart-controls">
        <button 
          @click="chartType = 'currency'" 
          :class="{ active: chartType === 'currency' }"
          class="chart-type-btn"
        >
          通貨別
        </button>
        <button 
          @click="chartType = 'region'" 
          :class="{ active: chartType === 'region' }"
          class="chart-type-btn"
        >
          地域別
        </button>
        <button @click="refreshData" class="refresh-btn" :disabled="loading">
          🔄 更新
        </button>
      </div>
    </div>
    
    <div class="chart-content" v-if="!loading">
      <div class="chart-container">
        <canvas ref="chartCanvas"></canvas>
      </div>
      
      <div class="chart-legend">
        <div class="legend-header">
          <h4>📊 構成詳細</h4>
          <div class="total-amount">
            総額: {{ formatCurrency(totalValue) }}円
          </div>
        </div>
        
        <div class="legend-items">
          <div 
            v-for="(item, index) in chartData" 
            :key="item.label"
            class="legend-item"
            @mouseover="highlightSegment(index)"
            @mouseleave="unhighlightSegment()"
          >
            <div class="legend-color" :style="{ backgroundColor: item.color }"></div>
            <div class="legend-info">
              <div class="legend-label">
                <span class="flag">{{ item.flag }}</span>
                {{ item.label }}
              </div>
              <div class="legend-values">
                <span class="amount">{{ formatCurrency(item.value) }}円</span>
                <span class="percentage">({{ item.percentage.toFixed(1) }}%)</span>
              </div>
              <div class="legend-details" v-if="item.details">
                <span class="stocks-count">{{ item.details.stocks_count }}銘柄</span>
                <span class="region" v-if="item.details.region">{{ item.details.region }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="loading">
      📊 ポートフォリオデータを読み込み中...
    </div>
    
    <div v-if="error" class="error">
      ❌ {{ error }}
    </div>
    
    <!-- 詳細情報パネル -->
    <div class="details-panel" v-if="selectedSegment">
      <h4>🔍 {{ selectedSegment.label }} 詳細</h4>
      <div class="segment-details">
        <div class="detail-row">
          <span class="detail-label">投資額:</span>
          <span class="detail-value">{{ formatCurrency(selectedSegment.value) }}円</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">構成比率:</span>
          <span class="detail-value">{{ selectedSegment.percentage.toFixed(1) }}%</span>
        </div>
        <div class="detail-row" v-if="selectedSegment.details">
          <span class="detail-label">銘柄数:</span>
          <span class="detail-value">{{ selectedSegment.details.stocks_count }}銘柄</span>
        </div>
        <div class="detail-row" v-if="selectedSegment.stocks">
          <span class="detail-label">含まれる銘柄:</span>
          <div class="stocks-list">
            <span 
              v-for="stock in selectedSegment.stocks" 
              :key="stock.symbol"
              class="stock-tag"
            >
              {{ stock.name }} ({{ stock.symbol }})
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'CurrencyPieChart',
  setup() {
    const chartCanvas = ref(null)
    const chart = ref(null)
    const chartType = ref('currency') // 'currency' or 'region'
    const loading = ref(true)
    const error = ref('')
    const portfolioData = ref([])
    const currencySummary = ref([])
    const totalValue = ref(0)
    const selectedSegment = ref(null)

    // 通貨・地域設定
    const currencyRegions = {
      'JPY': { region: '日本', flag: '🇯🇵' },
      'USD': { region: '北米', flag: '🇺🇸' },
      'EUR': { region: 'ヨーロッパ', flag: '🇪🇺' },
      'GBP': { region: 'イギリス', flag: '🇬🇧' },
      'HKD': { region: 'アジア', flag: '🇭🇰' },
      'AUD': { region: 'オセアニア', flag: '🇦🇺' },
      'CAD': { region: '北米', flag: '🇨🇦' },
      'SGD': { region: 'アジア', flag: '🇸🇬' }
    }

    // カラーパレット
    const colorPalette = [
      '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
      '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
      '#4BC0C0', '#FF6384', '#36A2EB', '#FFCE56'
    ]

    // チャートデータ計算
    const chartData = computed(() => {
      if (chartType.value === 'currency') {
        return currencySummary.value.map((currency, index) => ({
          label: currency.currency,
          value: currency.total_cost,
          percentage: currency.percentage,
          color: colorPalette[index % colorPalette.length],
          flag: currencyRegions[currency.currency]?.flag || '💰',
          details: {
            stocks_count: currency.stocks_count,
            region: currencyRegions[currency.currency]?.region
          },
          stocks: portfolioData.value.filter(stock => stock.currency === currency.currency)
        }))
      } else {
        // 地域別集計
        const regionSummary = {}
        portfolioData.value.forEach(stock => {
          const region = currencyRegions[stock.currency]?.region || 'その他'
          const value = stock.purchase_price * stock.shares
          
          if (!regionSummary[region]) {
            regionSummary[region] = {
              region,
              total_cost: 0,
              stocks_count: 0,
              currencies: new Set(),
              stocks: []
            }
          }
          
          regionSummary[region].total_cost += value
          regionSummary[region].stocks_count += 1
          regionSummary[region].currencies.add(stock.currency)
          regionSummary[region].stocks.push(stock)
        })
        
        return Object.values(regionSummary).map((region, index) => ({
          label: region.region,
          value: region.total_cost,
          percentage: (region.total_cost / totalValue.value * 100),
          color: colorPalette[index % colorPalette.length],
          flag: getRegionFlag(region.region),
          details: {
            stocks_count: region.stocks_count,
            currencies: Array.from(region.currencies).join(', ')
          },
          stocks: region.stocks
        }))
      }
    })

    // 地域フラグ取得
    const getRegionFlag = (region) => {
      const flags = {
        '日本': '🇯🇵',
        '北米': '🌎',
        'ヨーロッパ': '🇪🇺',
        'イギリス': '🇬🇧',
        'アジア': '🌏',
        'オセアニア': '🇦🇺'
      }
      return flags[region] || '🌍'
    }

    // 数値フォーマット
    const formatCurrency = (value) => {
      if (typeof value !== 'number') return '0'
      return new Intl.NumberFormat('ja-JP').format(Math.round(value))
    }

    // データ取得
    const fetchData = async () => {
      try {
        loading.value = true
        error.value = ''
        
        // ポートフォリオデータ取得
        const portfolioResponse = await fetch('/api/portfolio/')
        const portfolioResult = await portfolioResponse.json()
        
        if (portfolioResult.error) {
          throw new Error(portfolioResult.error)
        }
        
        portfolioData.value = portfolioResult.data
        
        // 通貨サマリー取得
        const summaryResponse = await fetch('/api/currency_summary/')
        const summaryResult = await summaryResponse.json()
        
        if (summaryResult.error) {
          throw new Error(summaryResult.error)
        }
        
        currencySummary.value = summaryResult.data
        totalValue.value = summaryResult.total_value
        
      } catch (err) {
        error.value = `データの取得に失敗しました: ${err.message}`
        console.error('Data fetch error:', err)
      } finally {
        loading.value = false
      }
    }

    // チャート作成
    const createChart = () => {
      if (!chartCanvas.value || chartData.value.length === 0) return

      const ctx = chartCanvas.value.getContext('2d')

      // 既存チャートを破棄
      if (chart.value) {
        chart.value.destroy()
      }

      // 新しいチャート作成
      chart.value = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: chartData.value.map(item => item.label),
          datasets: [{
            data: chartData.value.map(item => item.value),
            backgroundColor: chartData.value.map(item => item.color),
            borderColor: '#ffffff',
            borderWidth: 2,
            hoverOffset: 10
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const item = chartData.value[context.dataIndex]
                  return `${item.label}: ${formatCurrency(item.value)}円 (${item.percentage.toFixed(1)}%)`
                }
              }
            }
          },
          onClick: (event, elements) => {
            if (elements.length > 0) {
              const index = elements[0].index
              selectedSegment.value = chartData.value[index]
            }
          },
          onHover: (event, elements) => {
            event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default'
          }
        }
      })
    }

    // セグメントハイライト
    const highlightSegment = (index) => {
      if (chart.value) {
        chart.value.setActiveElements([{ datasetIndex: 0, index }])
        chart.value.update('none')
      }
    }

    const unhighlightSegment = () => {
      if (chart.value) {
        chart.value.setActiveElements([])
        chart.value.update('none')
      }
    }

    // データ更新
    const refreshData = async () => {
      await fetchData()
      await nextTick()
      createChart()
    }

    // チャートタイプ変更を監視
    watch(chartType, async () => {
      await nextTick()
      createChart()
    })

    onMounted(async () => {
      await fetchData()
      await nextTick()
      createChart()
    })

    return {
      chartCanvas,
      chartType,
      loading,
      error,
      chartData,
      totalValue,
      selectedSegment,
      formatCurrency,
      highlightSegment,
      unhighlightSegment,
      refreshData
    }
  }
}
</script>

<style scoped>
.currency-pie-chart {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  flex-wrap: wrap;
  gap: 15px;
}

.chart-header h3 {
  margin: 0;
  color: #333;
  font-size: 20px;
}

.chart-controls {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.chart-type-btn {
  padding: 8px 15px;
  border: 2px solid #e0e0e0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
  font-size: 14px;
}

.chart-type-btn:hover {
  background: #f5f5f5;
}

.chart-type-btn.active {
  background: #2196f3;
  color: white;
  border-color: #2196f3;
}

.refresh-btn {
  padding: 8px 15px;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #388e3c;
}

.refresh-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.chart-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  align-items: start;
}

.chart-container {
  height: 350px;
  position: relative;
}

.chart-legend {
  padding-left: 20px;
}

.legend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f0f0f0;
}

.legend-header h4 {
  margin: 0;
  color: #333;
  font-size: 16px;
}

.total-amount {
  font-weight: bold;
  color: #2196f3;
  font-size: 14px;
}

.legend-items {
  max-height: 300px;
  overflow-y: auto;
}

.legend-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.legend-item:hover {
  background: #f8f9fa;
}

.legend-color {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  margin-right: 12px;
  flex-shrink: 0;
  margin-top: 2px;
}

.legend-info {
  flex: 1;
}

.legend-label {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.flag {
  margin-right: 5px;
}

.legend-values {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}

.amount {
  font-weight: bold;
  color: #2196f3;
}

.percentage {
  color: #666;
  font-size: 14px;
}

.legend-details {
  font-size: 12px;
  color: #666;
  display: flex;
  gap: 10px;
}

.loading {
  text-align: center;
  padding: 50px;
  color: #666;
  font-size: 16px;
}

.error {
  text-align: center;
  padding: 20px;
  color: #f44336;
  background: #ffebee;
  border-radius: 8px;
  margin: 20px 0;
}

.details-panel {
  margin-top: 25px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #2196f3;
}

.details-panel h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 16px;
}

.segment-details {
  display: grid;
  gap: 10px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.detail-label {
  font-weight: 500;
  color: #666;
  min-width: 80px;
}

.detail-value {
  font-weight: bold;
  color: #333;
  text-align: right;
  flex: 1;
}

.stocks-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 5px;
}

.stock-tag {
  background: #e3f2fd;
  color: #1976d2;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

@media (max-width: 1024px) {
  .chart-content {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .chart-legend {
    padding-left: 0;
  }
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .chart-controls {
    width: 100%;
    justify-content: space-between;
  }
  
  .chart-container {
    height: 250px;
  }
  
  .legend-items {
    max-height: none;
  }
  
  .detail-row {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .detail-value {
    text-align: left;
  }
}
</style>