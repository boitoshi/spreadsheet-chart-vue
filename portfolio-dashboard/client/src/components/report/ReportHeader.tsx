/** 月次レポートページ用グラデーションヘッダー */
import type React from "react";

interface Props {
  year: number;
  month: number;
}

export function ReportHeader({ year, month }: Props): React.ReactElement {
  return (
    <div
      style={{
        background: "linear-gradient(135deg,#0d47a1,#1565c0 40%,#1976d2)",
        padding: "40px 24px 32px",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* 装飾円（右上） */}
      <div
        style={{
          position: "absolute",
          top: "-40px",
          right: "-40px",
          width: "200px",
          height: "200px",
          borderRadius: "50%",
          background: "rgba(255,255,255,0.05)",
          pointerEvents: "none",
        }}
      />

      {/* ラベル */}
      <p
        style={{
          fontSize: "11px",
          color: "rgba(255,255,255,0.5)",
          fontWeight: 600,
          letterSpacing: "0.1em",
          margin: "0 0 6px",
        }}
      >
        POKÉMON STOCK PORTFOLIO
      </p>

      {/* タイトル */}
      <p
        style={{
          fontSize: "28px",
          fontWeight: 900,
          color: "white",
          margin: "0 0 8px",
          lineHeight: 1.2,
        }}
      >
        {`【ポケモン投資】${year}年${month}月の状況`}
      </p>

      {/* サブタイトル */}
      <p
        style={{
          fontSize: "13px",
          color: "rgba(255,255,255,0.6)",
          margin: 0,
        }}
      >
        ポケモン関連銘柄の月次投資レポート
      </p>
    </div>
  );
}
