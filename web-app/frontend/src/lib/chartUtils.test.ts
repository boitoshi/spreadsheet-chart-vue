import { describe, it, expect } from "vitest";
import { buildPivotData } from "./chartUtils";
import type { MonthlyProfitPoint } from "@/types";

/** テスト用のサンプルデータを生成するヘルパー */
function makePoint(
  overrides: Partial<MonthlyProfitPoint> & {
    date: string;
    code: string;
    name: string;
  },
): MonthlyProfitPoint {
  return {
    profit: 0,
    value: 0,
    profitRate: 0,
    currency: "JPY",
    stockProfit: 0,
    fxProfit: 0,
    ...overrides,
  };
}

describe("buildPivotData", () => {
  const data: MonthlyProfitPoint[] = [
    makePoint({ date: "2024-01-末", code: "7974.T", name: "任天堂", value: 700000 }),
    makePoint({ date: "2024-01-末", code: "NVDA", name: "エヌビディア", value: 300000 }),
    makePoint({ date: "2024-02-末", code: "7974.T", name: "任天堂", value: 720000 }),
    makePoint({ date: "2024-02-末", code: "NVDA", name: "エヌビディア", value: 350000 }),
  ];

  it("銘柄名の一覧を返す", () => {
    const { names } = buildPivotData(data, (d) => d.value);
    expect(names).toContain("任天堂");
    expect(names).toContain("エヌビディア");
    expect(names).toHaveLength(2);
  });

  it("日付ごとに銘柄の値をまとめたチャートデータを返す", () => {
    const { chartData } = buildPivotData(data, (d) => d.value);
    expect(chartData).toHaveLength(2);
    expect(chartData[0]).toMatchObject({
      date: "2024-01-末",
      任天堂: 700000,
      エヌビディア: 300000,
    });
    expect(chartData[1]).toMatchObject({
      date: "2024-02-末",
      任天堂: 720000,
      エヌビディア: 350000,
    });
  });

  it("chartData は日付の昇順でソートされる", () => {
    const unsorted: MonthlyProfitPoint[] = [
      makePoint({ date: "2024-03-末", code: "7974.T", name: "任天堂", value: 100 }),
      makePoint({ date: "2024-01-末", code: "7974.T", name: "任天堂", value: 200 }),
      makePoint({ date: "2024-02-末", code: "7974.T", name: "任天堂", value: 300 }),
    ];
    const { chartData } = buildPivotData(unsorted, (d) => d.value);
    const dates = chartData.map((row) => row.date);
    expect(dates).toEqual(["2024-01-末", "2024-02-末", "2024-03-末"]);
  });

  it("getValue に profitRate を渡すと損益率のピボットを返す", () => {
    const rateData: MonthlyProfitPoint[] = [
      makePoint({ date: "2024-01-末", code: "NVDA", name: "エヌビディア", profitRate: 15.5 }),
    ];
    const { chartData } = buildPivotData(rateData, (d) => d.profitRate);
    expect(chartData[0]).toMatchObject({ エヌビディア: 15.5 });
  });

  it("データが空のとき空の結果を返す", () => {
    const { chartData, names } = buildPivotData([], (d) => d.value);
    expect(chartData).toHaveLength(0);
    expect(names).toHaveLength(0);
  });
});
