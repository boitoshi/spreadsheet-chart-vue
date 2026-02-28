import { fetchApi } from "@/lib/api";
import { PortfolioResponse } from "@/types";
import { HoldingsTable } from "@/components/portfolio/HoldingsTable";

export const dynamic = "force-dynamic";

export default async function PortfolioPage() {
  const data = await fetchApi<PortfolioResponse>("/api/portfolio");
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">ポートフォリオ</h1>
      <HoldingsTable items={data.items} />
    </div>
  );
}
