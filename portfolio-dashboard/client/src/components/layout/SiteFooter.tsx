/** 全ページ共通フッター — ブログへの導線（リンク集）・データ出典・免責・コピーライト */

const blogLinks = [
  {
    href: "https://www.pokebros.net/",
    label: "ポケブロス（ブログ本体）",
    note: "ポケモン情報がメイン",
  },
  {
    href: "https://www.pokebros.net/category/%e3%83%9d%e3%82%b1%e3%83%a2%e3%83%b3%e6%8a%95%e8%b3%87/",
    label: "【ポケモン投資】記事一覧",
    note: "月次レポートのブログ版",
  },
  {
    href: "https://www.pokebros.net/pokemon-investment-portfolio/",
    label: "ポートフォリオの全体像",
    note: "投資方針・銘柄の紹介",
  },
];

export function SiteFooter() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-wrap gap-x-12 gap-y-6">
          {/* リンク集（ブログへの導線） */}
          <div className="flex-1 min-w-60">
            <p className="text-sm font-bold text-gray-900 mb-2">
              ブログ「ポケブロス」
            </p>
            <p className="text-xs text-gray-500 leading-relaxed mb-3">
              このダッシュボードは、ポケモン情報ブログ「ポケブロス」の投資記録コーナーです。ブログ本体はポケモンの情報がメインで、株の話はその一部です。
            </p>
            <ul className="space-y-1.5">
              {blogLinks.map((link) => (
                <li key={link.href} className="text-xs">
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {link.label} ↗
                  </a>
                  <span className="text-gray-400 ml-2">{link.note}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* データの出典 */}
          <div className="flex-1 min-w-60">
            <p className="text-sm font-bold text-gray-900 mb-2">データの出典</p>
            <ul className="text-xs text-gray-500 leading-relaxed space-y-1">
              <li>
                株価・為替レート・株価指数（日経225 / S&amp;P500）: Yahoo
                Finance（yfinance ライブラリ経由で月末時点の値を取得）
              </li>
              <li>買付履歴・受取配当: 管理人自身の取引記録</li>
            </ul>
          </div>
        </div>

        {/* 免責・コピーライト */}
        <div className="border-t border-gray-100 mt-6 pt-4">
          <p className="text-xs text-gray-400 leading-relaxed">
            ※
            本サイトの情報は投資助言ではありません。データには誤り・遅延が含まれる場合があります。投資は自己責任でお願いします。
          </p>
          <p className="text-xs text-gray-400 mt-1">
            © {new Date().getFullYear()} ポケブロス（pokebros.net）
          </p>
        </div>
      </div>
    </footer>
  );
}
