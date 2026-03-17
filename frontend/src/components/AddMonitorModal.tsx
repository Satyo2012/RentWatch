"use client";

import { useState } from "react";
import { X } from "lucide-react";

interface AddMonitorModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: {
    name: string;
    site: string;
    monitor_type: string;
    url: string;
  }) => void;
}

export default function AddMonitorModal({
  open,
  onClose,
  onSubmit,
}: AddMonitorModalProps) {
  const [name, setName] = useState("");
  const [site, setSite] = useState("suumo");
  const [monitorType, setMonitorType] = useState("search");
  const [url, setUrl] = useState("");

  if (!open) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ name, site, monitor_type: monitorType, url });
    setName("");
    setUrl("");
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="glass-card w-full max-w-lg p-8">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-bold">モニターを追加</h2>
          <button onClick={onClose} className="text-white/40 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-white/60">
              モニター名
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例: 渋谷区 1LDK 10万以下"
              className="input-field"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-white/60">
                サイト
              </label>
              <select
                value={site}
                onChange={(e) => setSite(e.target.value)}
                className="input-field"
              >
                <option value="suumo">SUUMO</option>
                <option value="homes">HOME&apos;S</option>
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-white/60">
                タイプ
              </label>
              <select
                value={monitorType}
                onChange={(e) => setMonitorType(e.target.value)}
                className="input-field"
              >
                <option value="search">検索条件</option>
                <option value="url">物件URL</option>
              </select>
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-white/60">
              URL
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder={
                monitorType === "search"
                  ? "検索結果ページのURLを貼り付け"
                  : "物件詳細ページのURLを貼り付け"
              }
              className="input-field"
              required
            />
            <p className="mt-1.5 text-xs text-white/30">
              {monitorType === "search"
                ? "SUUMOやHOME'Sで条件を設定し、検索結果ページのURLをコピーしてください"
                : "監視したい物件の詳細ページURLをコピーしてください"}
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">
              キャンセル
            </button>
            <button type="submit" className="btn-primary">
              追加
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
