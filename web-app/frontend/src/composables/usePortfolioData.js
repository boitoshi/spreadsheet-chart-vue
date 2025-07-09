import { ref, computed } from 'vue'
import { calculateProfitLoss, calculatePortfolioSummary } from '../utils/calculations.js'

/**
 * ポートフォリオデータ管理用Composable
 */
export const usePortfolioData = () => {
  const holdings = ref([])
  const loading = ref(false)
  const error = ref(null)
  
  // 計算されたポートフォリオサマリー
  const portfolioSummary = computed(() => {
    if (!holdings.value.length) return null
    return calculatePortfolioSummary(holdings.value)
  })
  
  // 銘柄別損益データ
  const holdingsWithCalc = computed(() => {
    return holdings.value.map(holding => ({
      ...holding,
      ...calculateProfitLoss(holding.purchasePrice, holding.currentPrice, holding.quantity)
    }))
  })
  
  /**
   * ダミーデータを取得（バックエンドなし開発用）
   */
  const fetchPortfolioData = async (params = {}) => {
    loading.value = true
    error.value = null
    
    try {
      // ダミーデータを設定
      const dummyData = [
        {
          stock: 'トヨタ自動車',
          quantity: 100,
          purchasePrice: 2500,
          currentPrice: 2800
        },
        {
          stock: 'ソフトバンク',
          quantity: 200,
          purchasePrice: 1200,
          currentPrice: 1150
        },
        {
          stock: '任天堂',
          quantity: 50,
          purchasePrice: 5600,
          currentPrice: 6200
        },
        {
          stock: 'DeNA',
          quantity: 150,
          purchasePrice: 2100,
          currentPrice: 2350
        }
      ]
      
      // 実際のAPIを模擬した遅延
      await new Promise(resolve => setTimeout(resolve, 500))
      
      holdings.value = dummyData
      
    } catch (err) {
      error.value = err.message
      console.error('ポートフォリオデータ取得エラー:', err)
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 手動で価格を更新
   */
  const updatePrice = async (stockSymbol, newPrice) => {
    try {
      const response = await fetch('/api/manual_update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          stock: stockSymbol,
          price: newPrice,
          date: new Date().toISOString().split('T')[0]
        })
      })
      
      if (!response.ok) {
        throw new Error('価格更新に失敗しました')
      }
      
      // データを再取得
      await fetchPortfolioData()
      
    } catch (err) {
      error.value = err.message
      throw err
    }
  }
  
  return {
    holdings,
    loading,
    error,
    portfolioSummary,
    holdingsWithCalc,
    fetchPortfolioData,
    updatePrice
  }
}
