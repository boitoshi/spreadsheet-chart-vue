import { ExposureItem } from "@/types";
import { formatJpy, formatPercent } from "@/lib/formatters";

interface Props {
  items: ExposureItem[];
}

export function CurrencyExposureTable({ items }: Props) {
  if (items.length === 0) {
    return (
      <p className="text-gray-400 text-sm text-center py-4">データがありません</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2 pr-4 font-medium text-gray-500">通貨</th>
            <th className="text-right py-2 pr-4 font-medium text-gray-500">評価額</th>
            <th className="text-right py-2 pr-4 font-medium text-gray-500">取得額</th>
            <th className="text-right py-2 pr-4 font-medium text-gray-500">損益</th>
            <th className="text-right py-2 pr-4 font-medium text-gray-500">損益率</th>
            <th className="text-right py-2 font-medium text-gray-500">構成比</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.currency} className="border-b border-gray-100">
              <td className="py-2 pr-4 font-semibold text-gray-900">{item.currency}</td>
              <td className="py-2 pr-4 text-right text-gray-700">
                {formatJpy(item.value)}
              </td>
              <td className="py-2 pr-4 text-right text-gray-700">
                {formatJpy(item.cost)}
              </td>
              <td
                className={`py-2 pr-4 text-right font-medium ${
                  item.profit >= 0 ? "text-emerald-600" : "text-red-500"
                }`}
              >
                {item.profit >= 0 ? "+" : ""}
                {formatJpy(item.profit)}
              </td>
              <td
                className={`py-2 pr-4 text-right font-medium ${
                  item.profitRate >= 0 ? "text-emerald-600" : "text-red-500"
                }`}
              >
                {formatPercent(item.profitRate)}
              </td>
              <td className="py-2 text-right text-gray-600">
                {item.percentage.toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
