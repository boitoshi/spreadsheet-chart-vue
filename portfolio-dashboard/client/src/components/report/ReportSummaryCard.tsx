/** 月次レポート用サマリーカード — 総資産・損益・ドーナツ＋凡例・メタ情報 */
import type React from "react";
import { Cell, Pie, PieChart } from "recharts";
import {
  formatSignedPercent,
  formatSignedYen,
  plColor,
} from "@/lib/formatters";
import type { DashboardStock } from "@/types";

interface Props {
  stocks: DashboardStock[];
  totalValue: number;
  totalProfit: number;
  totalProfitRate: number;
  exchangeRate: number;
  reportDate: string;
}

/** 円表示（¥カンマ整数） */
function fmtJpy(v: number): string {
  return `¥${Math.round(v).toLocaleString("ja-JP")}`;
}

export function ReportSummaryCard({
  stocks,
  totalValue,
  totalProfit,
  totalProfitRate,
  exchangeRate,
  reportDate,
}: Props): React.ReactElement {
  return (
    <div
      style={{
        background: "white",
        borderRadius: "16px",
        padding: "20px",
        boxShadow: "0 1px 4px rgba(0,0,0,0.05)",
      }}
    >
      {/* ラベル */}
      <p
        style={{
          fontSize: "10px",
          color: "#8c90a0",
          margin: "0 0 4px",
          fontWeight: 500,
        }}
      >
        総資産評価額
      </p>

      {/* 合計値 */}
      <p
        style={{
          fontSize: "30px",
          fontWeight: 800,
          color: "#1e2130",
          margin: "0 0 12px",
          lineHeight: 1.2,
        }}
      >
        {fmtJpy(totalValue)}
      </p>

      {/* 評価損益・損益率 2ボックス */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
        <div
          style={{
            flex: 1,
            background: "#f6f7fa",
            borderRadius: "8px",
            padding: "8px 10px",
          }}
        >
          <p
            style={{
              fontSize: "9px",
              color: "#8c90a0",
              margin: "0 0 2px",
              fontWeight: 500,
            }}
          >
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
          <p
            style={{
              fontSize: "9px",
              color: "#8c90a0",
              margin: "0 0 2px",
              fontWeight: 500,
            }}
          >
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
      <div
        style={{
          display: "flex",
          gap: "14px",
          alignItems: "flex-start",
          marginBottom: "16px",
        }}
      >
        {/* ドーナツ（110px 固定） */}
        <PieChart width={110} height={110}>
          <Pie
            data={stocks}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={35}
            outerRadius={55}
            paddingAngle={2}
            isAnimationActive={false}
          >
            {stocks.map((s) => (
              <Cell key={s.code} fill={s.color} />
            ))}
          </Pie>
        </PieChart>

        {/* 凡例 */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: "6px",
          }}
        >
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
                    width: "10px",
                    height: "10px",
                    borderRadius: "3px",
                    backgroundColor: s.color,
                    flexShrink: 0,
                  }}
                />
                {/* 銘柄名 */}
                <span
                  style={{
                    fontSize: "13px",
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
                {/* 構成比＋評価額 */}
                <span
                  style={{ fontSize: "12px", color: "#8c90a0", flexShrink: 0 }}
                >
                  {pct}% ・ {fmtJpy(s.value)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* メタ情報行 */}
      <p style={{ fontSize: "11px", color: "#8c90a0", margin: 0 }}>
        {`USD/JPY ¥${exchangeRate.toFixed(2)} ・ ${reportDate}時点`}
      </p>
    </div>
  );
}
