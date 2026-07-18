import { Fragment, useState } from "react";
import { PortfolioItem } from "@/types";
import { formatJpy, formatNative } from "@/lib/formatters";

interface Props {
  items: PortfolioItem[];
}

const COLUMN_COUNT = 6;

export function HoldingsTable({ items }: Props) {
  // 単一展開方式: 展開中の銘柄コードのみ保持
  const [expandedCode, setExpandedCode] = useState<string | null>(null);

  const toggleRow = (code: string) => {
    setExpandedCode((prev) => (prev === code ? null : code));
  };

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
          {items.map((item, i) => {
            const isExpanded = expandedCode === item.code;
            return (
              <Fragment key={item.code || i}>
                <tr
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => toggleRow(item.code)}
                >
                  <td className="px-4 py-3 font-mono text-gray-900">
                    <span
                      className="inline-block mr-1 text-gray-400 transition-transform"
                      style={{ transform: isExpanded ? "rotate(90deg)" : "none" }}
                    >
                      ▸
                    </span>
                    {item.code}
                  </td>
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
                {isExpanded && (
                  <tr className="bg-gray-50">
                    <td colSpan={COLUMN_COUNT} className="px-4 py-3">
                      <PurchaseHistoryTable purchases={item.purchases} />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/** 買付履歴ミニテーブル */
function PurchaseHistoryTable({ purchases }: { purchases: PortfolioItem["purchases"] }) {
  if (purchases.length === 0) {
    return <p className="text-xs text-gray-500">買付履歴がありません</p>;
  }

  return (
    <table className="min-w-full text-xs">
      <thead>
        <tr className="text-gray-500">
          <th className="px-2 py-1 text-left font-medium">回</th>
          <th className="px-2 py-1 text-left font-medium">取得日</th>
          <th className="px-2 py-1 text-right font-medium">株数</th>
          <th className="px-2 py-1 text-right font-medium">取得単価</th>
          <th className="px-2 py-1 text-right font-medium">円換算額</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {purchases.map((p) => {
          const isForeign = p.priceForeign != null;
          const jpyAmount = isForeign
            ? p.exchangeRate != null
              ? p.priceForeign! * p.exchangeRate * p.shares
              : null
            : p.price * p.shares;

          return (
            <tr key={p.seq}>
              <td className="px-2 py-1 text-gray-700">{p.seq}</td>
              <td className="px-2 py-1 text-gray-700">{p.purchasedAt}</td>
              <td className="px-2 py-1 text-right text-gray-700">
                {p.shares.toLocaleString()}
              </td>
              <td className="px-2 py-1 text-right text-gray-900">
                {isForeign ? (
                  <>
                    {formatNative(p.priceForeign as number, "USD")}
                    {p.exchangeRate != null && (
                      <span className="block text-[10px] text-gray-400">
                        @為替 ¥{p.exchangeRate.toFixed(2)}
                      </span>
                    )}
                  </>
                ) : (
                  formatJpy(p.price)
                )}
              </td>
              <td className="px-2 py-1 text-right text-gray-900">
                {jpyAmount != null ? formatJpy(jpyAmount) : "—"}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
