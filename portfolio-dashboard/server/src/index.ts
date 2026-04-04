import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { logger } from "hono/logger";
import { cors } from "hono/cors";
import { dashboardRoute } from "./routes/dashboard.js";
import { portfolioRoute } from "./routes/portfolio.js";
import { historyRoute } from "./routes/history.js";
import { currencyRoute } from "./routes/currency.js";
import { dividendRoute } from "./routes/dividend.js";
import { reportsRoute } from "./routes/reports.js";
import { benchmarkRoute } from "./routes/benchmark.js";
import { exposureRoute } from "./routes/exposure.js";

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

// サーバー起動
const port = parseInt(process.env.PORT ?? "3000", 10);
console.log(`Server running on http://localhost:${port}`);

serve({ fetch: app.fetch, port });

export default app;
