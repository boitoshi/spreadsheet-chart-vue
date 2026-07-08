/** 期間切替ボタングループ */
import type React from "react";

export type Period = "3M" | "6M" | "1Y" | "ALL";

const DEFAULT_LABELS: Record<Period, string> = {
  "3M": "3M",
  "6M": "6M",
  "1Y": "1Y",
  ALL: "ALL",
};

interface Props {
  period: Period;
  onChange: (p: Period) => void;
  color: string;
  labels?: Record<Period, string>;
}

const PERIODS: Period[] = ["3M", "6M", "1Y", "ALL"];

export function PeriodToggle({ period, onChange, color, labels }: Props): React.ReactElement {
  const displayLabels = labels ?? DEFAULT_LABELS;
  return (
    <div style={{ display: "flex", gap: "4px" }}>
      {PERIODS.map((p) => {
        const isActive = p === period;
        return (
          <button
            key={p}
            onClick={() => onChange(p)}
            style={{
              fontSize: "9px",
              fontWeight: 600,
              padding: "3px 7px",
              borderRadius: "4px",
              border: "none",
              cursor: "pointer",
              backgroundColor: isActive ? color : "#f0f2f5",
              color: isActive ? "white" : "#8c90a0",
              transition: "background-color 0.15s",
            }}
          >
            {displayLabels[p]}
          </button>
        );
      })}
    </div>
  );
}
