<template>
  <div class="currency-portfolio">
    <div class="header">
      <h2>💰 通貨別ポートフォリオ</h2>
      <div class="total-value">
        総評価額: {{ formatCurrency(totalValue) }}円
      </div>
    </div>

    <div class="currency-grid">
      <!-- 通貨別サマリーカード -->
      <div 
        v-for="currency in currencySummary" 
        :key="currency.currency"
        class="currency-card"
        :class="{ 'foreign': currency.is_foreign }"
      >
        <div class="currency-header">
          <span class="currency-flag">
            {{ currency.is_foreign ? '🌏' : '🇯🇵' }}
          </span>
          <h3>{{ currency.currency }}</h3>
          <span class="percentage">{{ currency.percentage.toFixed(1) }}%</span>
        </div>
        
        <div class="currency-details">
          <div class="detail-item">
            <span class="label">取得額:</span>
            <span class="value">{{ formatCurrency(currency.total_cost) }}円</span>
          </div>
          <div class="detail-item">
            <span class="label">銘柄数:</span>
            <span class="value">{{ currency.stocks_count }}銘柄</span>
          </div>
          <div class="detail-item" v-if="currency.is_foreign">
            <span class="label">為替影響:</span>
            <span class="value exchange-rate">
              {{ getCurrencyRate(currency.currency) }}円
            </span>
          </div>
        </div>

        <div class="progress-bar">
          <div 
            class="progress-fill"
            :style="{ width: currency.percentage + '%' }"
            :class="currency.is_foreign ? 'foreign-fill' : 'domestic-fill'"
          ></div>
        </div>
      </div>
    </div>

    <!-- 通貨別銘柄詳細 -->
    <div class="currency-details-section">
      <h3>📊 通貨別銘柄詳細</h3>
      <div class="currency-tabs">
        <button 
          v-for="currency in currencySummary" 
          :key="currency.currency"
          @click="selectedCurrency = currency.currency"
          :class="{ active: selectedCurrency === currency.currency }"
          class="tab-button"
        >
          {{ currency.currency }} ({{ currency.stocks_count }})
        </button>
      </div>

      <div class="stocks-table" v-if="selectedCurrencyStocks.length > 0">
        <table>
          <thead>
            <tr>
              <th>銘柄</th>
              <th>銘柄コード</th>
              <th>取得価格</th>
              <th>保有株数</th>
              <th>取得額</th>
              <th>外国株</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stock in selectedCurrencyStocks" :key="stock.symbol">
              <td class="stock-name">{{ stock.name }}</td>
              <td class="stock-symbol">{{ stock.symbol }}</td>
              <td class="price">{{ formatCurrency(stock.purchase_price) }}</td>
              <td class="shares">{{ stock.shares.toLocaleString() }}</td>
              <td class="total">{{ formatCurrency(stock.purchase_price * stock.shares) }}円</td>
              <td class="foreign-flag">
                <span :class="{ 'foreign': stock.is_foreign }">
                  {{ stock.is_foreign ? '🌏' : '🇯🇵' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'

export default {
  name: 'CurrencyPortfolio',
  setup() {
    const currencySummary = ref([])
    const portfolioData = ref([])
    const exchangeRates = ref({})
    const totalValue = ref(0)
    const selectedCurrency = ref('JPY')
    const loading = ref(true)
    const error = ref('')

    // 選択された通貨の銘柄リスト
    const selectedCurrencyStocks = computed(() => {
      return portfolioData.value.filter(stock => stock.currency === selectedCurrency.value)
    })

    // 通貨フォーマット
    const formatCurrency = (value) => {
      if (typeof value !== 'number') return '0'
      return new Intl.NumberFormat('ja-JP').format(Math.round(value))
    }

    // 為替レート取得
    const getCurrencyRate = (currency) => {
      const rate = exchangeRates.value[`${currency}/JPY`]
      return rate ? `1${currency} = ${rate.toFixed(2)}` : '取得中...'
    }

    // ポートフォリオデータ取得
    const fetchPortfolioData = async () => {
      try {
        const response = await fetch('/api/portfolio/')
        const data = await response.json()
        
        if (data.error) {
          throw new Error(data.error)
        }
        
        portfolioData.value = data.data
        await fetchCurrencySummary()
        await fetchExchangeRates()
        
      } catch (err) {
        error.value = `ポートフォリオデータの取得に失敗しました: ${err.message}`
        console.error('Portfolio fetch error:', err)
      } finally {
        loading.value = false
      }
    }

    // 通貨サマリー取得
    const fetchCurrencySummary = async () => {
      try {
        const response = await fetch('/api/currency_summary/')
        const data = await response.json()
        
        if (data.error) {
          throw new Error(data.error)
        }
        
        currencySummary.value = data.data.sort((a, b) => b.total_cost - a.total_cost)
        totalValue.value = data.total_value
        
        // デフォルトで最初の通貨を選択
        if (currencySummary.value.length > 0) {
          selectedCurrency.value = currencySummary.value[0].currency
        }
        
      } catch (err) {
        error.value = `通貨サマリーの取得に失敗しました: ${err.message}`
        console.error('Currency summary fetch error:', err)
      }
    }

    // 為替レート取得
    const fetchExchangeRates = async () => {
      try {
        const response = await fetch('/api/currency_rates/')
        const data = await response.json()
        
        if (data.error) {
          console.warn('為替レートの取得に失敗:', data.error)
          return
        }
        
        // 最新の為替レートを取得
        const ratesMap = {}
        data.data.forEach(rate => {
          ratesMap[rate.currency_pair] = rate.rate
        })
        
        exchangeRates.value = ratesMap
        
      } catch (err) {
        console.warn('為替レート取得エラー:', err)
      }
    }

    onMounted(() => {
      fetchPortfolioData()
    })

    return {
      currencySummary,
      portfolioData,
      exchangeRates,
      totalValue,
      selectedCurrency,
      selectedCurrencyStocks,
      loading,
      error,
      formatCurrency,
      getCurrencyRate
    }
  }
}
</script>

<style scoped>
.currency-portfolio {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.header h2 {
  margin: 0;
  color: #333;
  font-size: 24px;
}

.total-value {
  font-size: 18px;
  font-weight: bold;
  color: #2c5aa0;
  background: #f0f8ff;
  padding: 10px 15px;
  border-radius: 8px;
}

.currency-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.currency-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 2px solid #e0e0e0;
  transition: transform 0.2s, box-shadow 0.2s;
}

.currency-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
}

.currency-card.foreign {
  border-left: 4px solid #ff9800;
}

.currency-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.currency-flag {
  font-size: 24px;
  margin-right: 10px;
}

.currency-header h3 {
  margin: 0;
  flex: 1;
  font-size: 20px;
  color: #333;
}

.percentage {
  background: #e3f2fd;
  color: #1976d2;
  padding: 5px 10px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 14px;
}

.currency-details {
  margin-bottom: 15px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.label {
  color: #666;
  font-size: 14px;
}

.value {
  font-weight: bold;
  color: #333;
}

.exchange-rate {
  color: #ff9800;
  font-size: 12px;
}

.progress-bar {
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.domestic-fill {
  background: linear-gradient(90deg, #4caf50, #81c784);
}

.foreign-fill {
  background: linear-gradient(90deg, #ff9800, #ffb74d);
}

.currency-details-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.currency-details-section h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 20px;
}

.currency-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.tab-button {
  padding: 10px 15px;
  border: 2px solid #e0e0e0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.tab-button:hover {
  background: #f5f5f5;
}

.tab-button.active {
  background: #2196f3;
  color: white;
  border-color: #2196f3;
}

.stocks-table {
  overflow-x: auto;
}

.stocks-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.stocks-table th,
.stocks-table td {
  padding: 12px 8px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.stocks-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #333;
  position: sticky;
  top: 0;
}

.stock-name {
  font-weight: 600;
  color: #333;
}

.stock-symbol {
  font-family: monospace;
  color: #666;
  font-size: 12px;
}

.price, .total {
  text-align: right;
  font-family: monospace;
}

.shares {
  text-align: right;
}

.foreign-flag .foreign {
  font-size: 16px;
}

@media (max-width: 768px) {
  .currency-portfolio {
    padding: 15px;
  }
  
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .currency-grid {
    grid-template-columns: 1fr;
  }
  
  .currency-tabs {
    flex-direction: column;
  }
  
  .stocks-table {
    font-size: 12px;
  }
  
  .stocks-table th,
  .stocks-table td {
    padding: 8px 4px;
  }
}
</style>