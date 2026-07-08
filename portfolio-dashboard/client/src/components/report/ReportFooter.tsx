/** 月次レポートフッター — サイト名・免責事項 */
import type React from "react";

export function ReportFooter(): React.ReactElement {
  return (
    <div style={{ textAlign: "center", padding: "8px 0 4px" }}>
      <p style={{ fontSize: "11px", color: "#b0b4c3", margin: "0 0 4px" }}>
        pokebros.net ・ ポケブロス
      </p>
      <p style={{ fontSize: "11px", color: "#b0b4c3", margin: 0 }}>
        ※ 本レポートは投資助言ではありません。投資は自己責任でお願いします。
      </p>
    </div>
  );
}
