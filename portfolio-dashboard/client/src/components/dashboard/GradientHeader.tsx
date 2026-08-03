/** グラデーションヘッダー — ポートフォリオタイトルと基準日を表示 */
import type React from "react";

interface Props {
  year: number;
  month: number;
  usdJpy: number;
}

export function GradientHeader({
  year,
  month,
  usdJpy,
}: Props): React.ReactElement {
  return (
    <div
      style={{
        background: "linear-gradient(135deg,#0d47a1,#1565c0 40%,#1976d2)",
        padding: "16px 28px",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        {/* 左: ラベル＋タイトル */}
        <div>
          <p
            style={{
              fontSize: "10px",
              color: "rgba(255,255,255,0.4)",
              fontWeight: 600,
              letterSpacing: "0.1em",
              margin: 0,
            }}
          >
            POKÉMON STOCK PORTFOLIO
          </p>
          <p
            style={{
              fontSize: "18px",
              fontWeight: 800,
              color: "white",
              margin: "2px 0 0",
            }}
          >
            {`【ポケモン投資】${year}年${month}月の状況`}
          </p>
        </div>
        {/* 右: 基準日＋為替レート */}
        <p
          style={{
            fontSize: "11px",
            color: "rgba(255,255,255,0.5)",
            margin: 0,
          }}
        >
          {`${year}年${month}月末 ・ USD/JPY ¥${usdJpy.toFixed(2)}`}
        </p>
      </div>
    </div>
  );
}
