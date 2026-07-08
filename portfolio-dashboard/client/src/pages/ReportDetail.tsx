/**
 * 月次レポート詳細ページ
 * - /api/reports/:year/:month/data が成功: 新デザイン（Phase C）
 * - 404 / エラー: 既存 Markdown 表示（ReportMarkdown）へフォールバック
 */
import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { fetchApi } from "@/lib/api";
import type { ReportDataResponse } from "@/types";
import { ReportMarkdown } from "@/components/report/ReportMarkdown";
import { ReportHeader } from "@/components/report/ReportHeader";
import { ReportSummaryCard } from "@/components/report/ReportSummaryCard";
import { ReportStockCard } from "@/components/report/ReportStockCard";
import { CtaBox } from "@/components/report/CtaBox";
import { ReportFooter } from "@/components/report/ReportFooter";
import { AssetTrendChart } from "@/components/dashboard/AssetTrendChart";

export default function ReportDetail() {
  const { year, month } = useParams<{ year: string; month: string }>();

  // 新デザイン用データクエリ（404 はリトライしない）
  const { data: reportData, isLoading, isError } = useQuery({
    queryKey: ["reportData", year, month],
    queryFn: () => fetchApi<ReportDataResponse>(`/api/reports/${year}/${month}/data`),
    enabled: !!year && !!month,
    retry: false,
  });

  // データ取得中
  if (isLoading) {
    return <p className="text-gray-500">読み込み中...</p>;
  }

  // データ取得失敗 → 既存 Markdown 表示へフォールバック
  if (isError || !reportData) {
    return <ReportMarkdown />;
  }

  // 合計値の計算
  const totalValue = reportData.stocks.reduce((sum, s) => sum + s.value, 0);
  const totalProfit = reportData.stocks.reduce((sum, s) => sum + s.profit, 0);
  const totalCost = totalValue - totalProfit;
  const totalProfitRate = totalCost > 0 ? (totalProfit / totalCost) * 100 : 0;

  const { year: y, month: m, exchangeRate, reportDate } = reportData.meta;

  return (
    // AppLayout の main padding を負マージンで打ち消し（全幅ヘッダー用）
    <div className="-mt-8 -mx-4 sm:-mx-6 lg:-mx-8">
      {/* グラデーションヘッダー（全幅） */}
      <ReportHeader year={y} month={m} />

      {/* メインコンテンツ（max-w-[680px] 中央寄せ） */}
      <div
        style={{
          maxWidth: "680px",
          margin: "0 auto",
          padding: "24px 16px 40px",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        {/* 一覧へ戻るリンク */}
        <Link
          to="/reports"
          style={{
            fontSize: "13px",
            color: "#8c90a0",
            textDecoration: "none",
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
          }}
        >
          ← 一覧へ
        </Link>

        {/* intro がある場合：今月のサマリーカード */}
        {reportData.intro && (
          <div
            style={{
              background: "white",
              borderRadius: "16px",
              padding: "20px",
              boxShadow: "0 1px 4px rgba(0,0,0,0.05)",
            }}
          >
            <p style={{ fontSize: "13px", color: "#8c90a0", margin: "0 0 8px", fontWeight: 500 }}>
              今月のサマリー
            </p>
            <p style={{ fontSize: "15px", color: "#1e2130", lineHeight: 1.8, margin: 0 }}>
              {reportData.intro}
            </p>
          </div>
        )}

        {/* サマリーカード */}
        <ReportSummaryCard
          stocks={reportData.stocks}
          totalValue={totalValue}
          totalProfit={totalProfit}
          totalProfitRate={totalProfitRate}
          exchangeRate={exchangeRate}
          reportDate={reportDate}
        />

        {/* 銘柄別カード */}
        {reportData.stocks.map((stock) => (
          <ReportStockCard key={stock.code} stock={stock} />
        ))}

        {/* 資産推移・損益推移チャート */}
        <div
          style={{
            background: "white",
            borderRadius: "16px",
            boxShadow: "0 1px 4px rgba(0,0,0,0.05)",
            overflow: "hidden",
          }}
        >
          <AssetTrendChart
            totalHistory={reportData.totalHistory}
            totalProfit={totalProfit}
            height={220}
          />
        </div>

        {/* summary がある場合：まとめカード */}
        {reportData.summary && (
          <div
            style={{
              background: "white",
              borderRadius: "16px",
              padding: "20px",
              boxShadow: "0 1px 4px rgba(0,0,0,0.05)",
            }}
          >
            <p style={{ fontSize: "13px", color: "#8c90a0", margin: "0 0 8px", fontWeight: 500 }}>
              まとめ
            </p>
            <p style={{ fontSize: "15px", color: "#1e2130", lineHeight: 1.8, margin: 0 }}>
              {reportData.summary}
            </p>
          </div>
        )}

        {/* CTA ボックス */}
        <CtaBox />

        {/* フッター */}
        <ReportFooter />
      </div>
    </div>
  );
}
