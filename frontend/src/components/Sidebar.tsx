"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Eye,
  TrendingDown,
  Settings,
} from "lucide-react";
import clsx from "clsx";

const navItems = [
  { href: "/", label: "ダッシュボード", icon: LayoutDashboard },
  { href: "/monitors", label: "モニター", icon: Eye },
  { href: "/changes", label: "価格変動", icon: TrendingDown },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-white/5 bg-black/40 backdrop-blur-xl">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-purple-600">
          <Eye className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-white">
            RentWatch
          </h1>
          <p className="text-[10px] font-medium uppercase tracking-widest text-white/40">
            Price Monitor
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="mt-6 flex-1 space-y-1 px-3">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-brand-600/20 text-brand-400"
                  : "text-white/50 hover:bg-white/5 hover:text-white/80"
              )}
            >
              <item.icon
                className={clsx("h-4.5 w-4.5", isActive ? "text-brand-400" : "text-white/30")}
              />
              {item.label}
              {isActive && (
                <span className="ml-auto h-1.5 w-1.5 rounded-full bg-brand-400" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-white/5 p-4">
        <p className="text-center text-[10px] text-white/20">
          SUUMO & HOME&apos;S Tracker
        </p>
      </div>
    </aside>
  );
}
