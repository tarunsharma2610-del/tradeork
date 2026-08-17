"use client";

import { RefreshCw, TrendingDown, TrendingUp } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, type Quote } from "@/lib/api";
import { cn } from "@/lib/utils";

interface MarketQuotesCardProps {
  token: string | null;
}

const inr = new Intl.NumberFormat("en-IN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function MarketQuotesCard({ token }: MarketQuotesCardProps) {
  const [symbols, setSymbols] = React.useState("RELIANCE,TCS,NIFTY");
  const [quotes, setQuotes] = React.useState<Quote[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const load = React.useCallback(async () => {
    if (!token) return;
    setError(null);
    setLoading(true);
    const list = symbols
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean);
    if (list.length === 0) {
      setError("Enter at least one symbol.");
      setLoading(false);
      return;
    }
    try {
      const data = await api.getQuotes(token, list, "NSE");
      setQuotes(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch quotes.");
      setQuotes([]);
    } finally {
      setLoading(false);
    }
  }, [token, symbols]);

  React.useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div className="space-y-1.5">
          <CardTitle>Market quotes</CardTitle>
          <CardDescription>
            Simulated NSE quotes — clearly marked as mock data
          </CardDescription>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium text-muted-foreground">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-positive" />
          mock
        </span>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input
            placeholder="e.g. RELIANCE,TCS,NIFTY"
            value={symbols}
            onChange={(e) => setSymbols(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") load();
            }}
          />
          <Button onClick={load} disabled={loading} className="shrink-0">
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
            {loading ? "Fetching…" : "Refresh"}
          </Button>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        {quotes.length > 0 && (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                    <th className="pb-2 pr-3 font-medium">Symbol</th>
                    <th className="pb-2 pr-3 text-right font-medium">Last</th>
                    <th className="pb-2 pr-3 text-right font-medium">Change</th>
                    <th className="hidden pb-2 pr-3 text-right font-medium sm:table-cell">
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
                          <span className="font-medium">{q.symbol}</span>
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
                        <td className="hidden py-2.5 pr-3 text-right tabular-nums text-muted-foreground sm:table-cell">
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
