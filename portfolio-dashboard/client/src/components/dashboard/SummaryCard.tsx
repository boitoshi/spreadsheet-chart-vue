/** サマリーカード — 総資産・損益・ドーナツチャート＋凡例 */
import type React from "react";
import { PieChart, Pie, Cell } from "recharts";
import type { DashboardStock } from "@/types";
import {
  formatSignedYen,
  formatSignedPercent,
  plColor,
} from "@/lib/formatters";

/** カード共通スタイル */
const cardStyle: React.CSSProperties = {
  background: "white",
  borderRadius: "14px",
  padding: "18px",
  boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
};

interface Props {
  stocks: DashboardStock[];
  totalValue: number;
  totalProfit: number;
  totalProfitRate: number;
}

/** 円表示（¥カンマ整数） */
function fmtJpy(v: number): string {
  return `¥${Math.round(v).toLocaleString("ja-JP")}`;
}

export function SummaryCard({
  stocks,
  totalValue,
  totalProfit,
  totalProfitRate,
}: Props): React.ReactElement {
  return (
    <div style={cardStyle}>
      {/* ラベル */}
      <p
        style={{ fontSize: "10px", color: "#8c90a0", margin: "0 0 6px", fontWeight: 500 }}
      >
        総資産評価額
      </p>

      {/* 合計値 */}
      <p
        style={{
          fontSize: "28px",
          fontWeight: 800,
          color: "#1e2130",
          margin: "0 0 12px",
          lineHeight: 1.2,
        }}
      >
        {fmtJpy(totalValue)}
      </p>

      {/* 評価損益・損益率 2ボックス */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
        <div
          style={{
            flex: 1,
            background: "#f6f7fa",
            borderRadius: "8px",
            padding: "8px 10px",
          }}
        >
          <p style={{ fontSize: "9px", color: "#8c90a0", margin: "0 0 2px", fontWeight: 500 }}>
            評価損益
          </p>
          <p
            className={plColor(totalProfit)}
            style={{ fontSize: "13px", fontWeight: 700, margin: 0 }}
          >
            {formatSignedYen(totalProfit)}
          </p>
        </div>
        <div
          style={{
            flex: 1,
            background: "#f6f7fa",
            borderRadius: "8px",
            padding: "8px 10px",
          }}
        >
          <p style={{ fontSize: "9px", color: "#8c90a0", margin: "0 0 2px", fontWeight: 500 }}>
            損益率
          </p>
          <p
            className={plColor(totalProfitRate)}
            style={{ fontSize: "13px", fontWeight: 700, margin: 0 }}
          >
            {formatSignedPercent(totalProfitRate)}
          </p>
        </div>
      </div>

      {/* ドーナツチャート＋凡例 */}
      <div style={{ display: "flex", gap: "14px", alignItems: "flex-start" }}>
        {/* ドーナツ（固定サイズ） */}
        <PieChart width={90} height={90}>
          <Pie
            data={stocks}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={29}
            outerRadius={45}
            paddingAngle={2}
            isAnimationActive={false}
          >
            {stocks.map((s, i) => (
              <Cell key={i} fill={s.color} />
            ))}
          </Pie>
        </PieChart>

        {/* 凡例 */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "5px" }}>
          {stocks.map((s) => {
            const pct =
              totalValue > 0
                ? ((s.value / totalValue) * 100).toFixed(1)
                : "0.0";
            return (
              <div
                key={s.code}
                style={{ display: "flex", alignItems: "center", gap: "6px" }}
              >
                {/* カラードット */}
                <div
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "2px",
                    backgroundColor: s.color,
                    flexShrink: 0,
                  }}
                />
                {/* 銘柄名 */}
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: 600,
                    color: "#1e2130",
                    flex: 1,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {s.name}
                </span>
                {/* 構成比 */}
                <span style={{ fontSize: "10px", color: "#8c90a0", flexShrink: 0 }}>
                  {pct}%
                </span>
                {/* 評価額 */}
                <span style={{ fontSize: "10px", color: "#8c90a0", flexShrink: 0 }}>
                  {fmtJpy(s.value)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
