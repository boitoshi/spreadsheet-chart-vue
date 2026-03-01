"use client";
import { MonthlyProfitPoint } from "@/types";
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

const COLORS = [
  "#3b82f6", "#10b981", "#f59e0b",
  "#ef4444", "#8b5cf6", "#06b6d4",
];

interface Props {
  data: MonthlyProfitPoint[];
}

function buildChartData(data: MonthlyProfitPoint[]) {
  const dateSet = new Set<string>();
  const nameMap = new Map<string, string>(); // code -> name
  for (const d of data) {
    dateSet.add(d.date);
    nameMap.set(d.code, d.name);
  }
  const dates = Array.from(dateSet).sort((a, b) => a.localeCompare(b));
  const names = Array.from(nameMap.values());

  const dateValueMap = new Map<string, Record<string, number>>();
  for (const d of data) {
    if (!dateValueMap.has(d.date)) dateValueMap.set(d.date, {});
    dateValueMap.get(d.date)![d.name] = d.value;
  }

  return {
    chartData: dates.map((date) => ({
      date,
      ...dateValueMap.get(date),
    })),
    names,
  };
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
