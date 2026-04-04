import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import type { DashboardResponse, ExposureResponse, HistoryResponse } from "@/types";
import { KpiCards } from "@/components/dashboard/KpiCards";
import { AllocationChart } from "@/components/dashboard/AllocationChart";
import { LatestBarChart } from "@/components/dashboard/LatestBarChart";
import { AllocationTrendChart } from "@/components/dashboard/AllocationTrendChart";
import { CurrencyExposureTable } from "@/components/dashboard/CurrencyExposureTable";

export default function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => fetchApi<DashboardResponse>("/api/dashboard"),
  });
  const { data: history } = useQuery({
    queryKey: ["history"],
    queryFn: () => fetchApi<HistoryResponse>("/api/history"),
  });
  const { data: exposure } = useQuery({
    queryKey: ["exposure"],
    queryFn: () => fetchApi<ExposureResponse>("/api/exposure"),
  });

  if (isLoading || !data) return <p className="text-gray-500">読み込み中...</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">ダッシュボード</h1>
        <p className="text-sm text-gray-500">基準日: {data.kpi.baseDate}</p>
      </div>
      <KpiCards kpi={data.kpi} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">構成比</h2>
          <AllocationChart data={data.allocation} />
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">最新月 損益</h2>
          <LatestBarChart data={data.latestProfits} />
        </div>
      </div>
      {history && (
        <div className="mt-6 bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">評価額推移（銘柄別）</h2>
          <AllocationTrendChart data={history.data} />
        </div>
      )}
      {exposure && (
        <div className="mt-6 bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">通貨別エクスポージャー（最新月）</h2>
          <CurrencyExposureTable items={exposure.items} />
        </div>
      )}
    </div>
  );
}
