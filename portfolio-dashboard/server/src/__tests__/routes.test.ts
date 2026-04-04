import { describe, it, expect, beforeAll } from "vitest";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

// DB_PATH を :memory: に設定してからモジュールをインポート
process.env.DB_PATH = ":memory:";

const __dirname = dirname(fileURLToPath(import.meta.url));

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let app: any;

beforeAll(async () => {
  // db/index.ts は process.env.DB_PATH を参照するので、インポート前に設定済み
  const { sqlite } = await import("../db/index.js");

  // マイグレーション SQL を読み込んで実行
  const migrationPath = resolve(
    __dirname,
    "../../drizzle/migrations/0000_wise_morgan_stark.sql",
  );
  const migrationSql = readFileSync(migrationPath, "utf-8");

  // --> statement-breakpoint で分割して各文を実行
  const statements = migrationSql
    .split("--> statement-breakpoint")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  for (const stmt of statements) {
    sqlite.exec(stmt);
  }

  // テストデータ INSERT
  sqlite.exec(`
    INSERT INTO holdings (code, name, acquired_date, acquired_price_jpy, acquired_price_foreign, acquired_exchange_rate, shares, currency, is_foreign)
    VALUES ('7974.T', '任天堂', '2023-06-28', 6433, NULL, NULL, 100, 'JPY', 0);
  `);
  sqlite.exec(`
    INSERT INTO holdings (code, name, acquired_date, acquired_price_jpy, acquired_price_foreign, acquired_exchange_rate, shares, currency, is_foreign)
    VALUES ('NVDA', 'エヌビディア', '2024-03-15', 16500, 110.0, 150.0, 10, 'USD', 1);
  `);

  sqlite.exec(`
    INSERT INTO monthly_pnl (date, code, name, acquired_price, current_price, shares, cost, value, profit, profit_rate, currency, acquired_price_foreign, current_price_foreign, acquired_exchange_rate, current_exchange_rate)
    VALUES ('2025-03-末', '7974.T', '任天堂', 6433, 10000, 100, 643300, 1000000, 356700, 55.45, 'JPY', NULL, NULL, NULL, NULL);
  `);
  sqlite.exec(`
    INSERT INTO monthly_pnl (date, code, name, acquired_price, current_price, shares, cost, value, profit, profit_rate, currency, acquired_price_foreign, current_price_foreign, acquired_exchange_rate, current_exchange_rate)
    VALUES ('2025-03-末', 'NVDA', 'エヌビディア', 16500, 18000, 10, 165000, 180000, 15000, 9.09, 'USD', 110.0, 120.0, 150.0, 150.0);
  `);

  sqlite.exec(`
    INSERT INTO exchange_rates (date, pair, rate, prev_rate, change_rate, high, low)
    VALUES ('2025-03-31', 'USD/JPY', 150.0, 149.0, 0.67, 151.0, 148.0);
  `);

  sqlite.exec(`
    INSERT INTO dividends (date, code, name, dividend_foreign, shares, total_foreign, currency, exchange_rate, total_jpy)
    VALUES ('2025-03-15', 'NVDA', 'エヌビディア', 0.01, 10, 0.1, 'USD', 150.0, 15);
  `);

  sqlite.exec(`
    INSERT INTO benchmark_data (date, portfolio, nikkei225, sp500)
    VALUES ('2025-01-末', 5.0, 3.0, 2.0);
  `);
  sqlite.exec(`
    INSERT INTO benchmark_data (date, portfolio, nikkei225, sp500)
    VALUES ('2025-02-末', 10.0, 5.0, 4.0);
  `);
  sqlite.exec(`
    INSERT INTO benchmark_data (date, portfolio, nikkei225, sp500)
    VALUES ('2025-03-末', 15.0, 8.0, 6.0);
  `);

  // app をインポート（DB 準備完了後）
  const mod = await import("../index.js");
  app = mod.default;
});

describe("API routes", () => {
  it("GET /health → { status: 'ok' }", async () => {
    const res = await app.request("/health");
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toEqual({ status: "ok" });
  });

  it("GET /api/dashboard → kpi.totalValue === 1180000、allocation と latestProfits は 2件", async () => {
    const res = await app.request("/api/dashboard");
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.kpi.totalValue).toBe(1180000);
    expect(body.allocation).toHaveLength(2);
    expect(body.latestProfits).toHaveLength(2);
  });

  it("GET /api/portfolio → items は 2件、items[0].totalCost === 643300", async () => {
    const res = await app.request("/api/portfolio");
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.items).toHaveLength(2);
    // code 順にソートされている場合でも totalCost で探す
    const nintendo = body.items.find(
      (item: { code: string }) => item.code === "7974.T",
    );
    expect(nintendo).toBeDefined();
    expect(nintendo.totalCost).toBe(643300);
  });

  it("GET /api/history → data は 2件、symbols は ['7974.T', 'NVDA']", async () => {
    const res = await app.request("/api/history");
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.data).toHaveLength(2);
    expect(body.symbols).toEqual(expect.arrayContaining(["7974.T", "NVDA"]));
    expect(body.symbols).toHaveLength(2);
  });

  it("GET /api/history?stock=7974.T → data は 1件", async () => {
    const res = await app.request("/api/history?stock=7974.T");
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.data).toHaveLength(1);
    expect(body.data[0].code).toBe("7974.T");
  });

  it("GET /api/currency → data は 1件、latestRate === 150.0", async () => {
    const res = await app.request("/api/currency");
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.data).toHaveLength(1);
    expect(body.latestRate).toBe(150.0);
  });

  it("GET /api/dividend → data は 1件、totalJpy === 15", async () => {
    const res = await app.request("/api/dividend");
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.data).toHaveLength(1);
    expect(body.totalJpy).toBe(15);
  });

  it("GET /api/benchmark → data は 3件", async () => {
    const res = await app.request("/api/benchmark");
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.data).toHaveLength(3);
  });

  it("GET /api/exposure → items は 2件（JPY, USD）、JPY の value === 1000000", async () => {
    const res = await app.request("/api/exposure");
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.items).toHaveLength(2);
    const jpyItem = body.items.find(
      (item: { currency: string }) => item.currency === "JPY",
    );
    expect(jpyItem).toBeDefined();
    expect(jpyItem.value).toBe(1000000);
  });

  it("GET /api/reports → reports は配列（空でも可）", async () => {
    const res = await app.request("/api/reports");
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(Array.isArray(body.reports)).toBe(true);
  });
});
