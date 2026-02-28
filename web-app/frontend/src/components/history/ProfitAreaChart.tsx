"use client";
import { MonthlyProfitPoint } from "@/types";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Props {
  data: MonthlyProfitPoint[];
}

// 日付ごとに損益合計を集計（複数銘柄の場合）
function aggregate(data: MonthlyProfitPoint[]) {
  const map = new Map<string, number>();
  for (const d of data) {
    map.set(d.date, (map.get(d.date) ?? 0) + d.profit);
  }
  return Array.from(map.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, profit]) => ({ date, profit }));
}

export function ProfitAreaChart({ data }: Props) {
  const chartData = aggregate(data);
  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="profitGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
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
            "損益合計",
          ]}
        />
        <Area
          type="monotone"
          dataKey="profit"
          stroke="#3b82f6"
          strokeWidth={2}
          fill="url(#profitGrad)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
