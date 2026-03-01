import type { Metadata } from "next";
import { Geist } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ポートフォリオダッシュボード",
  description: "投資ポートフォリオ管理アプリ",
};

const navItems = [
  { href: "/", label: "ダッシュボード" },
  { href: "/portfolio", label: "ポートフォリオ" },
  { href: "/history", label: "損益推移" },
  { href: "/currency", label: "為替レート" },
  { href: "/dividend", label: "配当・分配金" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className={`${geistSans.variable} antialiased min-h-screen bg-gray-50`}>
        {/* ナビゲーションバー */}
        <nav className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center h-16 gap-8">
              <span className="font-bold text-gray-900 text-lg">Portfolio</span>
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        </nav>
        {/* ページコンテンツ */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
