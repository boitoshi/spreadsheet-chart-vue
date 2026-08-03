import { useQuery } from "@tanstack/react-query";
import type React from "react";
import { DividendTable } from "@/components/dividend/DividendTable";
import { DividendYearChart } from "@/components/dividend/DividendYearChart";
import { fetchApi } from "@/lib/api";
import type { DividendResponse } from "@/types";

/** サマリーカード共通スタイル（dashboard/SummaryCard の流儀に合わせる）*/
const cardStyle: React.CSSProperties = {
  background: "white",
  borderRadius: "14px",
  padding: "18px",
  boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
  flex: "1 1 200px",
};

/** 円表示（¥カンマ整数） */
function fmtJpy(v: number): string {
  return `¥${Math.round(v).toLocaleString("ja-JP")}`;
}

export default function Dividend() {
  const { data, isLoading } = useQuery({
    queryKey: ["dividend"],
    queryFn: () => fetchApi<DividendResponse>("/api/dividend"),
  });

  if (isLoading || !data) return <p className="text-gray-500">読み込み中...</p>;

  const currentYear = new Date().getFullYear();
  const thisYearTotal = data.data
    .filter((item) => Number(item.date.slice(0, 4)) === currentYear)
    .reduce((sum, item) => sum + item.totalJpy, 0);

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">配当・分配金</h1>
      <p className="text-xs text-gray-500 leading-relaxed mb-6">
        配当利回りを狙った投資はしていないため金額は小さめですが、受け取った分は記録として残しています。金額は税引前です。
      </p>

      {/* サマリーカード3枚 */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          flexWrap: "wrap",
          marginBottom: "16px",
        }}
      >
        <div style={cardStyle}>
          <p
            style={{
              fontSize: "10px",
              color: "#8c90a0",
              margin: "0 0 6px",
              fontWeight: 500,
            }}
          >
            累計受取額
          </p>
          <p
            style={{
              fontSize: "24px",
              fontWeight: 800,
              color: "#1e2130",
              margin: 0,
            }}
          >
            {fmtJpy(data.totalJpy)}
          </p>
        </div>
        <div style={cardStyle}>
          <p
            style={{
              fontSize: "10px",
              color: "#8c90a0",
              margin: "0 0 6px",
              fontWeight: 500,
            }}
          >
            今年の受取額
          </p>
          <p
            style={{
              fontSize: "24px",
              fontWeight: 800,
              color: "#1e2130",
              margin: 0,
            }}
          >
            {fmtJpy(thisYearTotal)}
          </p>
        </div>
        <div style={cardStyle}>
          <p
            style={{
              fontSize: "10px",
              color: "#8c90a0",
              margin: "0 0 6px",
              fontWeight: 500,
            }}
          >
            受取回数
          </p>
          <p
            style={{
              fontSize: "24px",
              fontWeight: 800,
              color: "#1e2130",
              margin: 0,
            }}
          >
            {data.data.length.toLocaleString("ja-JP")} 回
          </p>
        </div>
      </div>

      {/* 年別受取額チャート */}
      <div style={{ marginBottom: "16px" }}>
        <DividendYearChart data={data.data} />
      </div>

      {/* 明細テーブル */}
      <DividendTable data={data.data} />
    </div>
  );
}
