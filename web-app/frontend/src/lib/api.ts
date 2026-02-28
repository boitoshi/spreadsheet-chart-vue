const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    next: { revalidate: 300 }, // 5分キャッシュ
  });
  if (!res.ok) {
    throw new Error(`API エラー: ${res.status} ${path}`);
  }
  return res.json() as Promise<T>;
}

export { fetchApi };
