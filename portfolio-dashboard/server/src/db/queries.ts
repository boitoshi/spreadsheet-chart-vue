import { db } from "./index.js";
import { monthlyPnl } from "./schema.js";
import { desc, eq } from "drizzle-orm";

/** monthlyPnl の最新日付を取得 */
export function getLatestDate(): string | null {
  const row = db
    .select({ date: monthlyPnl.date })
    .from(monthlyPnl)
    .orderBy(desc(monthlyPnl.date))
    .limit(1)
    .get();
  return row?.date ?? null;
}

/** 指定日付の monthlyPnl レコードを全取得 */
export function getLatestPnlRecords(date: string) {
  return db
    .select()
    .from(monthlyPnl)
    .where(eq(monthlyPnl.date, date))
    .all();
}

/**
 * 損益分離計算。(stockProfit, fxProfit) を返す。
 *
 * 元の Python 実装 (web-app/backend/app/sheets/performance.py:5-27) を忠実に移植:
 * - JPY、または外貨フィールドが1つでも null → (profit, 0)
 * - 外貨建て:
 *   stockProfit = (currentPriceForeign - acquiredPriceForeign) * acquiredExchangeRate * shares
 *   fxProfit = (currentExchangeRate - acquiredExchangeRate) * currentPriceForeign * shares
 */
export function calcProfitDecomposition(
  profit: number,
  shares: number,
  currency: string,
  acquiredPriceForeign: number | null,
  currentPriceForeign: number | null,
  acquiredExchangeRate: number | null,
  currentExchangeRate: number | null,
): { stockProfit: number; fxProfit: number } {
  if (
    currency === "JPY" ||
    acquiredPriceForeign == null ||
    currentPriceForeign == null ||
    acquiredExchangeRate == null ||
    currentExchangeRate == null
  ) {
    return { stockProfit: profit, fxProfit: 0 };
  }
  const priceDiff = currentPriceForeign - acquiredPriceForeign;
  const stockProfit = priceDiff * acquiredExchangeRate * shares;
  const rateDiff = currentExchangeRate - acquiredExchangeRate;
  const fxProfit = rateDiff * currentPriceForeign * shares;
  return { stockProfit, fxProfit };
}
