"use client";
import { useRouter, usePathname } from "next/navigation";

interface Props {
  symbols: string[];
  current?: string;
}

export function StockFilter({ symbols, current }: Props) {
  const router = useRouter();
  const pathname = usePathname();

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const v = e.target.value;
    router.push(v ? `${pathname}?stock=${v}` : pathname);
  };

  return (
    <select
      value={current ?? ""}
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
