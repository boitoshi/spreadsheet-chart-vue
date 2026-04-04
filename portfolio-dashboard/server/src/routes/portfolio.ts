import { Hono } from "hono";
import { db } from "../db/index.js";
import { holdings } from "../db/schema.js";

const app = new Hono();

app.get("/", (c) => {
  const rows = db.select().from(holdings).all();

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
    };
  });

  return c.json({ items });
});

export { app as portfolioRoute };
