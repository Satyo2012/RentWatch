"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import PriceChart from "@/components/PriceChart";
import {
  ArrowLeft,
  RefreshCw,
  ExternalLink,
  TrendingDown,
  TrendingUp,
  Minus,
  Building2,
} from "lucide-react";
import { api, Property, Monitor } from "@/lib/api";
import {
  formatPrice,
  formatPriceChange,
  formatDateTime,
  siteName,
  siteColor,
} from "@/lib/format";

export default function MonitorDetailPage() {
  const params = useParams();
  const monitorId = Number(params.id);
  const [monitor, setMonitor] = useState<Monitor | null>(null);
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);

  const fetchData = async () => {
    try {
      const [monitors, props] = await Promise.all([
        api.getMonitors(),
        api.getProperties(monitorId),
      ]);
      const m = monitors.find((m) => m.id === monitorId) || null;
      setMonitor(m);
      setProperties(props);
      if (props.length > 0 && !selectedProperty) {
        setSelectedProperty(props[0]);
      }
    } catch (e) {
      console.error("Failed to fetch data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [monitorId]);

  const handleScrape = async () => {
    setScraping(true);
    try {
      await api.scrapeMonitor(monitorId);
      await fetchData();
    } catch (e) {
      console.error("Scrape failed:", e);
    } finally {
      setScraping(false);
    }
  };

  const sortedProperties = [...properties].sort((a, b) => {
    if (a.price_change && b.price_change) {
      return a.price_change - b.price_change; // Price drops first
    }
    if (a.price_change) return -1;
    if (b.price_change) return 1;
    return (a.current_price ?? 0) - (b.current_price ?? 0);
  });

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-64 flex-1 p-8">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/monitors"
            className="mb-4 inline-flex items-center gap-2 text-sm text-white/40 hover:text-white/60 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            モニター一覧
          </Link>

          {monitor && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h1 className="text-2xl font-bold tracking-tight">
                  {monitor.name}
                </h1>
                <span
                  className="badge"
                  style={{
                    backgroundColor: `${siteColor(monitor.site)}15`,
                    color: siteColor(monitor.site),
                  }}
                >
                  {siteName(monitor.site)}
                </span>
              </div>
              <button
                onClick={handleScrape}
                disabled={scraping}
                className="btn-primary"
              >
                <RefreshCw
                  className={`h-4 w-4 ${scraping ? "animate-spin" : ""}`}
                />
                {scraping ? "スキャン中..." : "今すぐスキャン"}
              </button>
            </div>
          )}
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-brand-500" />
          </div>
        ) : properties.length === 0 ? (
          <div className="glass-card flex h-64 flex-col items-center justify-center">
            <Building2 className="mb-4 h-12 w-12 text-white/10" />
            <p className="text-lg font-medium text-white/40">物件がありません</p>
            <p className="mt-1 text-sm text-white/20">
              「今すぐスキャン」でデータを取得してください
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            {/* Property List */}
            <div className="xl:col-span-2">
              <div className="glass-card overflow-hidden">
                <div className="border-b border-white/5 px-6 py-4">
                  <h2 className="text-lg font-semibold">
                    物件一覧
                    <span className="ml-2 text-sm font-normal text-white/30">
                      ({properties.length}件)
                    </span>
                  </h2>
                </div>
                <div className="divide-y divide-white/5">
                  {sortedProperties.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => setSelectedProperty(p)}
                      className={`w-full px-6 py-4 text-left transition-colors hover:bg-white/[0.02] ${
                        selectedProperty?.id === p.id
                          ? "bg-brand-600/5 border-l-2 border-brand-500"
                          : ""
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="truncate text-sm font-medium">
                              {p.name}
                            </p>
                            {p.price_change !== null && p.price_change !== 0 && (
                              <span
                                className={`badge ${
                                  p.price_change < 0
                                    ? "badge-success"
                                    : "badge-danger"
                                }`}
                              >
                                {p.price_change < 0 ? (
                                  <TrendingDown className="mr-1 h-3 w-3" />
                                ) : (
                                  <TrendingUp className="mr-1 h-3 w-3" />
                                )}
                                {formatPriceChange(p.price_change)}
                              </span>
                            )}
                          </div>
                          <div className="mt-1 flex items-center gap-3 text-xs text-white/30">
                            {p.layout && <span>{p.layout}</span>}
                            {p.area && <span>{p.area}</span>}
                            {p.floor && <span>{p.floor}</span>}
                            {p.address && (
                              <span className="truncate">{p.address}</span>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-brand-400">
                            {p.current_price
                              ? formatPrice(p.current_price)
                              : "-"}
                          </p>
                          {p.price_records[0]?.management_fee && (
                            <p className="text-xs text-white/30">
                              管理費{" "}
                              {formatPrice(p.price_records[0].management_fee)}
                            </p>
                          )}
                        </div>
                        {p.detail_url && (
                          <a
                            href={p.detail_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-white/20 hover:text-brand-400"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Detail Panel */}
            <div className="xl:col-span-1">
              {selectedProperty ? (
                <div className="glass-card sticky top-8 p-6">
                  <h3 className="mb-4 text-lg font-semibold">
                    {selectedProperty.name}
                  </h3>

                  <div className="mb-6 space-y-3">
                    {selectedProperty.address && (
                      <div className="flex justify-between text-sm">
                        <span className="text-white/40">住所</span>
                        <span className="text-right text-white/80">
                          {selectedProperty.address}
                        </span>
                      </div>
                    )}
                    {selectedProperty.layout && (
                      <div className="flex justify-between text-sm">
                        <span className="text-white/40">間取り</span>
                        <span className="text-white/80">
                          {selectedProperty.layout}
                        </span>
                      </div>
                    )}
                    {selectedProperty.area && (
                      <div className="flex justify-between text-sm">
                        <span className="text-white/40">面積</span>
                        <span className="text-white/80">
                          {selectedProperty.area}
                        </span>
                      </div>
                    )}
                    {selectedProperty.age && (
                      <div className="flex justify-between text-sm">
                        <span className="text-white/40">築年数</span>
                        <span className="text-white/80">
                          {selectedProperty.age}
                        </span>
                      </div>
                    )}
                    {selectedProperty.access && (
                      <div className="flex justify-between text-sm">
                        <span className="text-white/40">アクセス</span>
                        <span className="text-right text-xs text-white/80">
                          {selectedProperty.access}
                        </span>
                      </div>
                    )}
                    {selectedProperty.price_records[0]?.deposit && (
                      <div className="flex justify-between text-sm">
                        <span className="text-white/40">敷金</span>
                        <span className="text-white/80">
                          {selectedProperty.price_records[0].deposit}
                        </span>
                      </div>
                    )}
                    {selectedProperty.price_records[0]?.key_money && (
                      <div className="flex justify-between text-sm">
                        <span className="text-white/40">礼金</span>
                        <span className="text-white/80">
                          {selectedProperty.price_records[0].key_money}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Price History Chart */}
                  <div className="border-t border-white/5 pt-4">
                    <h4 className="mb-3 text-sm font-medium text-white/50">
                      価格推移
                    </h4>
                    <PriceChart
                      records={selectedProperty.price_records}
                      height={200}
                    />
                  </div>

                  {/* Price History Table */}
                  <div className="mt-4 border-t border-white/5 pt-4">
                    <h4 className="mb-3 text-sm font-medium text-white/50">
                      価格履歴
                    </h4>
                    <div className="space-y-2">
                      {selectedProperty.price_records.map((r, i) => {
                        const prev = selectedProperty.price_records[i + 1];
                        const diff = prev ? r.price - prev.price : 0;
                        return (
                          <div
                            key={r.id}
                            className="flex items-center justify-between text-sm"
                          >
                            <span className="text-white/30">
                              {formatDateTime(r.recorded_at)}
                            </span>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">
                                {formatPrice(r.price)}
                              </span>
                              {diff !== 0 && (
                                <span
                                  className={`text-xs font-medium ${
                                    diff < 0
                                      ? "text-green-400"
                                      : "text-red-400"
                                  }`}
                                >
                                  {formatPriceChange(diff)}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="glass-card flex h-48 items-center justify-center text-sm text-white/30">
                  物件を選択して詳細を表示
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
