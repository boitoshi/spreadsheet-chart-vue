// KPI サマリー
export interface KpiSummary {
  totalValue: number; // 評価額合計（円）
  totalProfit: number; // 損益合計（円）
  profitRate: number; // 損益率（%）
  baseDate: string; // 基準日（YYYY-MM-DD）
}

// ダッシュボード: 構成比（DonutChart 用）
export interface AllocationItem {
  name: string; // 銘柄名
  value: number; // 評価額（円）
  percentage: number; // 構成比（%）
}

// ダッシュボード: 最新月損益（BarChart 用）
export interface LatestProfitItem {
  name: string; // 銘柄名
  profit: number; // 損益（円）
  profitRate: number; // 損益率（%）
}

// ダッシュボード レスポンス
export interface DashboardResponse {
  kpi: KpiSummary;
  allocation: AllocationItem[];
  latestProfits: LatestProfitItem[];
}

// ポートフォリオ保有銘柄
export interface PortfolioItem {
  code: string; // 銘柄コード
  name: string; // 銘柄名
  acquiredDate: string; // 取得日
  acquiredPriceJpy: number; // 取得単価（円）
  acquiredPriceForeign: number | null; // 取得単価（外貨）
  acquiredExchangeRate: number | null; // 取得時為替レート
  shares: number; // 保有株数
  totalCost: number; // 取得額合計
  currency: string; // 通貨コード（JPY/USD/HKD）
  isForeign: boolean; // 外国株フラグ
}

// ポートフォリオ レスポンス
export interface PortfolioResponse {
  items: PortfolioItem[];
}

// 月次損益データポイント
export interface MonthlyProfitPoint {
  date: string; // 日付
  code: string; // 銘柄コード
  name: string; // 銘柄名
  profit: number; // 損益（円）
  value: number; // 評価額（円）
  profitRate: number; // 損益率（%）
  currency: string; // 通貨コード（JPY/USD/HKD）
  stockProfit: number; // 株価損益（円）
  fxProfit: number; // 為替損益（円）
}

// 損益推移 レスポンス
export interface HistoryResponse {
  data: MonthlyProfitPoint[];
  symbols: string[]; // フィルター選択肢（銘柄コード）
}

// 為替レートデータポイント
export interface CurrencyRatePoint {
  date: string; // 取得日
  pair: string; // 通貨ペア（例: USD/JPY）
  rate: number; // レート
  changeRate: number | null; // 変動率（%）
  high: number | null; // 最高値
  low: number | null; // 最安値
}

// 為替レート レスポンス
export interface CurrencyResponse {
  data: CurrencyRatePoint[];
  latestRate: number; // 最新レート
}

// 配当・分配金データポイント
export interface DividendItem {
  date: string;        // 受取日
  code: string;        // 銘柄コード
  name: string;        // 銘柄名
  dividendForeign: number;  // 1株配当（外貨）
  shares: number;      // 保有株数
  totalForeign: number; // 配当合計（外貨）
  currency: string;    // 通貨コード（JPY/USD/HKD）
  exchangeRate: number; // 為替レート
  totalJpy: number;    // 配当合計（円）
}

// 配当・分配金 レスポンス
export interface DividendResponse {
  data: DividendItem[];
  totalJpy: number;    // 受取配当合計（円）
}
