export function formatPrice(yen: number): string {
  if (yen >= 10000) {
    const man = yen / 10000;
    return `${man % 1 === 0 ? man.toFixed(0) : man.toFixed(1)}万円`;
  }
  return `${yen.toLocaleString()}円`;
}

export function formatPriceChange(change: number): string {
  const prefix = change > 0 ? "+" : "";
  return `${prefix}${formatPrice(change)}`;
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("ja-JP", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function siteName(site: string): string {
  switch (site) {
    case "suumo": return "SUUMO";
    case "homes": return "HOME'S";
    default: return site;
  }
}

export function siteColor(site: string): string {
  switch (site) {
    case "suumo": return "#4ade80";
    case "homes": return "#f97316";
    default: return "#8888a8";
  }
}
