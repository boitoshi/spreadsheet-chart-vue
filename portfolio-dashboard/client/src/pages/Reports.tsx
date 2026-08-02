import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchApi } from "@/lib/api";
import type { ReportListResponse } from "@/types";

export default function Reports() {
  const { data, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: () => fetchApi<ReportListResponse>("/api/reports"),
  });
  if (isLoading || !data) return <p className="text-gray-500">読み込み中...</p>;
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">月次レポート</h1>
      {data.reports.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500">
          レポートがありません。月次バッチ（collect_and_publish）実行後に表示されます。
        </div>
      ) : (
        <ul className="space-y-2">
          {data.reports.map((r) => (
            <li key={`${r.year}-${r.month}`}>
              <Link
                to={`/reports/${r.year}/${r.month}`}
                className="flex items-center gap-3 bg-white rounded-lg border border-gray-200 px-5 py-4 hover:border-blue-400 hover:bg-blue-50 transition-colors"
              >
                <span className="text-blue-600 font-medium flex-1">{r.label}</span>
                {r.wpUrl !== null && (
                  <a
                    href={r.wpUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="text-gray-400 text-sm hover:text-blue-500 hover:underline shrink-0"
                  >
                    ブログ記事 ↗
                  </a>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
