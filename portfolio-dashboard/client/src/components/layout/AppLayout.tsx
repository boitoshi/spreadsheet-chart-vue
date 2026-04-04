import { NavLink, Outlet } from "react-router-dom";
import { clsx } from "clsx";

const navItems = [
  { to: "/", label: "ダッシュボード" },
  { to: "/portfolio", label: "ポートフォリオ" },
  { to: "/history", label: "損益推移" },
  { to: "/currency", label: "為替レート" },
  { to: "/dividend", label: "配当・分配金" },
  { to: "/reports", label: "月次レポート" },
];

export function AppLayout() {
  return (
    <>
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 gap-8">
            <span className="font-bold text-gray-900 text-lg">Portfolio</span>
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  clsx(
                    "text-sm transition-colors",
                    isActive
                      ? "text-blue-600 font-medium"
                      : "text-gray-600 hover:text-gray-900",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </>
  );
}
