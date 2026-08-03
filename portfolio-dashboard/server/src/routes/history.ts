import { eq } from "drizzle-orm";
import { Hono } from "hono";
import { db } from "../db/index.js";
import { calcProfitDecomposition } from "../db/queries.js";
import { monthlyPnl } from "../db/schema.js";

const app = new Hono();

app.get("/", (c) => {
  const stockParam = c.req.query("stock");

  // symbols は全銘柄の { code, name } sorted unique list（フィルタ前）
  // distinct (code, name) で取っているため、name が月によって揺れると
  // 同じ code が複数出うる。code をキーにした Map で一意化する（後勝ち）
  const symbolRows = db
    .selectDistinct({ code: monthlyPnl.code, name: monthlyPnl.name })
    .from(monthlyPnl)
    .all();
  const symbolMap = new Map<string, string>();
  for (const r of symbolRows) {
    symbolMap.set(r.code, r.name);
  }
  const symbols = Array.from(symbolMap, ([code, name]) => ({
    code,
    name,
  })).sort((a, b) => (a.code < b.code ? -1 : a.code > b.code ? 1 : 0));

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
