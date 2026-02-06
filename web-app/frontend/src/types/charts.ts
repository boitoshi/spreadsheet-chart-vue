/**
 * チャート関連の型定義
 */

// 期間データの型
export interface PeriodData {
  labels: string[]
  data: number[]
}

// 期間別データの型
export interface ProfitDataType {
  '6months': PeriodData
  '1year': PeriodData
  'all': PeriodData
}

// 銘柄別推移データの型
export interface StockProfitDataEntry {
  labels: string[]
  data: number[]
  acquisitions: string[]
}

// 銘柄別データの型
export type StockProfitDataType = Record<string, StockProfitDataEntry>

// チャート設定の型
export interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    borderColor: string
    backgroundColor: string
    fill?: boolean
    tension?: number
    pointBackgroundColor?: string[]
    pointRadius?: number[]
    pointHoverRadius?: number[]
  }[]
}