"use client";
import { MonthlyProfitPoint } from "@/types";
import { COLORS, buildPivotData } from "@/lib/chartUtils";
import {
  AreaChart,
  Area,
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
  return buildPivotData(data, (d) => d.value);
}

export function AllocationTrendChart({ data }: Props) {
  const { chartData, names } = buildChartData(data);
  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart
        data={chartData}
        margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} tickLine={false} />
        <YAxis
          tick={{ fontSize: 12 }}
          tickLine={false}
          tickFormatter={(v: number) => `${(v / 10000).toFixed(0)}万`}
        />
        <Tooltip
          formatter={(v) => [
            typeof v === "number" ? `${v.toLocaleString()}円` : String(v),
            "評価額",
          ]}
        />
        <Legend />
        {names.map((name, i) => (
          <Area
            key={name}
            type="monotone"
            dataKey={name}
            stackId="allocation"
            stroke={COLORS[i % COLORS.length]}
            fill={COLORS[i % COLORS.length]}
            fillOpacity={0.6}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}
