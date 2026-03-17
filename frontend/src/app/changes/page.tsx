"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import {
  RefreshCw,
  ArrowDownRight,
  ArrowUpRight,
  ExternalLink,
  TrendingDown,
} from "lucide-react";
import { api, PriceChange } from "@/lib/api";
import { formatPrice, formatPriceChange, formatDateTime } from "@/lib/format";

export default function ChangesPage() {
  const [changes, setChanges] = useState<PriceChange[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getPriceChanges(100)
      .then(setChanges)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const drops = changes.filter((c) => c.change < 0);
  const increases = changes.filter((c) => c.change > 0);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-64 flex-1 p-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight">価格変動</h1>
          <p className="mt-1 text-sm text-white/40">
            すべての監視物件の価格変動を一覧で確認
          </p>
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-brand-500" />
          </div>
        ) : changes.length === 0 ? (
          <div className="glass-card flex h-64 flex-col items-center justify-center">
            <TrendingDown className="mb-4 h-12 w-12 text-white/10" />
            <p className="text-lg font-medium text-white/40">
              まだ価格変動はありません
            </p>
          </div>
        ) : (
          <div className="grid gap-6 xl:grid-cols-2">
            {/* Price Drops */}
            <div className="glass-card overflow-hidden">
              <div className="flex items-center gap-3 border-b border-white/5 px-6 py-4">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-green-500/10">
                  <ArrowDownRight className="h-4 w-4 text-green-400" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-green-400">
                    値下げ
                  </h2>
                  <p className="text-xs text-white/30">{drops.length}件</p>
                </div>
              </div>
              <div className="divide-y divide-white/5">
                {drops.length === 0 ? (
                  <div className="flex h-24 items-center justify-center text-sm text-white/20">
                    値下げ物件はありません
                  </div>
                ) : (
                  drops.map((c, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-4 px-6 py-3 hover:bg-white/[0.02]"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">
                          {c.property_name}
                        </p>
                        <p className="text-xs text-white/20">
                          {formatDateTime(c.changed_at)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-white/30 line-through">
                          {formatPrice(c.old_price)}
                        </p>
                        <p className="text-sm font-semibold text-green-400">
                          {formatPrice(c.new_price)}
                        </p>
                      </div>
                      <span className="badge-success font-bold">
                        {formatPriceChange(c.change)}
                      </span>
                      {c.detail_url && (
                        <a
                          href={c.detail_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-white/20 hover:text-brand-400"
                        >
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Price Increases */}
            <div className="glass-card overflow-hidden">
              <div className="flex items-center gap-3 border-b border-white/5 px-6 py-4">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-500/10">
                  <ArrowUpRight className="h-4 w-4 text-red-400" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-red-400">値上げ</h2>
                  <p className="text-xs text-white/30">{increases.length}件</p>
                </div>
              </div>
              <div className="divide-y divide-white/5">
                {increases.length === 0 ? (
                  <div className="flex h-24 items-center justify-center text-sm text-white/20">
                    値上げ物件はありません
                  </div>
                ) : (
                  increases.map((c, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-4 px-6 py-3 hover:bg-white/[0.02]"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">
                          {c.property_name}
                        </p>
                        <p className="text-xs text-white/20">
                          {formatDateTime(c.changed_at)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-white/30 line-through">
                          {formatPrice(c.old_price)}
                        </p>
                        <p className="text-sm font-semibold text-red-400">
                          {formatPrice(c.new_price)}
                        </p>
                      </div>
                      <span className="badge-danger font-bold">
                        {formatPriceChange(c.change)}
                      </span>
                      {c.detail_url && (
                        <a
                          href={c.detail_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-white/20 hover:text-brand-400"
                        >
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
