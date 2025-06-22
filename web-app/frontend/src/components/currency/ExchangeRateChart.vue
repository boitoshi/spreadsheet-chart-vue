<template>
  <div class="exchange-rate-chart">
    <div class="chart-header">
      <h3>📈 為替レート推移</h3>
      <div class="chart-controls">
        <select v-model="selectedCurrency" @change="updateChart" class="currency-select">
          <option value="">全通貨</option>
          <option v-for="currency in availableCurrencies" :key="currency" :value="currency">
            {{ currency }}
          </option>
        </select>
        
        <select v-model="timePeriod" @change="updateChart" class="period-select">
          <option value="7">直近7日</option>
          <option value="30">直近30日</option>
          <option value="90">直近90日</option>
          <option value="365">直近1年</option>
        </select>
        
        <button @click="refreshData" class="refresh-btn" :disabled="loading">
          🔄 更新
        </button>
      </div>
    </div>
    
    <div class="chart-container" v-if="!loading">
      <canvas ref="chartCanvas"></canvas>
    </div>
    
    <div v-if="loading" class="loading">
      📊 為替レートデータを読み込み中...
    </div>
    
    <div v-if="error" class="error">
      ❌ {{ error }}
    </div>
    
    <!-- 通貨別サマリー -->
    <div class="rate-summary" v-if="latestRates.length > 0">
      <h4>💰 最新レート</h4>
      <div class="rates-grid">
        <div 
          v-for="rate in latestRates" 
          :key="rate.currency_pair"
          class="rate-card"
        >
          <div class="rate-pair">{{ rate.currency_pair }}</div>
          <div class="rate-value">{{ rate.rate.toFixed(2) }}円</div>
          <div class="rate-change" :class="rate.change_class">
            {{ rate.change_text }}
          </div>
          <div class="rate-date">{{ formatDate(rate.date) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'ExchangeRateChart',
  setup() {
    const chartCanvas = ref(null)
    const chart = ref(null)
    const selectedCurrency = ref('')
    const timePeriod = ref('30')
    const loading = ref(true)
    const error = ref('')
    const exchangeRateData = ref([])
    const latestRates = ref([])
    const availableCurrencies = ref(['USD/JPY', 'EUR/JPY', 'GBP/JPY', 'HKD/JPY'])

    // 日付フォーマット
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('ja-JP', { 
        month: 'short', 
        day: 'numeric' 
      })
    }

    // 為替レートデータ取得
    const fetchExchangeRateData = async () => {
      try {
        loading.value = true
        error.value = ''
        
        // 期間を計算
        const endDate = new Date()
        const startDate = new Date()
        startDate.setDate(endDate.getDate() - parseInt(timePeriod.value))
        
        const params = new URLSearchParams({
          start_date: startDate.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0]
        })
        
        if (selectedCurrency.value) {
          params.append('currency', selectedCurrency.value)
        }
        
        const response = await fetch(`/api/currency_rates/?${params}`)
        const data = await response.json()
        
        if (data.error) {
          throw new Error(data.error)
        }
        
        exchangeRateData.value = data.data
        processLatestRates(data.data)
        
      } catch (err) {
        error.value = `為替レートデータの取得に失敗しました: ${err.message}`
        console.error('Exchange rate fetch error:', err)
      } finally {
        loading.value = false
      }
    }

    // 最新レート処理
    const processLatestRates = (data) => {
      const ratesByPair = {}
      
      // 通貨ペア別に最新データを取得
      data.forEach(rate => {
        const pair = rate.currency_pair
        if (!ratesByPair[pair] || new Date(rate.date) > new Date(ratesByPair[pair].date)) {
          ratesByPair[pair] = rate
        }
      })
      
      // 変動率計算
      latestRates.value = Object.values(ratesByPair).map(rate => {
        const changeRate = rate.change_rate || 0
        return {
          ...rate,
          change_text: changeRate > 0 ? `+${changeRate.toFixed(2)}%` : `${changeRate.toFixed(2)}%`,
          change_class: changeRate > 0 ? 'positive' : changeRate < 0 ? 'negative' : 'neutral'
        }
      })
    }

    // チャート作成
    const createChart = () => {
      if (!chartCanvas.value || exchangeRateData.value.length === 0) return

      const ctx = chartCanvas.value.getContext('2d')
      
      // データを通貨ペア別にグループ化
      const groupedData = {}
      exchangeRateData.value.forEach(rate => {
        const pair = rate.currency_pair
        if (!groupedData[pair]) {
          groupedData[pair] = []
        }
        groupedData[pair].push({
          x: rate.date,
          y: rate.rate
        })
      })
      
      // データセット作成
      const datasets = Object.keys(groupedData).map((pair, index) => {
        const colors = [
          '#2196F3', // Blue
          '#4CAF50', // Green  
          '#FF9800', // Orange
          '#9C27B0', // Purple
          '#F44336', // Red
          '#00BCD4', // Cyan
        ]
        
        return {
          label: pair,
          data: groupedData[pair].sort((a, b) => new Date(a.x) - new Date(b.x)),
          borderColor: colors[index % colors.length],
          backgroundColor: colors[index % colors.length] + '20',
          borderWidth: 2,
          fill: false,
          tension: 0.1,
          pointRadius: 3,
          pointHoverRadius: 5
        }
      })

      // 既存チャートを破棄
      if (chart.value) {
        chart.value.destroy()
      }

      // 新しいチャート作成
      chart.value = new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: '為替レート推移',
              font: { size: 16 }
            },
            legend: {
              display: true,
              position: 'top'
            },
            tooltip: {
              mode: 'index',
              intersect: false,
              callbacks: {
                label: function(context) {
                  return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}円`
                }
              }
            }
          },
          scales: {
            x: {
              type: 'time',
              time: {
                unit: 'day',
                displayFormats: {
                  day: 'MM/DD'
                }
              },
              title: {
                display: true,
                text: '日付'
              }
            },
            y: {
              title: {
                display: true,
                text: 'レート (円)'
              },
              beginAtZero: false
            }
          },
          interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
          }
        }
      })
    }

    // チャート更新
    const updateChart = async () => {
      await fetchExchangeRateData()
      await nextTick()
      createChart()
    }

    // データ更新
    const refreshData = () => {
      updateChart()
    }

    onMounted(async () => {
      await fetchExchangeRateData()
      await nextTick()
      createChart()
    })

    return {
      chartCanvas,
      selectedCurrency,
      timePeriod,
      loading,
      error,
      latestRates,
      availableCurrencies,
      formatDate,
      updateChart,
      refreshData
    }
  }
}
</script>

<style scoped>
.exchange-rate-chart {
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
  margin-bottom: 20px;
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

.currency-select,
.period-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  font-size: 14px;
  cursor: pointer;
}

.refresh-btn {
  padding: 8px 15px;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #1976d2;
}

.refresh-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.chart-container {
  height: 400px;
  position: relative;
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

.rate-summary {
  margin-top: 30px;
  padding-top: 25px;
  border-top: 2px solid #f0f0f0;
}

.rate-summary h4 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
}

.rates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.rate-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #e9ecef;
  transition: transform 0.2s;
}

.rate-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.rate-pair {
  font-weight: bold;
  color: #333;
  font-size: 14px;
  margin-bottom: 8px;
}

.rate-value {
  font-size: 20px;
  font-weight: bold;
  color: #2196f3;
  margin-bottom: 5px;
}

.rate-change {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 5px;
}

.rate-change.positive {
  color: #4caf50;
}

.rate-change.negative {
  color: #f44336;
}

.rate-change.neutral {
  color: #666;
}

.rate-date {
  font-size: 11px;
  color: #666;
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
  
  .currency-select,
  .period-select {
    flex: 1;
    min-width: 0;
  }
  
  .chart-container {
    height: 300px;
  }
  
  .rates-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
}
</style>