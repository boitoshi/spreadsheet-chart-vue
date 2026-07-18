/**
 * formatters.ts のユニットテスト
 * 既存: formatJpy / formatPercent / formatYearMonth / profitColor
 * 追加: formatMan / formatNative / plColor / formatSignedYen / formatSignedPercent
 *       / formatMonthTick / formatMonthFull
 */
import { describe, it, expect } from "vitest";
import {
  formatMan,
  formatNative,
  plColor,
  formatSignedYen,
  formatSignedPercent,
  formatMonthTick,
  formatMonthFull,
  // 既存関数（回帰確認）
  formatJpy,
  formatPercent,
  profitColor,
} from "../lib/formatters";

describe("formatMan", () => {
  it("正の値を¥N万形式で返す", () => {
    expect(formatMan(1_000_000)).toBe("¥100万");
    expect(formatMan(1_234_567)).toBe("¥123万");
  });

  it("負の値も正しく四捨五入する", () => {
    expect(formatMan(-500_000)).toBe("¥-50万");
  });

  it("ゼロを正しく返す", () => {
    expect(formatMan(0)).toBe("¥0万");
  });

  it("四捨五入する", () => {
    // 15_000 / 10_000 = 1.5 → round → 2
    expect(formatMan(15_000)).toBe("¥2万");
    // 14_999 / 10_000 = 1.4999 → round → 1
    expect(formatMan(14_999)).toBe("¥1万");
  });
});

describe("formatNative", () => {
  it("USD は $XX.XX 形式（小数2桁・カンマ）", () => {
    expect(formatNative(174.4, "USD")).toBe("$174.40");
    expect(formatNative(1234.5, "USD")).toBe("$1,234.50");
  });

  it("JPY は ¥カンマ整数形式", () => {
    expect(formatNative(8775, "JPY")).toBe("¥8,775");
    expect(formatNative(1_000_000, "JPY")).toBe("¥1,000,000");
  });

  it("JPY の小数は四捨五入される", () => {
    expect(formatNative(8775.6, "JPY")).toBe("¥8,776");
  });
});

describe("plColor", () => {
  it("正の値は text-[#E53935] を返す（赤=利益）", () => {
    expect(plColor(100)).toBe("text-[#E53935]");
    expect(plColor(0)).toBe("text-[#E53935]");
  });

  it("負の値は text-[#1565C0] を返す（青=損失）", () => {
    expect(plColor(-1)).toBe("text-[#1565C0]");
    expect(plColor(-100_000)).toBe("text-[#1565C0]");
  });
});

describe("formatSignedYen", () => {
  it("正の値に + プレフィックスを付ける", () => {
    expect(formatSignedYen(123_456)).toBe("+¥123,456");
  });

  it("負の値に - プレフィックスを付ける", () => {
    expect(formatSignedYen(-78_900)).toBe("-¥78,900");
  });

  it("ゼロは + として扱う", () => {
    expect(formatSignedYen(0)).toBe("+¥0");
  });

  it("小数は四捨五入される", () => {
    expect(formatSignedYen(123.7)).toBe("+¥124");
    expect(formatSignedYen(-456.3)).toBe("-¥456");
  });
});

describe("formatSignedPercent", () => {
  it("正の値に + プレフィックスを付ける（小数2桁）", () => {
    expect(formatSignedPercent(1.23)).toBe("+1.23%");
    expect(formatSignedPercent(0)).toBe("+0.00%");
  });

  it("負の値に - プレフィックスを付ける（小数2桁）", () => {
    expect(formatSignedPercent(-1.23)).toBe("-1.23%");
  });

  it("整数値も小数2桁で表示", () => {
    expect(formatSignedPercent(5)).toBe("+5.00%");
  });
});

describe("formatMonthTick", () => {
  it("YYYY/M を M月 に変換する", () => {
    expect(formatMonthTick("2026/6")).toBe("6月");
    expect(formatMonthTick("2023/12")).toBe("12月");
  });

  it("不正入力はそのまま返す", () => {
    expect(formatMonthTick("invalid")).toBe("invalid");
  });
});

describe("formatMonthFull", () => {
  it("YYYY/M を YYYY年M月 に変換する", () => {
    expect(formatMonthFull("2026/6")).toBe("2026年6月");
    expect(formatMonthFull("2023/12")).toBe("2023年12月");
  });

  it("不正入力はそのまま返す", () => {
    expect(formatMonthFull("invalid")).toBe("invalid");
  });
});

// ── 既存関数の回帰確認 ────────────────────────────────────────────
describe("既存: formatJpy", () => {
  it("円形式で返す", () => {
    expect(formatJpy(1_234_567)).toContain("1,234,567");
  });
});

describe("既存: formatPercent", () => {
  it("符号付きパーセントを返す", () => {
    expect(formatPercent(12.34)).toBe("+12.34%");
    expect(formatPercent(-5.6)).toBe("-5.60%");
  });
});

describe("既存: profitColor", () => {
  it("正は green-600", () => {
    expect(profitColor(1)).toBe("text-green-600");
  });
  it("負は red-600", () => {
    expect(profitColor(-1)).toBe("text-red-600");
  });
});
