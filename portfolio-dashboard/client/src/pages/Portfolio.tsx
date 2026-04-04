import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import type { PortfolioResponse } from "@/types";
import { HoldingsTable } from "@/components/portfolio/HoldingsTable";

export default function Portfolio() {
  const { data, isLoading } = useQuery({
    queryKey: ["portfolio"],
    queryFn: () => fetchApi<PortfolioResponse>("/api/portfolio"),
  });
  if (isLoading || !data) return <p className="text-gray-500">読み込み中...</p>;
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">ポートフォリオ</h1>
      <HoldingsTable items={data.items} />
    </div>
  );
}
