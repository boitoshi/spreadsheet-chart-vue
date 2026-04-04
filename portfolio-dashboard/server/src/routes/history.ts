import { Hono } from "hono";
import { db } from "../db/index.js";
import { monthlyPnl } from "../db/schema.js";
import { eq } from "drizzle-orm";
import { calcProfitDecomposition } from "../db/queries.js";

const app = new Hono();

app.get("/", (c) => {
  const stockParam = c.req.query("stock");

  // symbols は全銘柄コードの sorted unique list（フィルタ前）
  const symbolRows = db
    .selectDistinct({ code: monthlyPnl.code })
    .from(monthlyPnl)
    .all();
  const symbols = symbolRows.map((r) => r.code).sort();

  // データ取得（stock パラメータで絞り込み可）
  const rows = stockParam
    ? db.select().from(monthlyPnl).where(eq(monthlyPnl.code, stockParam)).all()
    : db.select().from(monthlyPnl).all();

  const data = rows.map((r) => {
    const { stockProfit, fxProfit } = calcProfitDecomposition(
      r.profit,
      r.shares,
      r.currency,
      r.acquiredPriceForeign ?? null,
      r.currentPriceForeign ?? null,
      r.acquiredExchangeRate ?? null,
      r.currentExchangeRate ?? null,
    );

    return {
      date: r.date,
      code: r.code,
      name: r.name,
      profit: r.profit,
      value: r.value,
      profitRate: r.profitRate,
      currency: r.currency,
      stockProfit,
      fxProfit,
    };
  });

  return c.json({ data, symbols });
});

export { app as historyRoute };
