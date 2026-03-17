"use client";

import { ReactNode } from "react";
import clsx from "clsx";

interface StatsCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  trend?: "up" | "down" | "neutral";
  subtitle?: string;
  glowColor?: string;
}

export default function StatsCard({
  label,
  value,
  icon,
  trend,
  subtitle,
  glowColor = "blue",
}: StatsCardProps) {
  return (
    <div
      className={clsx(
        "glass-card relative overflow-hidden p-6",
        glowColor === "green" && "glow-green",
        glowColor === "red" && "glow-red",
        glowColor === "blue" && "glow-blue"
      )}
    >
      {/* Background glow */}
      <div
        className={clsx(
          "absolute -right-4 -top-4 h-24 w-24 rounded-full opacity-10 blur-2xl",
          glowColor === "green" && "bg-green-500",
          glowColor === "red" && "bg-red-500",
          glowColor === "blue" && "bg-brand-500"
        )}
      />

      <div className="relative">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-white/40">{label}</p>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/5">
            {icon}
          </div>
        </div>
        <p className="mt-3 text-3xl font-bold tracking-tight">{value}</p>
        {subtitle && (
          <p
            className={clsx(
              "mt-1 text-sm font-medium",
              trend === "down" && "text-green-400",
              trend === "up" && "text-red-400",
              trend === "neutral" && "text-white/40"
            )}
          >
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
}
