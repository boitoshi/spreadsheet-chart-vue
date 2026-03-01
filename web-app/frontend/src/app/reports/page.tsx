import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { ReportListResponse } from "@/types";

export const dynamic = "force-dynamic";

export default async function ReportsPage() {
  const data = await fetchApi<ReportListResponse>("/api/reports");
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">月次レポート</h1>
      {data.reports.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500">
          レポートがありません。data-collector を実行してください。
        </div>
      ) : (
        <ul className="space-y-2">
          {data.reports.map((r) => (
            <li key={`${r.year}-${r.month}`}>
              <Link
                href={`/reports/${r.year}/${r.month}`}
                className="flex items-center gap-3 bg-white rounded-lg border border-gray-200 px-5 py-4 hover:border-blue-400 hover:bg-blue-50 transition-colors"
              >
                <span className="text-blue-600 font-medium">{r.label}</span>
                <span className="text-gray-400 text-sm">{r.filename}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
