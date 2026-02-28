import { fetchApi } from "@/lib/api";
import { HistoryResponse } from "@/types";
import { ProfitAreaChart } from "@/components/history/ProfitAreaChart";
import { StockFilter } from "@/components/history/StockFilter";

export const dynamic = "force-dynamic";

interface Props {
  searchParams: Promise<{ stock?: string }>;
}

export default async function HistoryPage({ searchParams }: Props) {
  const { stock } = await searchParams;
  const url = stock ? `/api/history?stock=${stock}` : "/api/history";
  const data = await fetchApi<HistoryResponse>(url);
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">損益推移</h1>
      <StockFilter symbols={data.symbols} current={stock} />
      <div className="mt-4 bg-white rounded-lg border border-gray-200 p-6">
        <ProfitAreaChart data={data.data} />
      </div>
    </div>
  );
}
