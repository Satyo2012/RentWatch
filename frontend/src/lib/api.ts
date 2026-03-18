const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface Monitor {
  id: number;
  name: string;
  site: "suumo" | "homes";
  monitor_type: "url" | "search";
  url: string;
  tags: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  property_count: number;
}

export interface PriceRecord {
  id: number;
  price: number;
  management_fee: number | null;
  deposit: string | null;
  key_money: string | null;
  recorded_at: string;
}

export interface Property {
  id: number;
  monitor_id: number;
  external_id: string | null;
  name: string;
  address: string | null;
  layout: string | null;
  area: string | null;
  floor: string | null;
  age: string | null;
  access: string | null;
  detail_url: string | null;
  is_listed: boolean;
  last_seen: string;
  first_seen: string;
  price_records: PriceRecord[];
  current_price: number | null;
  price_change: number | null;
}

export interface DashboardStats {
  total_monitors: number;
  active_monitors: number;
  total_properties: number;
  total_listed: number;
  delisted: number;
  price_drops: number;
  price_increases: number;
  last_scan: string | null;
}

export interface PriceChange {
  property_id: number;
  property_name: string;
  monitor_id: number;
  old_price: number;
  new_price: number;
  change: number;
  changed_at: string;
  detail_url: string | null;
}

export interface ScrapeResult {
  monitor_id: number;
  properties_found: number;
  new_properties: number;
  price_changes: number;
  delisted: number;
}

export interface PropertyFilters {
  sort?: string;
  layout?: string;
  price_min?: number;
  price_max?: number;
  status?: string;
}

export const api = {
  getDashboard: () => fetchAPI<DashboardStats>("/dashboard"),
  getMonitors: () => fetchAPI<Monitor[]>("/monitors"),
  createMonitor: (data: { name: string; site: string; monitor_type: string; url: string }) =>
    fetchAPI<Monitor>("/monitors", { method: "POST", body: JSON.stringify(data) }),
  updateMonitor: (id: number, data: { name?: string; is_active?: boolean }) =>
    fetchAPI<Monitor>(`/monitors/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteMonitor: (id: number) =>
    fetchAPI<{ ok: boolean }>(`/monitors/${id}`, { method: "DELETE" }),
  scrapeMonitor: (id: number) =>
    fetchAPI<ScrapeResult>(`/monitors/${id}/scrape`, { method: "POST" }),
  scrapeAll: () => fetchAPI<{ results: ScrapeResult[] }>("/scrape-all", { method: "POST" }),
  getProperties: (monitorId: number, filters?: PropertyFilters) => {
    const params = new URLSearchParams();
    if (filters?.sort) params.set("sort", filters.sort);
    if (filters?.layout) params.set("layout", filters.layout);
    if (filters?.price_min) params.set("price_min", String(filters.price_min));
    if (filters?.price_max) params.set("price_max", String(filters.price_max));
    if (filters?.status) params.set("status", filters.status);
    const qs = params.toString();
    return fetchAPI<Property[]>(`/monitors/${monitorId}/properties${qs ? `?${qs}` : ""}`);
  },
  getPriceHistory: (propertyId: number) =>
    fetchAPI<PriceRecord[]>(`/properties/${propertyId}/history`),
  getPriceChanges: (limit?: number) =>
    fetchAPI<PriceChange[]>(`/price-changes?limit=${limit || 50}`),
};
