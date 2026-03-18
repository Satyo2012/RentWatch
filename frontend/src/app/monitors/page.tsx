"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import AddMonitorModal from "@/components/AddMonitorModal";
import {
  Plus,
  RefreshCw,
  Trash2,
  Play,
  Pause,
  Eye,
  ExternalLink,
  Search,
  LinkIcon,
} from "lucide-react";
import { api, Monitor } from "@/lib/api";
import { siteName, siteColor, formatDateTime } from "@/lib/format";

export default function MonitorsPage() {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [scrapingId, setScrapingId] = useState<number | null>(null);

  const fetchMonitors = async () => {
    try {
      const data = await api.getMonitors();
      setMonitors(data);
    } catch (e) {
      console.error("Failed to fetch monitors:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitors();
  }, []);

  const handleCreate = async (data: {
    name: string;
    site: string;
    monitor_type: string;
    url: string;
  }) => {
    try {
      await api.createMonitor(data);
      await fetchMonitors();
    } catch (e) {
      console.error("Failed to create monitor:", e);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("このモニターを削除しますか?")) return;
    try {
      await api.deleteMonitor(id);
      await fetchMonitors();
    } catch (e) {
      console.error("Failed to delete monitor:", e);
    }
  };

  const handleToggle = async (monitor: Monitor) => {
    try {
      await api.updateMonitor(monitor.id, { is_active: !monitor.is_active });
      await fetchMonitors();
    } catch (e) {
      console.error("Failed to toggle monitor:", e);
    }
  };

  const handleScrape = async (id: number) => {
    setScrapingId(id);
    try {
      const result = await api.scrapeMonitor(id);
      alert(
        `スキャン完了!\n物件数: ${result.properties_found}\n新規: ${result.new_properties}\n価格変動: ${result.price_changes}`
      );
      await fetchMonitors();
    } catch (e) {
      console.error("Failed to scrape:", e);
      alert("スキャンに失敗しました");
    } finally {
      setScrapingId(null);
    }
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-64 flex-1 p-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">モニター</h1>
            <p className="mt-1 text-sm text-white/40">
              監視対象のURLや検索条件を管理
            </p>
          </div>
          <button
            onClick={() => setModalOpen(true)}
            className="btn-primary"
          >
            <Plus className="h-4 w-4" />
            モニターを追加
          </button>
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-brand-500" />
          </div>
        ) : monitors.length === 0 ? (
          <div className="glass-card flex h-64 flex-col items-center justify-center">
            <Eye className="mb-4 h-12 w-12 text-white/10" />
            <p className="text-lg font-medium text-white/40">
              モニターがありません
            </p>
            <p className="mt-1 text-sm text-white/20">
              「モニターを追加」をクリックして始めましょう
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
            {monitors.map((m) => (
              <div
                key={m.id}
                className="glass-card-hover flex items-center gap-6 p-6"
              >
                {/* Site badge */}
                <div
                  className="flex h-12 w-12 items-center justify-center rounded-xl"
                  style={{
                    backgroundColor: `${siteColor(m.site)}15`,
                  }}
                >
                  <span
                    className="text-sm font-bold"
                    style={{ color: siteColor(m.site) }}
                  >
                    {m.site === "suumo" ? "S" : "H"}
                  </span>
                </div>

                {/* Info */}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-3">
                    <Link
                      href={`/monitors/${m.id}`}
                      className="text-base font-semibold hover:text-brand-400 transition-colors"
                    >
                      {m.name}
                    </Link>
                    <span
                      className="badge"
                      style={{
                        backgroundColor: `${siteColor(m.site)}15`,
                        color: siteColor(m.site),
                      }}
                    >
                      {siteName(m.site)}
                    </span>
                    <span className="badge-info">
                      {m.monitor_type === "search" ? (
                        <><Search className="mr-1 h-3 w-3" /> 検索</>
                      ) : (
                        <><LinkIcon className="mr-1 h-3 w-3" /> URL</>
                      )}
                    </span>
                    {!m.is_active && (
                      <span className="badge-warning">一時停止中</span>
                    )}
                  </div>
                  {/* Condition Tags */}
                  {m.tags && m.tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {m.tags.map((tag, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center rounded-lg bg-brand-600/10 px-2.5 py-0.5 text-xs font-medium text-brand-300 border border-brand-500/20"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="mt-2 flex items-center gap-4 text-xs text-white/20">
                    <span>{m.property_count} 物件</span>
                    <span>作成: {formatDateTime(m.created_at)}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleScrape(m.id)}
                    disabled={scrapingId === m.id}
                    className="btn-secondary !px-3 !py-2"
                    title="今すぐスキャン"
                  >
                    <RefreshCw
                      className={`h-4 w-4 ${
                        scrapingId === m.id ? "animate-spin" : ""
                      }`}
                    />
                  </button>
                  <button
                    onClick={() => handleToggle(m)}
                    className="btn-secondary !px-3 !py-2"
                    title={m.is_active ? "一時停止" : "再開"}
                  >
                    {m.is_active ? (
                      <Pause className="h-4 w-4" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                  </button>
                  <a
                    href={m.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary !px-3 !py-2"
                    title="URLを開く"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                  <button
                    onClick={() => handleDelete(m.id)}
                    className="btn-secondary !px-3 !py-2 hover:!border-red-500/30 hover:!bg-red-500/10 hover:!text-red-400"
                    title="削除"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <AddMonitorModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          onSubmit={handleCreate}
        />
      </main>
    </div>
  );
}
