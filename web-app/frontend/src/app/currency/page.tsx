import { fetchApi } from "@/lib/api";
import { CurrencyResponse } from "@/types";
import { CurrencyLineChart } from "@/components/currency/CurrencyLineChart";

export const dynamic = "force-dynamic";

export default async function CurrencyPage() {
  const data = await fetchApi<CurrencyResponse>("/api/currency");
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
