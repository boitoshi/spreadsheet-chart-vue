"use client";
import { MonthlyProfitPoint } from "@/types";
import { COLORS, buildPivotData } from "@/lib/chartUtils";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface Props {
  data: MonthlyProfitPoint[];
}

function buildChartData(data: MonthlyProfitPoint[]) {
  return buildPivotData(data, (d) => d.profitRate);
}

export function StockCompareChart({ data }: Props) {
  const { chartData, names } = buildChartData(data);
  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart
        data={chartData}
        margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} tickLine={false} />
        <YAxis
          tick={{ fontSize: 12 }}
          tickLine={false}
          tickFormatter={(v: number) => `${v.toFixed(1)}%`}
        />
        <Tooltip
          formatter={(v) => [
            typeof v === "number" ? `${v.toFixed(2)}%` : String(v),
          ]}
        />
        <Legend />
        {names.map((name, i) => (
          <Line
            key={name}
            type="monotone"
            dataKey={name}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
