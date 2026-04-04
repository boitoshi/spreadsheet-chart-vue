import { MonthlyProfitPoint } from "@/types";

export const COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
];

/**
 * MonthlyProfitPoint[] を「日付 × 銘柄名」のピボット形式に変換する。
 * getValue で取り出す値フィールドを選択する。
 */
export function buildPivotData(
  data: MonthlyProfitPoint[],
  getValue: (d: MonthlyProfitPoint) => number,
): { chartData: Record<string, unknown>[]; names: string[] } {
  const dateSet = new Set<string>();
  const nameMap = new Map<string, string>(); // code -> name
  for (const d of data) {
    dateSet.add(d.date);
    nameMap.set(d.code, d.name);
  }
  const dates = Array.from(dateSet).sort((a, b) => a.localeCompare(b));
  const names = Array.from(nameMap.values());

  const pivotMap = new Map<string, Record<string, number>>();
  for (const d of data) {
    if (!pivotMap.has(d.date)) pivotMap.set(d.date, {});
    pivotMap.get(d.date)![d.name] = getValue(d);
  }

  return {
    chartData: dates.map((date) => ({ date, ...pivotMap.get(date) })),
    names,
  };
}
