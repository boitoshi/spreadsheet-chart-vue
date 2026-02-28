"use client";
import { CurrencyRatePoint } from "@/types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Props {
  data: CurrencyRatePoint[];
}

export function CurrencyLineChart({ data }: Props) {
  // USD/JPY のみ表示
  const usdJpy = data.filter((d) => d.pair === "USD/JPY");
  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={usdJpy} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 12 }} tickLine={false} />
        <YAxis domain={["auto", "auto"]} tick={{ fontSize: 12 }} tickLine={false} />
        <Tooltip
          formatter={(v) => [
            typeof v === "number" ? `${v.toFixed(2)} 円` : String(v),
            "USD/JPY",
          ]}
        />
        <Line
          type="monotone"
          dataKey="rate"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
