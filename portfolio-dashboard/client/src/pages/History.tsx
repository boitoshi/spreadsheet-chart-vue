import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { fetchApi } from "@/lib/api";
import type { BenchmarkResponse, HistoryResponse } from "@/types";
import { BenchmarkChart } from "@/components/history/BenchmarkChart";
import { ProfitAreaChart } from "@/components/history/ProfitAreaChart";
import { StockFilter } from "@/components/history/StockFilter";
import { StockCompareChart } from "@/components/history/StockCompareChart";

export default function History() {
  const [searchParams] = useSearchParams();
  const stock = searchParams.get("stock") ?? undefined;
  const historyPath = stock
    ? `/api/history?stock=${encodeURIComponent(stock)}`
    : "/api/history";

  const { data, isLoading } = useQuery({
    queryKey: ["history", stock],
    queryFn: () => fetchApi<HistoryResponse>(historyPath),
  });
  const { data: benchmark } = useQuery({
    queryKey: ["benchmark"],
    queryFn: () => fetchApi<BenchmarkResponse>("/api/benchmark"),
  });

  if (isLoading || !data) return <p className="text-gray-500">読み込み中...</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">損益推移</h1>
      <StockFilter symbols={data.symbols} current={stock} />
      <div className="mt-4 bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-sm font-medium text-gray-500 mb-4">損益内訳（株価損益・為替損益）</h2>
        <ProfitAreaChart data={data.data} />
      </div>
      <div className="mt-4 bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-sm font-medium text-gray-500 mb-4">銘柄別損益率比較</h2>
        <StockCompareChart data={data.data} />
      </div>
      {benchmark && (
        <div className="mt-4 bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-medium text-gray-500 mb-4">ベンチマーク比較（累積リターン）</h2>
          <BenchmarkChart data={benchmark.data} />
        </div>
      )}
    </div>
  );
}
