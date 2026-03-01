"use client";
import { MonthlyProfitPoint } from "@/types";
import {
  BarChart,
  Bar,
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

// 日付ごとに株価損益・為替損益を集計（複数銘柄の場合）
function aggregate(data: MonthlyProfitPoint[]) {
  const map = new Map<string, { stockProfit: number; fxProfit: number }>();
  for (const d of data) {
    const prev = map.get(d.date) ?? { stockProfit: 0, fxProfit: 0 };
    map.set(d.date, {
      stockProfit: prev.stockProfit + d.stockProfit,
      fxProfit: prev.fxProfit + d.fxProfit,
    });
  }
  return Array.from(map.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, { stockProfit, fxProfit }]) => ({ date, stockProfit, fxProfit }));
}

export function ProfitAreaChart({ data }: Props) {
  const chartData = aggregate(data);
  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} tickLine={false} />
        <YAxis
          tick={{ fontSize: 12 }}
          tickLine={false}
          tickFormatter={(v: number) => `${(v / 10000).toFixed(0)}万`}
        />
        <Tooltip
          formatter={(v, name) => [
            typeof v === "number" ? `${v.toLocaleString()}円` : String(v),
            name === "stockProfit" ? "株価損益" : "為替損益",
          ]}
        />
        <Legend
          formatter={(value) => (value === "stockProfit" ? "株価損益" : "為替損益")}
        />
        <Bar dataKey="stockProfit" stackId="profit" fill="#3b82f6" />
        <Bar dataKey="fxProfit" stackId="profit" fill="#f97316" />
      </BarChart>
    </ResponsiveContainer>
  );
}
