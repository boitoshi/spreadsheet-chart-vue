/** 円表示（例: ¥1,234,567）*/
export function formatJpy(value: number): string {
  return new Intl.NumberFormat("ja-JP", {
    style: "currency",
    currency: "JPY",
    maximumFractionDigits: 0,
  }).format(value);
}

/** パーセント表示（例: +12.34%）*/
export function formatPercent(value: number, digits = 2): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

/** 日付表示（YYYY-MM-末 → YYYY年MM月）*/
export function formatYearMonth(dateStr: string): string {
  const match = dateStr.match(/^(\d{4})-(\d{2})/);
  if (!match) return dateStr;
  return `${match[1]}年${match[2]}月`;
}

/** 損益に応じた色クラスを返す */
export function profitColor(value: number): string {
  return value >= 0 ? "text-green-600" : "text-red-600";
}
