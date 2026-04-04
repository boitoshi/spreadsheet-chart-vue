import { Hono } from "hono";
import { getLatestDate, getLatestPnlRecords } from "../db/queries.js";

const app = new Hono();

app.get("/", (c) => {
  const latestDate = getLatestDate();

  if (!latestDate) {
    return c.json({
      kpi: { totalValue: 0, totalProfit: 0, profitRate: 0, baseDate: "" },
      allocation: [],
      latestProfits: [],
    });
  }

  const records = getLatestPnlRecords(latestDate);

  const totalValue = records.reduce((sum, r) => sum + r.value, 0);
  const totalProfit = records.reduce((sum, r) => sum + r.profit, 0);
  const totalCost = records.reduce((sum, r) => sum + r.cost, 0);
  const profitRate = totalCost > 0 ? (totalProfit / totalCost) * 100 : 0;

  const allocation = records
    .map((r) => ({
      name: r.name,
      value: r.value,
      percentage: totalValue > 0 ? (r.value / totalValue) * 100 : 0,
    }))
    .sort((a, b) => b.value - a.value);

  const latestProfits = records
    .map((r) => ({
      name: r.name,
      profit: r.profit,
      profitRate: r.profitRate,
    }))
    .sort((a, b) => b.profit - a.profit);

  return c.json({
    kpi: {
      totalValue,
      totalProfit,
      profitRate,
      baseDate: latestDate,
    },
    allocation,
    latestProfits,
  });
});

export { app as dashboardRoute };
