import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { fetchApi } from "@/lib/api";
import type { ReportContentResponse } from "@/types";

export default function ReportDetail() {
  const { year, month } = useParams<{ year: string; month: string }>();
  const { data, isLoading, error } = useQuery({
    queryKey: ["report", year, month],
    queryFn: () => fetchApi<ReportContentResponse>(`/api/reports/${year}/${month}`),
    enabled: !!year && !!month,
  });

  if (isLoading) return <p className="text-gray-500">読み込み中...</p>;
  if (error) return <p className="text-red-500">レポートが見つかりません</p>;
  if (!data) return null;

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link to="/reports" className="text-sm text-gray-500 hover:text-gray-700">
          ← 一覧へ
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">
          {data.year}年{data.month}月 レポート
        </h1>
      </div>
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <pre className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed font-mono overflow-auto">
          {data.content}
        </pre>
      </div>
    </div>
  );
}
