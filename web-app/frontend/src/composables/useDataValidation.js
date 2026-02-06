import { ref, computed } from 'vue'
import { apiService } from '../utils/api.js'

/**
 * データ検証・品質保証用Composable
 * バックエンドのデータ検証APIと連携して、投資データの品質を監視
 */
export const useDataValidation = () => {
  const validationResult = ref(null)
  const loading = ref(false)
  const error = ref(null)
  
  // 検証結果のステータス計算
  const validationStatus = computed(() => {
    if (!validationResult.value) return null
    
    const result = validationResult.value
    const errorCount = result.errors?.length || 0
    const warningCount = result.warnings?.length || 0
    
    if (errorCount > 0) {
      return {
        level: 'error',
        message: `重要なデータエラーが${errorCount}件あります`,
        color: '#ef4444',
        icon: '⚠️'
      }
    }
    
    if (warningCount > 0) {
      return {
        level: 'warning', 
        message: `データに${warningCount}件の注意点があります`,
        color: '#f59e0b',
        icon: '⚡'
      }
    }
    
    return {
      level: 'success',
      message: 'データ品質に問題ありません',
      color: '#22c55e', 
      icon: '✅'
    }
  })
  
  // データ整合性チェック
  const isDataConsistent = computed(() => {
    if (!validationResult.value) return null
    return validationResult.value.is_valid
  })
  
  // 要注意な異常値の検出
  const criticalIssues = computed(() => {
    if (!validationResult.value) return []
    
    const issues = []
    const errors = validationResult.value.errors || []
    const warnings = validationResult.value.warnings || []
    
    // エラーレベルの問題を優先
    errors.forEach(error => {
      issues.push({
        type: 'error',
        message: error,
        severity: 'high',
        action: '至急修正が必要です'
      })
    })
    
    // 投資に影響する可能性のある警告を抽出
    const criticalWarnings = warnings.filter(warning => 
      warning.includes('価格データが不足') || 
      warning.includes('取得日より古い') ||
      warning.includes('未登録')
    )
    
    criticalWarnings.forEach(warning => {
      issues.push({
        type: 'warning',
        message: warning,
        severity: 'medium',
        action: '確認をお勧めします'
      })
    })
    
    return issues
  })
  
  // 投資データの統計サマリー
  const dataSummary = computed(() => {
    if (!validationResult.value?.summary) return null
    
    const summary = validationResult.value.summary
    return {
      totalStocks: summary.total_stocks || 0,
      totalTransactions: summary.total_transactions || 0,
      totalPriceRecords: summary.total_price_records || 0,
      dateRange: summary.date_range || {},
      lastValidated: summary.validation_date ? 
        new Date(summary.validation_date).toLocaleString('ja-JP') : null
    }
  })
  
  /**
   * データ検証を実行
   */
  const validateData = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiService.validatePortfolioData()
      validationResult.value = response.data
      
      console.log('データ検証完了:', {
        valid: validationResult.value.is_valid,
        errors: validationResult.value.errors?.length,
        warnings: validationResult.value.warnings?.length
      })
      
    } catch (err) {
      error.value = `データ検証エラー: ${err.message}`
      console.error('データ検証でエラーが発生:', err)
      
      // フォールバック: 基本的な検証失敗情報を設定
      validationResult.value = {
        is_valid: false,
        errors: [error.value],
        warnings: [],
        summary: {}
      }
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 特定の投資指標の異常値をチェック
   * @param {Object} portfolioData - ポートフォリオデータ
   */
  const checkInvestmentAnomalies = (portfolioData) => {
    if (!portfolioData?.stocks) return []
    
    const anomalies = []
    
    portfolioData.stocks.forEach(stock => {
      // 1. 異常に高い損益率 (±100%を超える)
      const profitRate = ((stock.profit / stock.totalCost) * 100)
      if (Math.abs(profitRate) > 100) {
        anomalies.push({
          type: 'price_anomaly',
          stock: stock.name,
          message: `${stock.name}: 損益率が${profitRate.toFixed(1)}%と異常値です`,
          value: profitRate,
          severity: Math.abs(profitRate) > 200 ? 'high' : 'medium'
        })
      }
      
      // 2. 現在価格が0の銘柄
      if (stock.currentPrice === 0) {
        anomalies.push({
          type: 'missing_price',
          stock: stock.name,
          message: `${stock.name}: 現在価格が取得できていません`,
          severity: 'high'
        })
      }
      
      // 3. 異常に古い取引日
      const latestTransaction = stock.transactions?.reduce((latest, tx) => {
        const txDate = new Date(tx.date)
        const latestDate = new Date(latest.date)
        return txDate > latestDate ? tx : latest
      }, stock.transactions[0])
      
      if (latestTransaction) {
        const daysSinceLastTransaction = (new Date() - new Date(latestTransaction.date)) / (1000 * 60 * 60 * 24)
        if (daysSinceLastTransaction > 365) {
          anomalies.push({
            type: 'old_transaction',
            stock: stock.name,
            message: `${stock.name}: 最新取引から${Math.floor(daysSinceLastTransaction)}日経過`,
            severity: 'low'
          })
        }
      }
    })
    
    return anomalies
  }
  
  return {
    validationResult,
    loading,
    error,
    validationStatus,
    isDataConsistent,
    criticalIssues,
    dataSummary,
    validateData,
    checkInvestmentAnomalies
  }
}

/**
 * リアルタイム投資データ監視用Composable
 * 定期的にデータ品質をチェックし、異常を検出
 */
export const useInvestmentDataMonitor = () => {
  const { validateData, validationStatus, criticalIssues } = useDataValidation()
  const monitoringActive = ref(false)
  const lastCheckTime = ref(null)
  let monitorInterval = null
  
  /**
   * 定期監視を開始 (デフォルト: 5分間隔)
   * @param {number} intervalMinutes - 監視間隔（分）
   */
  const startMonitoring = async (intervalMinutes = 5) => {
    if (monitoringActive.value) return
    
    monitoringActive.value = true
    
    // 初回チェック
    await validateData()
    lastCheckTime.value = new Date()
    
    // 定期実行設定
    monitorInterval = setInterval(async () => {
      try {
        await validateData()
        lastCheckTime.value = new Date()
        
        // 重要な問題が検出された場合の通知
        if (criticalIssues.value.some(issue => issue.severity === 'high')) {
          console.warn('投資データに重要な問題が検出されました:', criticalIssues.value)
        }
      } catch (err) {
        console.error('定期データ監視でエラー:', err)
      }
    }, intervalMinutes * 60 * 1000)
    
    console.log(`投資データ監視を開始しました（${intervalMinutes}分間隔）`)
  }
  
  /**
   * 定期監視を停止
   */
  const stopMonitoring = () => {
    if (monitorInterval) {
      clearInterval(monitorInterval)
      monitorInterval = null
    }
    monitoringActive.value = false
    console.log('投資データ監視を停止しました')
  }
  
  return {
    monitoringActive,
    lastCheckTime,
    validationStatus,
    criticalIssues,
    startMonitoring,
    stopMonitoring,
    validateData
  }
}