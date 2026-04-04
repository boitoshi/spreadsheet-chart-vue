import { PortfolioItem } from "@/types";
import { formatJpy } from "@/lib/formatters";

interface Props {
  items: PortfolioItem[];
}

export function HoldingsTable({ items }: Props) {
  return (
    <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            {["銘柄コード", "銘柄名", "通貨", "取得日", "取得単価（円）", "保有株数"].map((h) => (
              <th key={h} className="px-4 py-3 text-left font-medium text-gray-600">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {items.map((item, i) => (
            <tr key={i} className="hover:bg-gray-50">
              <td className="px-4 py-3 font-mono text-gray-900">{item.code}</td>
              <td className="px-4 py-3 text-gray-900">{item.name}</td>
              <td className="px-4 py-3 text-gray-600">{item.currency}</td>
              <td className="px-4 py-3 text-gray-600">{item.acquiredDate}</td>
              <td className="px-4 py-3 text-right text-gray-900">
                {formatJpy(item.acquiredPriceJpy)}
              </td>
              <td className="px-4 py-3 text-right text-gray-900">
                {item.shares.toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
