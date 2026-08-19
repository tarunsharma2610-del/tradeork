"use client";

import { Wallet, BarChart3 } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface StatItem {
  label: string;
  value: string;
  hint?: string;
  icon: typeof Wallet;
  accent?: "default" | "positive" | "negative";
}

const iconStyles: Record<NonNullable<StatItem["accent"]>, string> = {
  default: "bg-primary/10 text-primary",
  positive: "bg-positive/10 text-positive",
  negative: "bg-negative/10 text-negative",
};

export function StatCard({ item }: { item: StatItem }) {
  const Icon = item.icon;
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{item.label}</p>
            <p className="text-2xl font-bold tracking-tight tabular-nums">
              {item.value}
            </p>
            {item.hint && (
              <p className="text-xs text-muted-foreground">{item.hint}</p>
            )}
          </div>
          <span
            className={cn(
              "inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
              iconStyles[item.accent ?? "default"]
            )}
          >
            <Icon className="h-4 w-4" strokeWidth={2} />
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

export function StatGrid({
  items,
  className,
}: {
  items: StatItem[];
  className?: string;
}) {
  return (
    <div
      className={cn(
        "grid gap-4 sm:grid-cols-2 lg:grid-cols-4",
        className
      )}
    >
      {items.map((item) => (
        <StatCard key={item.label} item={item} />
      ))}
    </div>
  );
}

export const statIcons = { Wallet, BarChart3 };
