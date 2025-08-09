import axios from 'axios'

// API ベースURL の設定
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Axios インスタンスの作成
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// リクエストインターセプター
api.interceptors.request.use(
  (config) => {
    // 開発環境でのログ出力
    if (import.meta.env.DEV) {
      console.log('API Request:', config.method?.toUpperCase(), config.url)
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// レスポンスインターセプター
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // エラーハンドリング
    if (error.response?.status === 404) {
      console.error('API endpoint not found:', error.config?.url)
    } else if (error.response?.status >= 500) {
      console.error('Server error:', error.response?.status)
    } else if (error.code === 'ECONNABORTED') {
      console.error('Request timeout')
    }
    return Promise.reject(error)
  }
)

// 汎用: 404 の場合にフォールバックパスへリトライ
async function getWithFallback(paths = [], params = {}) {
  const qs = new URLSearchParams(params).toString()
  let lastErr
  for (const p of paths) {
    try {
      const url = qs ? `${p}?${qs}` : p
      return await api.get(url)
    } catch (err) {
      if (err?.response?.status === 404) {
        lastErr = err
        continue
      }
      throw err
    }
  }
  throw lastErr || new Error('All fallback GET paths failed')
}

async function postWithFallback(paths = [], data = {}) {
  let lastErr
  for (const p of paths) {
    try {
      return await api.post(p, data)
    } catch (err) {
      if (err?.response?.status === 404) {
        lastErr = err
        continue
      }
      throw err
    }
  }
  throw lastErr || new Error('All fallback POST paths failed')
}

// API エンドポイント関数
export const apiService = {
  // スプレッドシートデータを取得
  getSpreadsheetData: (params = {}) => {
    return getWithFallback([
      '/api/v1/data/records/',
      '/get_data/'
    ], params)
  },
  
  // ポートフォリオデータを取得
  getPortfolioData: (params = {}) => {
    return getWithFallback([
      '/api/v1/portfolio/',
      '/api/portfolio/'
    ], params)
  },
  
  // 銘柄別履歴データを取得
  getStockHistory: (stockName, params = {}) => {
    return getWithFallback([
      `/api/v1/portfolio/stock/${stockName}/`,
      `/api/portfolio/stock/${stockName}/`
    ], params)
  },
  
  // 損益推移データを取得
  getProfitHistory: (params = {}) => {
    return getWithFallback([
      '/api/v1/portfolio/history/',
      '/api/portfolio/history/'
    ], params)
  },
  
  // 手動価格更新
  updatePrice: (data) => {
    return postWithFallback([
      '/api/v1/manual/update/',
      '/api/manual_update/'
    ], data)
  },
  
  // データ品質検証
  validatePortfolioData: () => {
    return getWithFallback([
      '/api/v1/portfolio/validate/',
      '/api/portfolio/validate/'
    ])
  }
}

export default api
