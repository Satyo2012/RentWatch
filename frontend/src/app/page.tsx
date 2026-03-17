"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import StatsCard from "@/components/StatsCard";
import {
  Eye,
  Building2,
  TrendingDown,
  TrendingUp,
  Clock,
  RefreshCw,
  ArrowDownRight,
  ArrowUpRight,
  ExternalLink,
} from "lucide-react";
import { api, DashboardStats, PriceChange } from "@/lib/api";
import { formatPrice, formatPriceChange, formatDateTime } from "@/lib/format";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [changes, setChanges] = useState<PriceChange[]>([]);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);

  const fetchData = async () => {
    try {
      const [s, c] = await Promise.all([
        api.getDashboard(),
        api.getPriceChanges(20),
      ]);
      setStats(s);
      setChanges(c);
    } catch (e) {
      console.error("Failed to fetch dashboard:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleScrapeAll = async () => {
    setScraping(true);
    try {
      await api.scrapeAll();
      await fetchData();
    } catch (e) {
      console.error("Scrape failed:", e);
    } finally {
      setScraping(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-64 flex-1 p-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">ダッシュボード</h1>
            <p className="mt-1 text-sm text-white/40">
              賃貸価格の変動をリアルタイムで監視
            </p>
          </div>
          <button
            onClick={handleScrapeAll}
            disabled={scraping}
            className="btn-primary"
          >
            <RefreshCw className={`h-4 w-4 ${scraping ? "animate-spin" : ""}`} />
            {scraping ? "スキャン中..." : "今すぐスキャン"}
          </button>
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-brand-500" />
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="mb-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
              <StatsCard
                label="アクティブモニター"
                value={stats?.active_monitors ?? 0}
                icon={<Eye className="h-4 w-4 text-brand-400" />}
                glowColor="blue"
              />
              <StatsCard
                label="監視物件数"
                value={stats?.total_properties ?? 0}
                icon={<Building2 className="h-4 w-4 text-brand-400" />}
                glowColor="blue"
              />
              <StatsCard
                label="値下げ物件"
                value={stats?.price_drops ?? 0}
                icon={<TrendingDown className="h-4 w-4 text-green-400" />}
                glowColor="green"
                trend="down"
                subtitle="チャンス!"
              />
              <StatsCard
                label="値上げ物件"
                value={stats?.price_increases ?? 0}
                icon={<TrendingUp className="h-4 w-4 text-red-400" />}
                glowColor="red"
                trend="up"
              />
            </div>

            {/* Last scan info */}
            {stats?.last_scan && (
              <div className="mb-8 flex items-center gap-2 text-sm text-white/30">
                <Clock className="h-3.5 w-3.5" />
                最終スキャン: {formatDateTime(stats.last_scan)}
              </div>
            )}

            {/* Price Changes Feed */}
            <div className="glass-card overflow-hidden">
              <div className="border-b border-white/5 px-6 py-4">
                <h2 className="text-lg font-semibold">最近の価格変動</h2>
              </div>

              {changes.length === 0 ? (
                <div className="flex h-48 flex-col items-center justify-center text-white/30">
                  <TrendingDown className="mb-3 h-10 w-10" />
                  <p className="text-sm">まだ価格変動はありません</p>
                  <p className="mt-1 text-xs">
                    モニターを追加してスキャンを実行してください
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-white/5">
                  {changes.map((c, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-4 px-6 py-4 transition-colors hover:bg-white/[0.02]"
                    >
                      <div
                        className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                          c.change < 0
                            ? "bg-green-500/10"
                            : "bg-red-500/10"
                        }`}
                      >
                        {c.change < 0 ? (
                          <ArrowDownRight className="h-5 w-5 text-green-400" />
                        ) : (
                          <ArrowUpRight className="h-5 w-5 text-red-400" />
                        )}
                      </div>

                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">
                          {c.property_name}
                        </p>
                        <p className="text-xs text-white/30">
                          {formatDateTime(c.changed_at)}
                        </p>
                      </div>

                      <div className="text-right">
                        <p className="text-sm text-white/40 line-through">
                          {formatPrice(c.old_price)}
                        </p>
                        <p className="text-sm font-semibold">
                          {formatPrice(c.new_price)}
                        </p>
                      </div>

                      <span
                        className={`rounded-full px-3 py-1 text-xs font-bold ${
                          c.change < 0
                            ? "bg-green-500/10 text-green-400"
                            : "bg-red-500/10 text-red-400"
                        }`}
                      >
                        {formatPriceChange(c.change)}
                      </span>

                      {c.detail_url && (
                        <a
                          href={c.detail_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-white/20 hover:text-brand-400"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
