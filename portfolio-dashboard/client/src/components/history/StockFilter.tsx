import { useNavigate, useSearchParams } from "react-router-dom";

interface Props {
  symbols: string[];
  current?: string;
}

export function StockFilter({ symbols, current }: Props) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const v = e.target.value;
    if (v) {
      navigate(`/history?stock=${v}`);
    } else {
      navigate("/history");
    }
  };

  return (
    <select
      value={current ?? searchParams.get("stock") ?? ""}
      onChange={handleChange}
      className="border border-gray-200 rounded-md px-3 py-2 text-sm bg-white text-gray-700"
    >
      <option value="">全銘柄</option>
      {symbols.map((s) => (
        <option key={s} value={s}>
          {s}
        </option>
      ))}
    </select>
  );
}
