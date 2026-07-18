import { Hono } from "hono";
import { asc } from "drizzle-orm";
import { db } from "../db/index.js";
import { holdings, purchaseHistory } from "../db/schema.js";

const app = new Hono();

app.get("/", (c) => {
  const rows = db.select().from(holdings).all();

  // purchase_history を 1 クエリで全件取得し、code ごとに Map へグルーピング（N+1 禁止）
  const purchaseRows = db
    .select()
    .from(purchaseHistory)
    .orderBy(asc(purchaseHistory.seq))
    .all();

  const purchasesByCode = new Map<string, typeof purchaseRows>();
  for (const p of purchaseRows) {
    const list = purchasesByCode.get(p.code);
    if (list) {
      list.push(p);
    } else {
      purchasesByCode.set(p.code, [p]);
    }
  }

  const items = rows.map((r) => {
    let acquiredPriceJpy = r.acquiredPriceJpy;
    // acquiredPriceJpy が 0 で外貨フィールドがある場合はフォールバック計算
    if (
      acquiredPriceJpy === 0 &&
      r.acquiredPriceForeign != null &&
      r.acquiredExchangeRate != null
    ) {
      acquiredPriceJpy = r.acquiredPriceForeign * r.acquiredExchangeRate;
    }

    const totalCost = acquiredPriceJpy * r.shares;

    const purchases = (purchasesByCode.get(r.code) ?? []).map((p) => ({
      seq: p.seq,
      shares: p.shares,
      price: p.price,
      priceForeign: p.priceForeign ?? null,
      exchangeRate: p.exchangeRate ?? null,
      purchasedAt: p.purchasedAt,
    }));

    return {
      code: r.code,
      name: r.name,
      acquiredDate: r.acquiredDate ?? null,
      acquiredPriceJpy,
      acquiredPriceForeign: r.acquiredPriceForeign ?? null,
      acquiredExchangeRate: r.acquiredExchangeRate ?? null,
      shares: r.shares,
      totalCost,
      currency: r.currency,
      isForeign: r.isForeign,
      purchases,
    };
  });

  return c.json({ items });
});

export { app as portfolioRoute };
