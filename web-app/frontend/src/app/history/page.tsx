import { fetchApi } from "@/lib/api";
import { HistoryResponse } from "@/types";
import { ProfitAreaChart } from "@/components/history/ProfitAreaChart";
import { StockFilter } from "@/components/history/StockFilter";
import { StockCompareChart } from "@/components/history/StockCompareChart";

export const dynamic = "force-dynamic";

interface Props {
  searchParams: Promise<{ stock?: string }>;
}

export default async function HistoryPage({ searchParams }: Props) {
  const { stock } = await searchParams;
  const historyPath = stock
    ? `/api/history?stock=${encodeURIComponent(stock)}`
    : "/api/history";
  const data = await fetchApi<HistoryResponse>(historyPath);
  const filteredData = data.data;
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">損益推移</h1>
      <StockFilter symbols={data.symbols} current={stock} />
      <div className="mt-4 bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-sm font-medium text-gray-500 mb-4">損益内訳（株価損益・為替損益）</h2>
        <ProfitAreaChart data={filteredData} />
      </div>
      <div className="mt-4 bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-sm font-medium text-gray-500 mb-4">銘柄別損益率比較</h2>
        <StockCompareChart data={filteredData} />
      </div>
    </div>
  );
}
