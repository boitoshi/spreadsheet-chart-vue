/** CTA（行動喚起）ボックス — 証券口座開設の案内 */
import type React from "react";

export function CtaBox(): React.ReactElement {
  return (
    <div
      style={{
        background: "#eef1f7",
        borderRadius: "16px",
        padding: "20px",
      }}
    >
      {/* タイトル */}
      <p style={{ fontSize: "13px", fontWeight: 700, color: "#1e2130", margin: "0 0 8px" }}>
        📌 証券口座の開設はこちら
      </p>

      {/* 本文 */}
      <p
        style={{
          fontSize: "13px",
          color: "#3a3f52",
          lineHeight: 1.7,
          margin: "0 0 8px",
        }}
      >
        楽天証券・SBI証券・マネックス証券など、単元未満株が購入できる証券会社なら1株からポケモン関連銘柄に投資できます。
      </p>

      {/* サブテキスト */}
      <p style={{ fontSize: "12px", color: "#8c90a0", margin: 0 }}>
        みなさんもポケモン銘柄へお布施投資しましょう！
      </p>
    </div>
  );
}
