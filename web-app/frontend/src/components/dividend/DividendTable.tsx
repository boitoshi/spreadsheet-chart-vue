"use client";
import { DividendItem } from "@/types";

interface Props {
  data: DividendItem[];
}

export function DividendTable({ data }: Props) {
  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500">
        データがありません。スプレッドシートに「配当・分配金」シートを作成してください。
      </div>
    );
  }
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-4 py-3 text-left text-gray-600">受取日</th>
            <th className="px-4 py-3 text-left text-gray-600">銘柄</th>
            <th className="px-4 py-3 text-right text-gray-600">配当（外貨）</th>
            <th className="px-4 py-3 text-right text-gray-600">為替レート</th>
            <th className="px-4 py-3 text-right text-gray-600">配当合計（円）</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={`${item.date}-${item.code}`} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="px-4 py-3 text-gray-700">{item.date}</td>
              <td className="px-4 py-3">
                <div className="font-medium text-gray-900">{item.name}</div>
                <div className="text-gray-500 text-xs">{item.code}</div>
              </td>
              <td className="px-4 py-3 text-right text-gray-700">
                {item.totalForeign.toLocaleString()} {item.currency}
              </td>
              <td className="px-4 py-3 text-right text-gray-700">
                {item.exchangeRate.toLocaleString()}
              </td>
              <td className="px-4 py-3 text-right font-medium text-gray-900">
                {item.totalJpy.toLocaleString()}円
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
