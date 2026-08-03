/** 資産推移＆損益推移チャート（ComposedChart / dual Y軸）*/
import type React from "react";
import {
  ComposedChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { TotalHistory } from "@/types";
import { formatMan, formatMonthTick, formatMonthFull } from "@/lib/formatters";
import { shouldShowDots } from "@/lib/chartUtils";

interface Props {
  totalHistory: TotalHistory;
  totalProfit: number;
  /** チャート高さ（px）。省略時は 260 */
  height?: number;
}

/** 円表示ツールチップ用 */
function fmtJpy(v: number): string {
  return `¥${Math.round(v).toLocaleString("ja-JP")}`;
}

export function AssetTrendChart({ totalHistory, totalProfit, height }: Props): React.ReactElement {
  // P/L の色（利益→赤、損失→青）
  const plStroke = totalProfit >= 0 ? "#E53935" : "#1565C0";
  const plGradId = totalProfit >= 0 ? "plGradRed" : "plGradBlue";
  const plGradColor = plStroke;

  // チャートデータに変換（dataKey には年付きの "YYYY/M" をそのまま使い、表示はフォーマッタで変換）
  const chartData = totalHistory.months.map((m, i) => ({
    month: m,
    asset: totalHistory.assetValues[i] ?? 0,
    pl: totalHistory.plValues[i] ?? 0,
  }));

  // 点が密集すると丸が線を潰すため、月数が多いときはドットを出さない
  const showDots = shouldShowDots(chartData.length);

  return (
    <div
      style={{
        background: "white",
        borderRadius: "14px",
        padding: "18px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
        height: "100%",
      }}
    >
      <p style={{ fontSize: "10px", color: "#8c90a0", margin: "0 0 12px", fontWeight: 500 }}>
        資産推移 ・ 損益推移
      </p>
      <ResponsiveContainer width="100%" height={height ?? 260}>
        <ComposedChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
          {/* SVG ネイティブ要素としてグラデーション定義 */}
          <defs>
            {/* 総資産グラデーション */}
            <linearGradient id="assetGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="10%" stopColor="#1565C0" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#1565C0" stopOpacity={0} />
            </linearGradient>
            {/* P/L グラデーション（淡色） */}
            <linearGradient id={plGradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="10%" stopColor={plGradColor} stopOpacity={0.15} />
              <stop offset="95%" stopColor={plGradColor} stopOpacity={0} />
            </linearGradient>
          </defs>

          <XAxis
            dataKey="month"
            tick={{ fontSize: 9, fill: "#b0b4c3" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={formatMonthTick}
          />

          {/* 左軸: 総資産 */}
          <YAxis
            yAxisId="left"
            tick={{ fontSize: 9, fill: "#1565C0" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={formatMan}
            width={54}
          />

          {/* 右軸: 損益 */}
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 9, fill: plStroke }}
            axisLine={false}
            tickLine={false}
            tickFormatter={formatMan}
            width={54}
          />

          <Tooltip
            formatter={(value, name) => [
              typeof value === "number" ? fmtJpy(value) : String(value),
              name === "asset" ? "総資産" : "損益",
            ]}
            labelFormatter={(label) => formatMonthFull(String(label ?? ""))}
            contentStyle={{ fontSize: "11px" }}
          />
          <Legend
            verticalAlign="bottom"
            height={28}
            formatter={(value: string) =>
              value === "asset" ? "総資産" : "損益"
            }
            wrapperStyle={{ fontSize: "10px" }}
          />

          {/* 総資産エリア */}
          <Area
            yAxisId="left"
            type="linear"
            dataKey="asset"
            stroke="#1565C0"
            strokeWidth={2}
            fill="url(#assetGrad)"
            dot={
              showDots
                ? { r: 3, fill: "white", stroke: "#1565C0", strokeWidth: 1.5 }
                : false
            }
            activeDot={{ r: 4 }}
            name="asset"
          />

          {/* 損益エリア */}
          <Area
            yAxisId="right"
            type="linear"
            dataKey="pl"
            stroke={plStroke}
            strokeDasharray="5 3"
            strokeWidth={1.5}
            fill={`url(#${plGradId})`}
            dot={false}
            name="pl"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
