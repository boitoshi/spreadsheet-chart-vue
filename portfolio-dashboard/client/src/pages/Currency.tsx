import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import type { CurrencyResponse } from "@/types";
import { CurrencyLineChart } from "@/components/currency/CurrencyLineChart";

export default function Currency() {
  const { data, isLoading } = useQuery({
    queryKey: ["currency"],
    queryFn: () => fetchApi<CurrencyResponse>("/api/currency"),
  });
  if (isLoading || !data) return <p className="text-gray-500">読み込み中...</p>;
  return (
    <div>
      <div className="flex items-baseline gap-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">為替レート</h1>
        <span className="text-gray-500">最新: {data.latestRate.toFixed(2)} 円/USD</span>
      </div>
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <CurrencyLineChart data={data.data} />
      </div>
    </div>
  );
}
