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

/** 万円表示（例: ¥123万）。v/10000 を四捨五入整数 */
export function formatMan(v: number): string {
  return `¥${Math.round(v / 10000)}万`;
}

/** ネイティブ通貨表示。USD→"$174.40"（小数2桁・カンマ）、JPY→"¥8,775"（整数・カンマ）*/
export function formatNative(v: number, currency: "JPY" | "USD"): string {
  if (currency === "USD") {
    return `$${v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return `¥${Math.round(v).toLocaleString("ja-JP")}`;
}

/** 損益に応じた色クラス（赤=利益、青=損失。日本株式市場の慣習）*/
export function plColor(v: number): string {
  return v >= 0 ? "text-[#E53935]" : "text-[#1565C0]";
}

/** 符号付き円表示（例: "+¥123,456" / "-¥123,456"）*/
export function formatSignedYen(v: number): string {
  const abs = Math.abs(Math.round(v)).toLocaleString("ja-JP");
  return v >= 0 ? `+¥${abs}` : `-¥${abs}`;
}

/** 符号付きパーセント表示（例: "+1.23%" / "-1.23%"）*/
export function formatSignedPercent(v: number): string {
  const sign = v >= 0 ? "+" : "-";
  return `${sign}${Math.abs(v).toFixed(2)}%`;
}
