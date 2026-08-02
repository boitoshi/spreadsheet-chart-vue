import type { DividendItem } from "@/types";

interface Props {
  data: DividendItem[];
}

/** 1株配当表示。外国株は通貨表記、日本株は totalJpy/shares の円表記（null 安全）*/
function formatPerShare(item: DividendItem): string {
  if (item.dividendForeign !== null) {
    if (item.currency === "USD") {
      return `$${item.dividendForeign.toFixed(2)}`;
    }
    // USD 以外の外貨は通貨記号なしの安全な表記
    return `${item.dividendForeign.toLocaleString("ja-JP", { maximumFractionDigits: 4 })} ${item.currency}`;
  }
  const perShare = item.shares > 0 ? item.totalJpy / item.shares : 0;
  return `¥${Math.round(perShare).toLocaleString("ja-JP")}`;
}

/** 外国株の受取額補足（例: "($0.02 @155.30)"）。null 安全、算出不能なら null */
function formatForeignNote(item: DividendItem): string | null {
  if (item.totalForeign === null || item.exchangeRate === null) return null;
  const amount =
    item.currency === "USD"
      ? `$${item.totalForeign.toFixed(2)}`
      : `${item.totalForeign.toLocaleString("ja-JP", { maximumFractionDigits: 4 })} ${item.currency}`;
  return `(${amount} @${item.exchangeRate.toFixed(2)})`;
}

export function DividendTable({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500">
        配当データがありません。collector の --add-dividend で記録すると表示されます。
      </div>
    );
  }
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-4 py-3 text-left text-gray-600">受取日</th>
            <th className="px-4 py-3 text-left text-gray-600">銘柄</th>
            <th className="px-4 py-3 text-right text-gray-600">1株配当</th>
            <th className="px-4 py-3 text-right text-gray-600">株数</th>
            <th className="px-4 py-3 text-right text-gray-600">受取額</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => {
            const foreignNote = formatForeignNote(item);
            return (
              <tr
                key={`${item.date}-${item.code}`}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="px-4 py-3 text-gray-700 whitespace-nowrap">{item.date}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span
                      className="inline-block w-2 h-2 rounded-sm shrink-0"
                      style={{ backgroundColor: item.color }}
                    />
                    <div>
                      <div className="font-medium text-gray-900">{item.name}</div>
                      <div className="text-gray-500 text-xs">{item.code}</div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 text-right text-gray-700 whitespace-nowrap">
                  {formatPerShare(item)}
                </td>
                <td className="px-4 py-3 text-right text-gray-700">
                  {item.shares.toLocaleString("ja-JP")}
                </td>
                <td className="px-4 py-3 text-right whitespace-nowrap">
                  <div className="font-medium text-gray-900">
                    ¥{Math.round(item.totalJpy).toLocaleString("ja-JP")}
                  </div>
                  {foreignNote !== null && (
                    <div className="text-gray-400 text-xs">{foreignNote}</div>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
