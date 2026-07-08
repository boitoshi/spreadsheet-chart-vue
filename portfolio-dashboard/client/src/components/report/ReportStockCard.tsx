/** 月次レポート用個別銘柄カード（縦1カラム・ブログ向け） */
import { useState } from "react";
import type React from "react";
import type { DashboardStock } from "@/types";
import {
  formatNative,
  formatSignedYen,
  formatSignedPercent,
  plColor,
} from "@/lib/formatters";
import { StockPriceChart } from "@/components/dashboard/StockPriceChart";
import { PeriodToggle } from "@/components/dashboard/PeriodToggle";
import type { Period } from "@/components/dashboard/PeriodToggle";

interface Props {
  stock: DashboardStock;
}

/** "YYYY/M" → "M月" */
function toLabel(ym: string): string {
  const m = ym.split("/")[1];
  return `${m}月`;
}

/** 期間に応じてスライス件数を返す */
function sliceCount(period: Period, total: number): number {
  if (period === "3M") return Math.min(3, total);
  if (period === "6M") return Math.min(6, total);
  if (period === "1Y") return Math.min(12, total);
  return total; // ALL（設定来）
}

/** 期間ラベル（日本語表記） */
const REPORT_PERIOD_LABELS: Record<Period, string> = {
  "3M": "3ヶ月",
  "6M": "6ヶ月",
  "1Y": "1年",
  ALL: "設定来",
};

export function ReportStockCard({ stock }: Props): React.ReactElement {
  const [period, setPeriod] = useState<Period>("6M");

  // 期間に応じてスライス
  const total = stock.priceHistory.length;
  const count = sliceCount(period, total);
  const prices = stock.priceHistory.slice(-count);
  const avgCosts = stock.acquiredAvgHistory.slice(-count);
  const rawLabels = stock.monthLabels.slice(-count);
  const labels = rawLabels.map(toLabel);

  // 前月比の計算
  const prevMonthRate: number | null =
    stock.previousMonthPrice !== null && stock.previousMonthPrice > 0
      ? ((stock.currentPrice - stock.previousMonthPrice) / stock.previousMonthPrice) * 100
      : null;

  // 銘柄名の頭文字（イニシャルアイコン用）
  const initial = stock.name.charAt(0);

  // 損益背景色
  const profitBg = stock.profit >= 0 ? "#fef2f2" : "#eff6ff";

  return (
    <div
      style={{
        background: "white",
        borderRadius: "16px",
        padding: "20px",
        boxShadow: "0 1px 4px rgba(0,0,0,0.05)",
      }}
    >
      {/* ── ヘッダー行（下線付き） ── */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          paddingBottom: "16px",
          borderBottom: "1px solid #f0f2f5",
          marginBottom: "14px",
        }}
      >
        {/* イニシャルアイコン（44px） */}
        <div
          style={{
            width: "44px",
            height: "44px",
            borderRadius: "12px",
            backgroundColor: stock.color,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <span style={{ fontSize: "18px", fontWeight: 800, color: "white" }}>
            {initial}
          </span>
        </div>

        {/* 銘柄名・ticker・market */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <p
            style={{
              fontSize: "17px",
              fontWeight: 700,
              color: "#1e2130",
              margin: 0,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {stock.name}
          </p>
          <p style={{ fontSize: "12px", color: "#8c90a0", margin: "2px 0 0" }}>
            {stock.ticker} ・ {stock.market}
          </p>
        </div>

        {/* 現在価格＆取得単価 */}
        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <p
            style={{
              fontSize: "22px",
              fontWeight: 800,
              color: "#1e2130",
              margin: 0,
            }}
          >
            {formatNative(stock.currentPrice, stock.currency)}
          </p>
          <p style={{ fontSize: "11px", color: "#8c90a0", margin: "2px 0 0" }}>
            取得単価 {formatNative(stock.acquiredPrice, stock.currency)}
          </p>
        </div>
      </div>

      {/* ── メトリクス 4枠 ── */}
      <div
        style={{
          display: "flex",
          gap: "8px",
          marginBottom: "14px",
        }}
      >
        {/* 評価損益（損益率サブ付き） */}
        <div
          style={{
            flex: 1,
            background: profitBg,
            borderRadius: "8px",
            padding: "10px",
            textAlign: "center",
          }}
        >
          <p style={{ fontSize: "9px", color: "#8c90a0", margin: "0 0 2px", fontWeight: 500 }}>
            評価損益
          </p>
          <p
            className={plColor(stock.profit)}
            style={{ fontSize: "12px", fontWeight: 700, margin: 0 }}
          >
            {formatSignedYen(stock.profit)}
          </p>
          <p
            className={plColor(stock.profitRate)}
            style={{ fontSize: "10px", margin: "1px 0 0" }}
          >
            {formatSignedPercent(stock.profitRate)}
          </p>
        </div>

        {/* 月間変動 */}
        <div
          style={{
            flex: 1,
            background: "#f6f7fa",
            borderRadius: "8px",
            padding: "10px",
            textAlign: "center",
          }}
        >
          <p style={{ fontSize: "9px", color: "#8c90a0", margin: "0 0 2px", fontWeight: 500 }}>
            月間変動
          </p>
          <p
            className={stock.monthlyChangeRate !== null ? plColor(stock.monthlyChangeRate) : ""}
            style={{
              fontSize: "12px",
              fontWeight: 700,
              margin: 0,
              color: stock.monthlyChangeRate === null ? "#8c90a0" : undefined,
            }}
          >
            {stock.monthlyChangeRate !== null
              ? formatSignedPercent(stock.monthlyChangeRate)
              : "—"}
          </p>
        </div>

        {/* 前月比 */}
        <div
          style={{
            flex: 1,
            background: "#f6f7fa",
            borderRadius: "8px",
            padding: "10px",
            textAlign: "center",
          }}
        >
          <p style={{ fontSize: "9px", color: "#8c90a0", margin: "0 0 2px", fontWeight: 500 }}>
            前月比
          </p>
          <p
            className={prevMonthRate !== null ? plColor(prevMonthRate) : ""}
            style={{
              fontSize: "12px",
              fontWeight: 700,
              margin: 0,
              color: prevMonthRate === null ? "#8c90a0" : undefined,
            }}
          >
            {prevMonthRate !== null ? formatSignedPercent(prevMonthRate) : "—"}
          </p>
        </div>

        {/* 保有株数 */}
        <div
          style={{
            flex: 1,
            background: "#f6f7fa",
            borderRadius: "8px",
            padding: "10px",
            textAlign: "center",
          }}
        >
          <p style={{ fontSize: "9px", color: "#8c90a0", margin: "0 0 2px", fontWeight: 500 }}>
            保有
          </p>
          <p style={{ fontSize: "12px", fontWeight: 700, margin: 0, color: "#1e2130" }}>
            {stock.quantity}株
          </p>
        </div>
      </div>

      {/* ── 株価チャート枠 ── */}
      <div
        style={{
          background: "#fafbfc",
          borderRadius: "12px",
          padding: "14px",
          marginBottom: stock.comment !== null ? "14px" : 0,
        }}
      >
        {/* チャートヘッダー */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "8px",
          }}
        >
          <span style={{ fontSize: "11px", color: "#8c90a0" }}>株価 vs 取得単価</span>
          <PeriodToggle
            period={period}
            onChange={setPeriod}
            color={stock.color}
            labels={REPORT_PERIOD_LABELS}
          />
        </div>

        {/* チャート本体（height=160） */}
        <StockPriceChart
          prices={prices}
          avgCosts={avgCosts}
          labels={labels}
          color={stock.color}
          currency={stock.currency}
          height={160}
        />
      </div>

      {/* ── AI コメント（null の場合は非表示） ── */}
      {stock.comment !== null && (
        <div>
          {/* 「今月のコメント」ラベル（銘柄カラー縦バー付き） */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              marginBottom: "6px",
            }}
          >
            <div
              style={{
                width: "3px",
                height: "16px",
                borderRadius: "2px",
                backgroundColor: stock.color,
                flexShrink: 0,
              }}
            />
            <span style={{ fontSize: "14px", fontWeight: 700, color: "#1e2130" }}>
              今月のコメント
            </span>
          </div>

          {/* コメント本文 */}
          <p
            style={{
              fontSize: "14px",
              color: "#3a3f52",
              lineHeight: 1.8,
              margin: 0,
            }}
          >
            {stock.comment}
          </p>
        </div>
      )}
    </div>
  );
}
