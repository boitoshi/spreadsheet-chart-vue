import { ref, computed } from 'vue'
import { calculateProfitLoss, calculatePortfolioSummary } from '../utils/calculations.js'
import { apiService } from '../utils/api.js'

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
   * ポートフォリオデータをAPIから取得
   */
  const fetchPortfolioData = async (params = {}) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiService.getPortfolioData(params)
      holdings.value = response.data.stocks || []
      
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
      await apiService.updatePrice({
        stock: stockSymbol,
        price: newPrice,
        date: new Date().toISOString().split('T')[0]
      })
      
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
