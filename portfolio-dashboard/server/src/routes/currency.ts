import { Hono } from "hono";
import { db } from "../db/index.js";
import { exchangeRates } from "../db/schema.js";
import { gte, desc } from "drizzle-orm";

const app = new Hono();

app.get("/", (c) => {
  const startParam = c.req.query("start"); // YYYY-MM 形式

  let rows;
  if (startParam) {
    // "YYYY-MM" → "YYYY-MM-01" で文字列比較フィルタ
    const startDate = `${startParam}-01`;
    rows = db
      .select()
      .from(exchangeRates)
      .where(gte(exchangeRates.date, startDate))
      .all();
  } else {
    rows = db.select().from(exchangeRates).all();
  }

  const data = rows.map((r) => ({
    date: r.date,
    pair: r.pair,
    rate: r.rate,
    changeRate: r.changeRate ?? null,
    high: r.high ?? null,
    low: r.low ?? null,
  }));

  // latestRate: 最新レコードの rate（データなしなら 0）
  const latestRow = db
    .select({ rate: exchangeRates.rate })
    .from(exchangeRates)
    .orderBy(desc(exchangeRates.date))
    .limit(1)
    .get();
  const latestRate = latestRow?.rate ?? 0;

  return c.json({ data, latestRate });
});

export { app as currencyRoute };
