"use client";

import { useEffect, useState, useCallback } from "react";
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
  Building2,
  EyeOff,
  SlidersHorizontal,
  ArrowUpDown,
} from "lucide-react";
import { api, Property, Monitor, PropertyFilters } from "@/lib/api";
import {
  formatPrice,
  formatPriceChange,
  formatDateTime,
  siteName,
  siteColor,
} from "@/lib/format";

const SORT_OPTIONS = [
  { value: "price_asc", label: "賃料（安い順）" },
  { value: "price_desc", label: "賃料（高い順）" },
  { value: "change_asc", label: "値下げ順" },
  { value: "change_desc", label: "値上げ順" },
  { value: "newest", label: "新着順" },
];

const STATUS_OPTIONS = [
  { value: "", label: "すべて" },
  { value: "listed", label: "掲載中" },
  { value: "delisted", label: "掲載終了" },
];

export default function MonitorDetailPage() {
  const params = useParams();
  const monitorId = Number(params.id);
  const [monitor, setMonitor] = useState<Monitor | null>(null);
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Filters
  const [sort, setSort] = useState("price_asc");
  const [statusFilter, setStatusFilter] = useState("");
  const [layoutFilter, setLayoutFilter] = useState("");
  const [priceMin, setPriceMin] = useState("");
  const [priceMax, setPriceMax] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const filters: PropertyFilters = { sort };
      if (statusFilter) filters.status = statusFilter;
      if (layoutFilter) filters.layout = layoutFilter;
      if (priceMin) filters.price_min = parseInt(priceMin) * 10000;
      if (priceMax) filters.price_max = parseInt(priceMax) * 10000;

      const [monitors, props] = await Promise.all([
        api.getMonitors(),
        api.getProperties(monitorId, filters),
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
  }, [monitorId, sort, statusFilter, layoutFilter, priceMin, priceMax]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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

  const listedCount = properties.filter((p) => p.is_listed).length;
  const delistedCount = properties.filter((p) => !p.is_listed).length;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-64 flex-1 p-8">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/monitors"
            className="mb-4 inline-flex items-center gap-2 text-sm text-white/40 hover:text-white/60 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            モニター一覧
          </Link>

          {monitor && (
            <>
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

              {/* Tags */}
              {monitor.tags && monitor.tags.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {monitor.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center rounded-lg bg-brand-600/10 px-2.5 py-0.5 text-xs font-medium text-brand-300 border border-brand-500/20"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-brand-500" />
          </div>
        ) : properties.length === 0 && !statusFilter && !layoutFilter && !priceMin && !priceMax ? (
          <div className="glass-card flex h-64 flex-col items-center justify-center">
            <Building2 className="mb-4 h-12 w-12 text-white/10" />
            <p className="text-lg font-medium text-white/40">物件がありません</p>
            <p className="mt-1 text-sm text-white/20">
              「今すぐスキャン」でデータを取得してください
            </p>
          </div>
        ) : (
          <>
            {/* Filter Bar */}
            <div className="mb-6 glass-card p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-white/40">
                      {properties.length}件表示
                    </span>
                    <span className="badge-success">掲載中 {listedCount}</span>
                    {delistedCount > 0 && (
                      <span className="badge-warning">掲載終了 {delistedCount}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {/* Sort */}
                  <div className="flex items-center gap-2">
                    <ArrowUpDown className="h-3.5 w-3.5 text-white/30" />
                    <select
                      value={sort}
                      onChange={(e) => setSort(e.target.value)}
                      className="input-field !w-auto !py-1.5 !text-xs"
                    >
                      {SORT_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>
                          {o.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button
                    onClick={() => setShowFilters(!showFilters)}
                    className={`btn-secondary !px-3 !py-1.5 !text-xs ${showFilters ? "!border-brand-500/30 !text-brand-400" : ""}`}
                  >
                    <SlidersHorizontal className="h-3.5 w-3.5" />
                    フィルタ
                  </button>
                </div>
              </div>

              {/* Expanded Filters */}
              {showFilters && (
                <div className="mt-4 grid grid-cols-4 gap-3 border-t border-white/5 pt-4">
                  <div>
                    <label className="mb-1 block text-xs text-white/40">ステータス</label>
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="input-field !py-1.5 !text-xs"
                    >
                      {STATUS_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>
                          {o.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs text-white/40">間取り</label>
                    <input
                      type="text"
                      value={layoutFilter}
                      onChange={(e) => setLayoutFilter(e.target.value)}
                      placeholder="例: 1LDK"
                      className="input-field !py-1.5 !text-xs"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs text-white/40">賃料下限（万円）</label>
                    <input
                      type="number"
                      value={priceMin}
                      onChange={(e) => setPriceMin(e.target.value)}
                      placeholder="5"
                      className="input-field !py-1.5 !text-xs"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs text-white/40">賃料上限（万円）</label>
                    <input
                      type="number"
                      value={priceMax}
                      onChange={(e) => setPriceMax(e.target.value)}
                      placeholder="15"
                      className="input-field !py-1.5 !text-xs"
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
              {/* Property List */}
              <div className="xl:col-span-2">
                <div className="glass-card overflow-hidden">
                  <div className="divide-y divide-white/5">
                    {properties.length === 0 ? (
                      <div className="flex h-32 items-center justify-center text-sm text-white/30">
                        条件に一致する物件がありません
                      </div>
                    ) : (
                      properties.map((p) => (
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
                                <p className={`truncate text-sm font-medium ${!p.is_listed ? "text-white/40 line-through" : ""}`}>
                                  {p.name}
                                </p>
                                {!p.is_listed && (
                                  <span className="badge-warning">
                                    <EyeOff className="mr-1 h-3 w-3" />
                                    掲載終了
                                  </span>
                                )}
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
                              <p className={`text-lg font-bold ${p.is_listed ? "text-brand-400" : "text-white/30"}`}>
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
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* Detail Panel */}
              <div className="xl:col-span-1">
                {selectedProperty ? (
                  <div className="glass-card sticky top-8 p-6">
                    <div className="mb-4 flex items-center justify-between">
                      <h3 className="text-lg font-semibold">
                        {selectedProperty.name}
                      </h3>
                      {!selectedProperty.is_listed && (
                        <span className="badge-warning">
                          <EyeOff className="mr-1 h-3 w-3" />
                          掲載終了
                        </span>
                      )}
                    </div>

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
                      <div className="flex justify-between text-sm">
                        <span className="text-white/40">最終確認</span>
                        <span className="text-white/80">
                          {formatDateTime(selectedProperty.last_seen)}
                        </span>
                      </div>
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
          </>
        )}
      </main>
    </div>
  );
}
