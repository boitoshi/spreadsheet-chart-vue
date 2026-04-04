import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "@/lib/api";
import type { DividendResponse } from "@/types";
import { DividendTable } from "@/components/dividend/DividendTable";

export default function Dividend() {
  const { data, isLoading } = useQuery({
    queryKey: ["dividend"],
    queryFn: () => fetchApi<DividendResponse>("/api/dividend"),
  });
  if (isLoading || !data) return <p className="text-gray-500">読み込み中...</p>;
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">配当・分配金</h1>
      <div className="mb-4 p-4 bg-white rounded-lg border border-gray-200">
        <p className="text-sm text-gray-600">受取配当合計</p>
        <p className="text-2xl font-bold text-gray-900">{data.totalJpy.toLocaleString()}円</p>
      </div>
      <DividendTable data={data.data} />
    </div>
  );
}
