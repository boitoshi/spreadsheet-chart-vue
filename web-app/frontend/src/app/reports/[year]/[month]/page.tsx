import Link from "next/link";
import { fetchApi } from "@/lib/api";
import { ReportContentResponse } from "@/types";

export const dynamic = "force-dynamic";

interface Props {
  params: Promise<{ year: string; month: string }>;
}

export default async function ReportDetailPage({ params }: Props) {
  const { year, month } = await params;
  const data = await fetchApi<ReportContentResponse>(
    `/api/reports/${year}/${month}`
  );
  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link
          href="/reports"
          className="text-sm text-gray-500 hover:text-gray-700"
        >
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
