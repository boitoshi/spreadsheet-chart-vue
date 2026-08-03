import { desc, eq } from "drizzle-orm";
import { Hono } from "hono";
import { db } from "../db/index.js";
import { getLatestDate, getLatestPnlRecords } from "../db/queries.js";
import { exchangeRates } from "../db/schema.js";
import { buildReportData } from "../services/reportData.js";

const app = new Hono();

app.get("/", (c) => {
  const latestDate = getLatestDate();

  if (!latestDate) {
    return c.json({
      kpi: { totalValue: 0, totalProfit: 0, profitRate: 0, baseDate: "" },
      allocation: [],
      latestProfits: [],
      stocks: [],
      totalHistory: { months: [], assetValues: [], plValues: [] },
      usdJpy: null,
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

  // ── 拡張データ：stocks / totalHistory / usdJpy ───────────────
  // buildReportData は latestDate をベースに詳細データを構築する
  const reportData = buildReportData(db, latestDate);

  // 最新 USD/JPY レート
  const latestUsdJpy = db
    .select({ rate: exchangeRates.rate })
    .from(exchangeRates)
    .where(eq(exchangeRates.pair, "USD/JPY"))
    .orderBy(desc(exchangeRates.date))
    .limit(1)
    .get();

  return c.json({
    kpi: {
      totalValue,
      totalProfit,
      profitRate,
      baseDate: latestDate,
    },
    allocation,
    latestProfits,
    // 以下は Phase A で追加した拡張フィールド
    stocks: reportData?.stocks ?? [],
    totalHistory: reportData?.totalHistory ?? {
      months: [],
      assetValues: [],
      plValues: [],
    },
    usdJpy: latestUsdJpy?.rate ?? null,
  });
});

export { app as dashboardRoute };
