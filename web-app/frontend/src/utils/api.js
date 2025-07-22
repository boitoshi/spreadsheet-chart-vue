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

// API エンドポイント関数
export const apiService = {
  // スプレッドシートデータを取得
  getSpreadsheetData: (params = {}) => {
    const queryParams = new URLSearchParams(params).toString()
    return api.get(`/get_data/?${queryParams}`)
  },
  
  // ポートフォリオデータを取得
  getPortfolioData: (params = {}) => {
    const queryParams = new URLSearchParams(params).toString()
    return api.get(`/api/portfolio/?${queryParams}`)
  },
  
  // 銘柄別履歴データを取得
  getStockHistory: (stockName, params = {}) => {
    const queryParams = new URLSearchParams(params).toString()
    return api.get(`/api/portfolio/stock/${stockName}/?${queryParams}`)
  },
  
  // 損益推移データを取得
  getProfitHistory: (params = {}) => {
    const queryParams = new URLSearchParams(params).toString()
    return api.get(`/api/portfolio/history/?${queryParams}`)
  },
  
  // 手動価格更新
  updatePrice: (data) => {
    return api.post('/api/manual_update/', data)
  },
  
  // データ品質検証
  validatePortfolioData: () => {
    return api.get('/api/portfolio/validate/')
  }
}

export default api