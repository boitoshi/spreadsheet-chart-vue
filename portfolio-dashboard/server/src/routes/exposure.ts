import { Hono } from "hono";
import { getLatestDate, getLatestPnlRecords } from "../db/queries.js";

// 対象通貨（HKD 除外）
const TARGET_CURRENCIES = ["JPY", "USD"];

const app = new Hono();

app.get("/", (c) => {
  const latestDate = getLatestDate();

  if (!latestDate) {
    return c.json({ items: [] });
  }

  const records = getLatestPnlRecords(latestDate);

  // JPY / USD のみに絞り込んで通貨別に集計
  const currencyMap = new Map<string, { value: number; cost: number }>();

  for (const r of records) {
    if (!TARGET_CURRENCIES.includes(r.currency)) continue;
    const acc = currencyMap.get(r.currency) ?? { value: 0, cost: 0 };
    acc.value += r.value;
    acc.cost += r.cost;
    currencyMap.set(r.currency, acc);
  }

  const totalValue = [...currencyMap.values()].reduce(
    (sum, v) => sum + v.value,
    0,
  );

  const items = [...currencyMap.entries()]
    .sort(([a], [b]) => a.localeCompare(b)) // アルファベット順
    .map(([currency, { value, cost }]) => {
      const profit = value - cost;
      const profitRate = cost > 0 ? (profit / cost) * 100 : 0;
      const percentage = totalValue > 0 ? (value / totalValue) * 100 : 0;

      return {
        currency,
        value: Math.round(value),
        cost: Math.round(cost),
        profit: Math.round(profit),
        profitRate: Math.round(profitRate * 100) / 100,
        percentage: Math.round(percentage * 100) / 100,
      };
    });

  return c.json({ items });
});

export { app as exposureRoute };
