"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { PriceRecord } from "@/lib/api";
import { formatPrice, formatDate } from "@/lib/format";

interface PriceChartProps {
  records: PriceRecord[];
  height?: number;
}

export default function PriceChart({ records, height = 250 }: PriceChartProps) {
  const data = records.map((r) => ({
    date: formatDate(r.recorded_at),
    price: r.price,
    timestamp: new Date(r.recorded_at).getTime(),
  }));

  data.sort((a, b) => a.timestamp - b.timestamp);

  if (data.length < 2) {
    return (
      <div
        className="flex items-center justify-center text-sm text-white/30"
        style={{ height }}
      >
        データが2件以上で グラフを表示
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis
          dataKey="date"
          stroke="rgba(255,255,255,0.2)"
          tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
        />
        <YAxis
          stroke="rgba(255,255,255,0.2)"
          tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }}
          tickFormatter={(v) => formatPrice(v)}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#1a1a2e",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "12px",
            boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
          }}
          labelStyle={{ color: "rgba(255,255,255,0.6)" }}
          formatter={(value) => [formatPrice(value as number), "賃料"]}
        />
        <Line
          type="monotone"
          dataKey="price"
          stroke="#5c7cfa"
          strokeWidth={2.5}
          dot={{ fill: "#5c7cfa", strokeWidth: 0, r: 4 }}
          activeDot={{ r: 6, fill: "#748ffc", strokeWidth: 0 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
