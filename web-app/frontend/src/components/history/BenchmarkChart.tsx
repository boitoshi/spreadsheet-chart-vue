"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import { BenchmarkPoint } from "@/types";

interface Props {
  data: BenchmarkPoint[];
}

function formatRate(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

export function BenchmarkChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <p className="text-gray-400 text-sm text-center py-8">データがありません</p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data} margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tickFormatter={formatRate} tick={{ fontSize: 11 }} />
        <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="4 2" />
        <Tooltip
          formatter={(value: number | undefined) =>
            value !== undefined ? formatRate(value) : "-"
          }
          labelStyle={{ fontWeight: 600 }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="portfolio"
          name="ポートフォリオ"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="nikkei225"
          name="日経225"
          stroke="#ef4444"
          strokeWidth={2}
          dot={false}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="sp500"
          name="S&P500"
          stroke="#10b981"
          strokeWidth={2}
          dot={false}
          connectNulls
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
