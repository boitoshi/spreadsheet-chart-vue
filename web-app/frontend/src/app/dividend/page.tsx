import { fetchApi } from "@/lib/api";
import { DividendResponse } from "@/types";
import { DividendTable } from "@/components/dividend/DividendTable";

export const dynamic = "force-dynamic";

export default async function DividendPage() {
  const data = await fetchApi<DividendResponse>("/api/dividend");
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">配当・分配金</h1>
      <div className="mb-4 p-4 bg-white rounded-lg border border-gray-200">
        <p className="text-sm text-gray-600">受取配当合計</p>
        <p className="text-2xl font-bold text-gray-900">
          {data.totalJpy.toLocaleString()}円
        </p>
      </div>
      <DividendTable data={data.data} />
    </div>
  );
}
