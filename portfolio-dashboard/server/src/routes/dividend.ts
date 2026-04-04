import { Hono } from "hono";
import { db } from "../db/index.js";
import { dividends } from "../db/schema.js";

const app = new Hono();

app.get("/", (c) => {
  const rows = db.select().from(dividends).all();

  const data = rows.map((r) => ({
    date: r.date,
    code: r.code,
    name: r.name,
    dividendForeign: r.dividendForeign ?? null,
    shares: r.shares,
    totalForeign: r.totalForeign ?? null,
    currency: r.currency,
    exchangeRate: r.exchangeRate ?? null,
    totalJpy: r.totalJpy,
  }));

  const totalJpy = rows.reduce((sum, r) => sum + r.totalJpy, 0);

  return c.json({ data, totalJpy });
});

export { app as dividendRoute };
