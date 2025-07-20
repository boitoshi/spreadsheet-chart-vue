/**
 * API レスポンス型定義
 * 
 * バックエンドからのレスポンス形式に対応した型定義
 */

// 取引履歴の型
export interface Transaction {
  date: string      // YYYY/MM/DD形式
  quantity: number  // 株数
  price: number     // その時の価格
}

// 銘柄データの型
export interface Stock {
  name: string               // 銘柄名
  currentPrice: number       // 現在の株価
  transactions: Transaction[] // 取引履歴
  quantity: number           // 総保有数
  avgPrice: number          // 平均取得価格
  currentValue: number      // 現在評価額
  profit: number            // 損益
  totalCost: number         // 投資元本
}

// ポートフォリオサマリーの型
export interface PortfolioSummary {
  totalValue: number   // 総評価額
  totalProfit: number  // 総損益
  totalCost: number    // 総投資元本
}

// ポートフォリオAPIレスポンスの型
export interface PortfolioResponse {
  summary: PortfolioSummary
  stocks: Stock[]
}

// 期間別データの型
export interface PeriodData {
  labels: string[]  // ラベル（月など）
  data: number[]    // データ値
}

// 銘柄別推移データの型
export interface StockHistoryData {
  labels: string[]        // 日付ラベル
  data: number[]          // 損益データ
  acquisitions: string[]  // 取得タイミング
}

// 推移データAPIレスポンスの型
export interface HistoryResponse {
  periods: {
    sixMonths: PeriodData
    oneYear: PeriodData
    all: PeriodData
  }
  stocks: Record<string, StockHistoryData>
}

// スプレッドシートデータの型
export interface SpreadsheetData {
  label: string    // 日付
  stock: string    // 銘柄名
  quantity: number // 株数
  purchase: number // 購入価格
  value: number    // 評価額
}

// API エラーレスポンスの型
export interface ApiError {
  message: string
  code?: string
  details?: any
}

// API リクエストパラメータの型
export interface ApiParams {
  [key: string]: string | number | boolean | undefined
}

// 手動価格更新リクエストの型
export interface PriceUpdateRequest {
  stock: string     // 銘柄名
  price: number     // 新価格
  date: string      // 日付（YYYY-MM-DD形式）
}