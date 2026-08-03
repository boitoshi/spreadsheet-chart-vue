import { serve } from "@hono/node-server";
import { serveStatic } from "@hono/node-server/serve-static";
import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";
import { benchmarkRoute } from "./routes/benchmark.js";
import { currencyRoute } from "./routes/currency.js";
import { dashboardRoute } from "./routes/dashboard.js";
import { dividendRoute } from "./routes/dividend.js";
import { exposureRoute } from "./routes/exposure.js";
import { historyRoute } from "./routes/history.js";
import { portfolioRoute } from "./routes/portfolio.js";
import { reportsRoute } from "./routes/reports.js";

const app = new Hono();

// ミドルウェア
app.use("*", logger());
app.use(
  "*",
  cors({
    origin: ["http://localhost:3000", "http://localhost:5173"],
  }),
);

// ヘルスチェック
app.get("/health", (c) => c.json({ status: "ok" }));

// API ルート
app.route("/api/dashboard", dashboardRoute);
app.route("/api/portfolio", portfolioRoute);
app.route("/api/history", historyRoute);
app.route("/api/currency", currencyRoute);
app.route("/api/dividend", dividendRoute);
app.route("/api/reports", reportsRoute);
app.route("/api/benchmark", benchmarkRoute);
app.route("/api/exposure", exposureRoute);

// SPA 静的ファイル配信（Vite ビルド成果物）
app.use("/*", serveStatic({ root: "./client/dist" }));
app.get("/*", serveStatic({ root: "./client/dist", path: "index.html" }));

// サーバー起動
const port = parseInt(process.env.PORT ?? "3000", 10);
console.log(`Server running on http://localhost:${port}`);

serve({ fetch: app.fetch, port });

export default app;
