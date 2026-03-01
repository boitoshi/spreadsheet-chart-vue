import { KpiSummary } from "@/types";
import { formatCagr, formatJpy, formatPercent } from "@/lib/formatters";

interface Props {
  kpi: KpiSummary;
}

export function KpiCards({ kpi }: Props) {
  const cards = [
    { label: "評価額合計", value: formatJpy(kpi.totalValue), positive: null },
    { label: "損益合計", value: formatJpy(kpi.totalProfit), positive: kpi.totalProfit >= 0 },
    { label: "損益率", value: formatPercent(kpi.profitRate), positive: kpi.profitRate >= 0 },
    {
      label: "CAGR（年率）",
      value: kpi.portfolioCagr != null ? formatCagr(kpi.portfolioCagr) : "-",
      positive: kpi.portfolioCagr != null ? kpi.portfolioCagr >= 0 : null,
    },
  ];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c) => (
        <div key={c.label} className="bg-white rounded-lg border border-gray-200 p-5">
          <p className="text-sm text-gray-500">{c.label}</p>
          <p
            className={`text-2xl font-bold mt-1 ${
              c.positive === null
                ? "text-gray-900"
                : c.positive
                  ? "text-green-600"
                  : "text-red-600"
            }`}
          >
            {c.value}
          </p>
        </div>
      ))}
    </div>
  );
}
