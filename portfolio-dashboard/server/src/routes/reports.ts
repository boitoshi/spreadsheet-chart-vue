import { readdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Hono } from "hono";
import { db } from "../db/index.js";
import { monthlyPnl, wpPosts } from "../db/schema.js";
import { buildReportData } from "../services/reportData.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

function getReportsDir(): string {
  // 現行 collector の blog_draft 出力先（portfolio-dashboard/collector/output）。
  // src/routes と dist/routes は server からの深さが同じなので、どちらの実行でも同じ場所を指す
  return (
    process.env.REPORTS_DIR ?? resolve(__dirname, "../../../collector/output")
  );
}

const app = new Hono();

// GET / → レポート一覧（DB（monthly_pnl）とファイル走査の和集合）
app.get("/", (c) => {
  // ── 1. monthly_pnl の日付（"YYYY-MM-末"）から年月を抽出 ──────────
  const pnlDatePattern = /^(\d{4})-(\d{2})-末$/;
  const pnlRows = db
    .selectDistinct({ date: monthlyPnl.date })
    .from(monthlyPnl)
    .all();
  const dbYearMonths = pnlRows
    .map((r) => pnlDatePattern.exec(r.date))
    .filter((m): m is RegExpExecArray => m !== null)
    .map((m) => ({ year: parseInt(m[1], 10), month: parseInt(m[2], 10) }));

  // ── 2. blog_draft_YYYY_MM.md ファイルの走査 ────────────────────
  const reportsDir = getReportsDir();
  let files: string[] = [];
  try {
    files = readdirSync(reportsDir);
  } catch {
    // ディレクトリが存在しない場合はファイル側は空扱い（DB 側だけで一覧を構成）
    files = [];
  }

  const filePattern = /^blog_draft_(\d{4})_(\d{2})\.md$/;
  const fileYearMonths = files
    .map((f) => filePattern.exec(f))
    .filter((m): m is RegExpExecArray => m !== null)
    .map((m) => ({ year: parseInt(m[1], 10), month: parseInt(m[2], 10) }));

  // ── 3. 和集合（重複排除） ──────────────────────────────────────
  const merged = new Map<string, { year: number; month: number }>();
  for (const ym of [...dbYearMonths, ...fileYearMonths]) {
    merged.set(`${ym.year}-${ym.month}`, ym);
  }

  // ── 4. wp_posts（month="YYYY-MM"）を引いて wpUrl を付与 ────────
  const wpRows = db.select().from(wpPosts).all();
  const wpMap = new Map(wpRows.map((r) => [r.month, r]));

  const reports = [...merged.values()]
    .sort((a, b) => {
      if (a.year !== b.year) return b.year - a.year;
      return b.month - a.month;
    })
    .map(({ year, month }) => {
      const monthKey = `${year}-${String(month).padStart(2, "0")}`;
      return {
        year,
        month,
        label: `${year}年${month}月`,
        wpUrl: wpMap.get(monthKey)?.url ?? null,
      };
    });

  return c.json({ reports });
});

// GET /:year/:month/data → 構造化レポートデータ（Markdown より先に定義）
app.get("/:year/:month/data", (c) => {
  const year = parseInt(c.req.param("year"), 10);
  const month = parseInt(c.req.param("month"), 10);

  if (Number.isNaN(year) || Number.isNaN(month)) {
    return c.json({ error: "Invalid year or month" }, 400);
  }

  // "YYYY-MM-末" 形式に変換（month は 2 桁ゼロ埋め）
  const mm = String(month).padStart(2, "0");
  const targetDate = `${year}-${mm}-末`;

  const data = buildReportData(db, targetDate);

  if (!data) {
    return c.json({ error: "Report data not found" }, 404);
  }

  return c.json(data);
});

// GET /:year/:month → 指定月のレポート内容（Markdown テキスト）
app.get("/:year/:month", (c) => {
  const year = parseInt(c.req.param("year"), 10);
  const month = parseInt(c.req.param("month"), 10);

  if (Number.isNaN(year) || Number.isNaN(month)) {
    return c.json({ error: "Invalid year or month" }, 400);
  }

  const mm = String(month).padStart(2, "0");
  const filename = `blog_draft_${year}_${mm}.md`;
  const reportsDir = getReportsDir();
  const filePath = resolve(reportsDir, filename);

  let content: string;
  try {
    content = readFileSync(filePath, "utf-8");
  } catch {
    return c.json({ error: "Report not found" }, 404);
  }

  return c.json({ year, month, content });
});

export { app as reportsRoute };
