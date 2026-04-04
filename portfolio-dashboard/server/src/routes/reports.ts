import { Hono } from "hono";
import { readdirSync, readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

function getReportsDir(): string {
  return (
    process.env.REPORTS_DIR ??
    resolve(__dirname, "../../../../data-collector/output")
  );
}

const app = new Hono();

// GET / → レポート一覧
app.get("/", (c) => {
  const reportsDir = getReportsDir();

  let files: string[];
  try {
    files = readdirSync(reportsDir);
  } catch {
    // ディレクトリが存在しない場合は空リストを返す
    return c.json({ reports: [] });
  }

  // blog_draft_YYYY_MM.md にマッチするファイルを抽出
  const pattern = /^blog_draft_(\d{4})_(\d{2})\.md$/;
  const reports = files
    .filter((f) => pattern.test(f))
    .map((filename) => {
      const m = pattern.exec(filename)!;
      const year = parseInt(m[1], 10);
      const month = parseInt(m[2], 10);
      return {
        year,
        month,
        label: `${year}年${month}月`,
        filename,
      };
    })
    .sort((a, b) => {
      if (a.year !== b.year) return b.year - a.year;
      return b.month - a.month;
    });

  return c.json({ reports });
});

// GET /:year/:month → 指定月のレポート内容
app.get("/:year/:month", (c) => {
  const year = parseInt(c.req.param("year"), 10);
  const month = parseInt(c.req.param("month"), 10);

  if (isNaN(year) || isNaN(month)) {
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
