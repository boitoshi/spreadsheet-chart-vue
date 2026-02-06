/**
 * ポートフォリオの損益計算ロジック
 */

/**
 * 投資損益を計算する関数
 * @param {number} purchasePrice - 取得価格
 * @param {number} currentPrice - 現在価格
 * @param {number} quantity - 保有数量
 * @returns {Object} 損益計算結果
 */
export const calculateProfitLoss = (purchasePrice, currentPrice, quantity = 1) => {
  const totalPurchase = purchasePrice * quantity
  const totalCurrent = currentPrice * quantity
  const profitLoss = totalCurrent - totalPurchase
  const profitLossRate = totalPurchase > 0 ? ((profitLoss / totalPurchase) * 100) : 0
  
  return {
    totalPurchase,      // 総取得額
    totalCurrent,       // 総評価額
    profitLoss,         // 損益額
    profitLossRate,     // 損益率(%)
    isProfit: profitLoss >= 0  // 利益フラグ
  }
}

/**
 * ポートフォリオ全体の集計を計算
 * @param {Array} holdings - 保有銘柄配列
 * @returns {Object} ポートフォリオサマリー
 */
export const calculatePortfolioSummary = (holdings) => {
  const summary = holdings.reduce((acc, holding) => {
    const calc = calculateProfitLoss(
      holding.purchasePrice, 
      holding.currentPrice, 
      holding.quantity
    )
    
    acc.totalPurchase += calc.totalPurchase
    acc.totalCurrent += calc.totalCurrent
    acc.totalProfitLoss += calc.profitLoss
    
    return acc
  }, {
    totalPurchase: 0,
    totalCurrent: 0,
    totalProfitLoss: 0
  })
  
  summary.totalProfitLossRate = summary.totalPurchase > 0
    ? (summary.totalProfitLoss / summary.totalPurchase) * 100
    : 0
  
  return summary
}
