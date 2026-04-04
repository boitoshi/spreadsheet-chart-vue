import { Hono } from "hono";
import { db } from "../db/index.js";
import { benchmarkData } from "../db/schema.js";
import { asc } from "drizzle-orm";

const app = new Hono();

app.get("/", (c) => {
  const rows = db
    .select()
    .from(benchmarkData)
    .orderBy(asc(benchmarkData.date))
    .all();

  const data = rows.map((r) => ({
    date: r.date,
    portfolio: r.portfolio,
    nikkei225: r.nikkei225 ?? null,
    sp500: r.sp500 ?? null,
  }));

  return c.json({ data });
});

export { app as benchmarkRoute };
