import { ref, computed } from 'vue'
// バックエンドを単一の計算ソースにするため、
// フロント側の再計算は最小限に留める
import { apiService } from '../utils/api.js'

/**
 * ポートフォリオデータ管理用Composable
 */
export const usePortfolioData = () => {
  const holdings = ref([])
  const loading = ref(false)
  const error = ref(null)
  
  // サーバ値からサマリーを算出（totalCost/currentValue/profit ベース）
  const portfolioSummary = computed(() => {
    if (!holdings.value.length) return null

    const totals = holdings.value.reduce((acc, h) => {
      const totalCost = Number(h.totalCost ?? 0)
      const currentValue = Number(h.currentValue ?? 0)
      const profit = Number(h.profit ?? (currentValue - totalCost))
      acc.totalPurchase += totalCost
      acc.totalCurrent += currentValue
      acc.totalProfitLoss += profit
      return acc
    }, { totalPurchase: 0, totalCurrent: 0, totalProfitLoss: 0 })

    const rateBase = totals.totalPurchase
    const totalProfitLossRate = rateBase > 0 ? (totals.totalProfitLoss / rateBase) * 100 : 0

    return { ...totals, totalProfitLossRate }
  })
  
  // 銘柄別損益データ（バックエンド値を反映し、必要最小限の派生値のみ計算）
  const holdingsWithCalc = computed(() => {
    return holdings.value.map(h => {
      const quantity = Number(h.quantity ?? 0)
      const avgPrice = Number(h.avgPrice ?? 0)
      const currentPrice = Number(h.currentPrice ?? 0)
      const totalPurchase = Number(h.totalCost ?? quantity * avgPrice)
      const totalCurrent = Number(h.currentValue ?? quantity * currentPrice)
      const profitLoss = Number(h.profit ?? (totalCurrent - totalPurchase))
      const profitLossRate = totalPurchase > 0 ? (profitLoss / totalPurchase) * 100 : 0

      return {
        ...h,
        // 既存UI互換のためのフィールド名を付与
        totalPurchase,
        totalCurrent,
        profitLoss,
        profitLossRate
      }
    })
  })
  
  /**
   * ポートフォリオデータをAPIから取得
   */
  const fetchPortfolioData = async (params = {}) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiService.getPortfolioData(params)
      // サーバ整形済みデータをそのまま保持
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
