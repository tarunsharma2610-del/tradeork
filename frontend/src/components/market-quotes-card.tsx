"use client";

import { RefreshCw, TrendingDown, TrendingUp } from "lucide-react";
import * as React from "react";

import { InstrumentSearch } from "@/components/instrument-search";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { Quote } from "@/lib/api";
import { useMarketStream } from "@/lib/use-market-stream";
import { cn } from "@/lib/utils";

interface MarketQuotesCardProps {
  token: string | null;
  /** Reports the current feed/mode so parent cards can reflect reality. */
  onFeedInfo?: (info: { mode: string; isMock: boolean | null; source: string | null }) => void;
}

const inr = new Intl.NumberFormat("en-IN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const TRAIL_POINTS = 40;

function Sparkline({ points, className }: { points: number[]; className?: string }) {
  if (points.length < 2) return null;
  const width = 64;
  const height = 28;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = max - min || 1;
  const step = (width - 4) / (points.length - 1);
  const coords = points.map((p, i) => {
    const x = 2 + i * step;
    const y = 2 + (height - 4) * (1 - (p - min) / span);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const up = points[points.length - 1] >= points[0];
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className={cn("h-7 w-16", className)}
      aria-hidden
    >
      <polyline
        points={coords.join(" ")}
        fill="none"
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
        className={up ? "stroke-positive" : "stroke-negative"}
      />
    </svg>
  );
}

function streamLabel(mode: string, isMock: boolean | undefined): string {
  if (mode === "idle") return "offline";
  const feed = isMock ? "mock" : "live";
  return mode === "live" ? `${feed} · streaming` : `${feed} · polling`;
}

export function MarketQuotesCard({ token, onFeedInfo }: MarketQuotesCardProps) {
  const [input, setInput] = React.useState("RELIANCE,TCS,NIFTY");
  const [error, setError] = React.useState<string | null>(null);
  const [refreshing, setRefreshing] = React.useState(false);
  const [trail, setTrail] = React.useState<Record<string, number[]>>({});

  const symbols = React.useMemo(
    () =>
      input
        .split(",")
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean),
    [input]
  );

  const onError = React.useCallback((message: string) => {
    setError(message || null);
  }, []);

  const { quotes, mode, refresh } = useMarketStream({
    symbols,
    exchange: "NSE",
    token,
    onError,
  });

  // Maintain a rolling price trail per symbol for the sparklines.
  React.useEffect(() => {
    if (quotes.length === 0) return;
    setTrail((prev) => {
      const next = { ...prev };
      for (const q of quotes) {
        const series = [...(next[q.symbol] ?? []), Number(q.last_price)];
        next[q.symbol] = series.slice(-TRAIL_POINTS);
      }
      return next;
    });
  }, [quotes]);

  const isMock = quotes[0]?.is_mock ?? null;

  React.useEffect(() => {
    onFeedInfo?.({ mode, isMock, source: quotes[0]?.source ?? null });
  }, [onFeedInfo, mode, isMock, quotes]);

  const handleRefresh = React.useCallback(async () => {
    if (!token || symbols.length === 0) {
      setError("Enter at least one symbol.");
      return;
    }
    setRefreshing(true);
    try {
      await refresh();
    } finally {
      setRefreshing(false);
    }
  }, [token, symbols, refresh]);

  React.useEffect(() => {
    if (symbols.length === 0) {
      setError("Enter at least one symbol.");
    } else {
      setError(null);
    }
  }, [symbols]);

  const addSymbol = React.useCallback(
    (symbol: string) => {
      setInput((prev) => {
        const current = prev
          .split(",")
          .map((s) => s.trim().toUpperCase())
          .filter(Boolean);
        if (current.includes(symbol)) return current.join(",");
        return [...current, symbol].join(",");
      });
    },
    []
  );

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div className="space-y-1.5">
          <CardTitle>Market quotes</CardTitle>
          <CardDescription>
            {isMock === true
              ? "Simulated NSE quotes — clearly marked as mock data"
              : "Live NSE quotes streamed from your configured provider"}
          </CardDescription>
        </div>
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium text-muted-foreground",
            mode === "live" && isMock === false && "border-positive/30 bg-positive/10 text-positive"
          )}
        >
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              mode === "live" ? "animate-pulse bg-positive" : "bg-muted-foreground"
            )}
          />
          {streamLabel(mode, isMock ?? undefined)}
        </span>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input
            placeholder="e.g. RELIANCE,TCS,NIFTY"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleRefresh();
            }}
          />
          <Button
            onClick={handleRefresh}
            disabled={refreshing || !token}
            className="shrink-0"
          >
            <RefreshCw
              className={cn("h-4 w-4", refreshing && "animate-spin")}
            />
            {refreshing ? "Refreshing…" : "Refresh"}
          </Button>
        </div>
        <InstrumentSearch onSelect={addSymbol} className="max-w-sm" />

        {error && <p className="text-sm text-destructive">{error}</p>}

        {quotes.length > 0 && (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                    <th className="pb-2 pr-3 font-medium">Symbol</th>
                    <th className="hidden pb-2 pr-3 font-medium sm:table-cell">Trend</th>
                    <th className="pb-2 pr-3 text-right font-medium">Last</th>
                    <th className="pb-2 pr-3 text-right font-medium">Change</th>
                    <th className="hidden pb-2 pr-3 text-right font-medium md:table-cell">
                      Open
                    </th>
                    <th className="hidden pb-2 pr-3 text-right font-medium md:table-cell">
                      High
                    </th>
                    <th className="hidden pb-2 pr-3 text-right font-medium md:table-cell">
                      Low
                    </th>
                    <th className="hidden pb-2 text-right font-medium sm:table-cell">
                      Prev close
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {quotes.map((q) => {
                    const change = Number(q.last_price) - Number(q.prev_close);
                    const pct =
                      Number(q.prev_close) !== 0
                        ? (change / Number(q.prev_close)) * 100
                        : 0;
                    const up = change >= 0;
                    return (
                      <tr key={q.symbol} className="border-b last:border-0">
                        <td className="py-2.5 pr-3">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{q.symbol}</span>
                            <span
                              className={cn(
                                "rounded-full px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide",
                                q.is_mock
                                  ? "bg-muted text-muted-foreground"
                                  : "bg-positive/10 text-positive"
                              )}
                            >
                              {q.is_mock ? "mock" : "live"}
                            </span>
                          </div>
                        </td>
                        <td className="hidden py-2.5 pr-3 sm:table-cell">
                          <Sparkline points={trail[q.symbol] ?? []} />
                        </td>
                        <td className="py-2.5 pr-3 text-right font-medium tabular-nums">
                          ₹{inr.format(Number(q.last_price))}
                        </td>
                        <td
                          className={cn(
                            "py-2.5 pr-3 text-right font-medium tabular-nums",
                            up ? "text-positive" : "text-negative"
                          )}
                        >
                          <span className="inline-flex items-center gap-1">
                            {up ? (
                              <TrendingUp className="h-3.5 w-3.5" />
                            ) : (
                              <TrendingDown className="h-3.5 w-3.5" />
                            )}
                            {up ? "+" : ""}
                            {inr.format(change)} ({pct.toFixed(2)}%)
                          </span>
                        </td>
                        <td className="hidden py-2.5 pr-3 text-right tabular-nums text-muted-foreground md:table-cell">
                          {inr.format(Number(q.open))}
                        </td>
                        <td className="hidden py-2.5 pr-3 text-right tabular-nums text-muted-foreground md:table-cell">
                          {inr.format(Number(q.high))}
                        </td>
                        <td className="hidden py-2.5 pr-3 text-right tabular-nums text-muted-foreground md:table-cell">
                          {inr.format(Number(q.low))}
                        </td>
                        <td className="hidden py-2.5 text-right tabular-nums text-muted-foreground sm:table-cell">
                          {inr.format(Number(q.prev_close))}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-muted-foreground">
              Source: {quotes[0].source} · updated{" "}
              {new Date(quotes[0].quote_time).toLocaleTimeString()}
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
