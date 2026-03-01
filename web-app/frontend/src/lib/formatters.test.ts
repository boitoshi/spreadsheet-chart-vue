import { describe, it, expect } from "vitest";
import { formatJpy, formatPercent, formatYearMonth, profitColor } from "./formatters";

// Intl.NumberFormat の円記号は実行環境（ICU版）により ¥(U+00A5) または ￥(U+FFE5) になる
const YEN_PATTERN = /[¥￥]/;

describe("formatJpy", () => {
  it("円記号とカンマ区切りの数値を含む文字列を返す", () => {
    const result = formatJpy(1234567);
    expect(result).toMatch(YEN_PATTERN);
    expect(result).toContain("1,234,567");
  });

  it("小数点以下を四捨五入する", () => {
    expect(formatJpy(1000.9)).toContain("1,001");
  });

  it("ゼロは 0 を含む文字列を返す", () => {
    expect(formatJpy(0)).toMatch(YEN_PATTERN);
    expect(formatJpy(0)).toContain("0");
  });

  it("マイナス金額は負号を含む文字列を返す", () => {
    const result = formatJpy(-50000);
    expect(result).toContain("50,000");
    expect(result).toMatch(/-/);
  });
});

describe("formatPercent", () => {
  it("プラスの値には + 符号を付ける", () => {
    expect(formatPercent(12.34)).toBe("+12.34%");
  });

  it("マイナスの値はそのままマイナス符号", () => {
    expect(formatPercent(-5.6)).toBe("-5.60%");
  });

  it("ゼロは + 符号付き（0以上として扱う）", () => {
    expect(formatPercent(0)).toBe("+0.00%");
  });

  it("digits 引数で小数桁数を変更できる", () => {
    expect(formatPercent(3.14159, 4)).toBe("+3.1416%");
  });
});

describe("formatYearMonth", () => {
  it("YYYY-MM-末 形式を YYYY年MM月 に変換する", () => {
    expect(formatYearMonth("2024-01-末")).toBe("2024年01月");
  });

  it("YYYY-MM-DD 形式も YYYY年MM月 に変換する", () => {
    expect(formatYearMonth("2025-12-31")).toBe("2025年12月");
  });

  it("パターンに一致しない文字列はそのまま返す", () => {
    expect(formatYearMonth("不明")).toBe("不明");
  });
});

describe("profitColor", () => {
  it("プラスの損益は緑クラスを返す", () => {
    expect(profitColor(1000)).toBe("text-green-600");
  });

  it("ゼロは緑クラスを返す（0以上）", () => {
    expect(profitColor(0)).toBe("text-green-600");
  });

  it("マイナスの損益は赤クラスを返す", () => {
    expect(profitColor(-1)).toBe("text-red-600");
  });
});
