"use client";

import { Loader2, RefreshCw, XCircle } from "lucide-react";
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
import { Label } from "@/components/ui/label";
import {
  api,
  type Instrument,
  type Order,
  type OrderSide,
  type OrderType,
  type Portfolio,
  type PortfolioSummary,
  type Position,
} from "@/lib/api";
import { cn } from "@/lib/utils";

interface TradingPanelProps {
  token: string | null;
  portfolios: Portfolio[];
  onPortfolioChanged?: (portfolio: Portfolio) => void;
}

const inr = new Intl.NumberFormat("en-IN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const statusStyles: Record<string, string> = {
  pending: "bg-muted text-muted-foreground",
  partially_filled: "bg-primary/10 text-primary",
  filled: "bg-positive/10 text-positive",
  cancelled: "bg-muted text-muted-foreground",
  rejected: "bg-destructive/10 text-destructive",
};

export function TradingPanel({
  token,
  portfolios,
  onPortfolioChanged,
}: TradingPanelProps) {
  const [selectedId, setSelectedId] = React.useState<string | "">("");
  const [instrument, setInstrument] = React.useState<Instrument | null>(null);
  const [side, setSide] = React.useState<OrderSide>("BUY");
  const [orderType, setOrderType] = React.useState<OrderType>("MARKET");
  const [quantity, setQuantity] = React.useState("10");
  const [limitPrice, setLimitPrice] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [notice, setNotice] = React.useState<string | null>(null);
  const [placing, setPlacing] = React.useState(false);
  const [summary, setSummary] = React.useState<PortfolioSummary | null>(null);
  const [positions, setPositions] = React.useState<Position[]>([]);
  const [orders, setOrders] = React.useState<Order[]>([]);
  const [loadingData, setLoadingData] = React.useState(false);
  const [cancellingId, setCancellingId] = React.useState<string | null>(null);

  const selected = portfolios.find((p) => p.id === selectedId) ?? null;

  const load = React.useCallback(
    async (portfolioId: string) => {
      if (!token) return;
      setLoadingData(true);
      setError(null);
      try {
        const [sum, pos, ord] = await Promise.all([
          api.portfolioSummary(token, portfolioId),
          api.listPositions(token, portfolioId),
          api.listOrders(token, portfolioId),
        ]);
        setSummary(sum);
        setPositions(pos);
        setOrders(ord);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load trading data.");
      } finally {
        setLoadingData(false);
      }
    },
    [token]
  );

  React.useEffect(() => {
    const first = portfolios[0];
    if (first && selectedId === "") {
      setSelectedId(first.id);
      onPortfolioChanged?.(first);
    }
  }, [portfolios, selectedId, onPortfolioChanged]);

  React.useEffect(() => {
    if (selectedId) {
      load(selectedId);
    }
  }, [selectedId, load]);

  const handleSelect = (id: string) => {
    setSelectedId(id);
    const p = portfolios.find((x) => x.id === id);
    if (p) onPortfolioChanged?.(p);
  };

  const resetForm = () => {
    setInstrument(null);
    setQuantity("10");
    setLimitPrice("");
    setNotice(null);
  };

  async function onPlace(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !selected || !instrument) return;
    const qty = Number(quantity);
    if (!Number.isInteger(qty) || qty <= 0) {
      setError("Quantity must be a positive whole number.");
      return;
    }
    if (orderType === "LIMIT" && (Number(limitPrice) <= 0 || limitPrice === "")) {
      setError("A limit price is required for LIMIT orders.");
      return;
    }
    setError(null);
    setNotice(null);
    setPlacing(true);
    try {
      const payload = {
        instrument_id: instrument.id,
        side,
        order_type: orderType,
        quantity: qty,
        ...(orderType === "LIMIT" ? { limit_price: limitPrice } : {}),
      };
      const order = await api.createOrder(token, selected.id, payload);
      setNotice(
        order.status === "filled"
          ? `Filled ${order.filled_quantity} @ ₹${order.avg_fill_price ?? "—"}`
          : order.status === "rejected"
            ? `Rejected: ${order.reject_reason ?? "unknown reason"}`
            : `Order ${order.status}: ${order.side} ${order.quantity} ${order.symbol}`
      );
      resetForm();
      await load(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to place order.");
    } finally {
      setPlacing(false);
    }
  }

  async function onCancel(orderId: string) {
    if (!token || !selected) return;
    setCancellingId(orderId);
    setError(null);
    try {
      await api.cancelOrder(token, selected.id, orderId);
      await load(selected.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to cancel order.");
    } finally {
      setCancellingId(null);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div className="space-y-1.5">
          <CardTitle>Paper trading</CardTitle>
          <CardDescription>
            Place orders, track positions, and manage open orders
          </CardDescription>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => selected && load(selected.id)}
          disabled={!selected || loadingData}
          aria-label="Refresh trading data"
        >
          <RefreshCw
            className={cn("h-4 w-4", loadingData && "animate-spin")}
          />
          {loadingData ? "Loading…" : "Refresh"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-5">
        {portfolios.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Create a portfolio above to start paper trading.
          </p>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-4">
              <div className="space-y-1">
                <Label htmlFor="trade-portfolio">Portfolio</Label>
                <select
                  id="trade-portfolio"
                  className="h-9 rounded-md border border-input bg-background px-3 text-sm"
                  value={selectedId}
                  onChange={(e) => handleSelect(e.target.value)}
                >
                  {portfolios.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
              {summary && (
                <dl className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
                  <div>
                    <dt className="text-xs text-muted-foreground">Cash</dt>
                    <dd className="font-medium tabular-nums">
                      ₹{inr.format(Number(summary.cash))}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">Equity</dt>
                    <dd className="font-medium tabular-nums">
                      ₹{inr.format(Number(summary.equity))}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">Realized P&amp;L</dt>
                    <dd
                      className={cn(
                        "font-medium tabular-nums",
                        Number(summary.realized_pnl) >= 0
                          ? "text-positive"
                          : "text-negative"
                      )}
                    >
                      ₹{inr.format(Number(summary.realized_pnl))}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">Unrealized P&amp;L</dt>
                    <dd
                      className={cn(
                        "font-medium tabular-nums",
                        Number(summary.unrealized_pnl) >= 0
                          ? "text-positive"
                          : "text-negative"
                      )}
                    >
                      ₹{inr.format(Number(summary.unrealized_pnl))}
                    </dd>
                  </div>
                </dl>
              )}
            </div>

            <form
              onSubmit={onPlace}
              className="grid gap-4 rounded-lg border p-4 sm:grid-cols-2 lg:grid-cols-6"
            >
              <div className="space-y-1.5 sm:col-span-2 lg:col-span-2">
                <Label>Instrument</Label>
                {instrument ? (
                  <div className="flex items-center justify-between rounded-md border px-3 py-1.5 text-sm">
                    <span>
                      <span className="font-medium">{instrument.symbol}</span>
                      <span className="ml-2 text-xs text-muted-foreground">
                        {instrument.exchange} · {instrument.instrument_type}
                      </span>
                    </span>
                    <button
                      type="button"
                      onClick={() => setInstrument(null)}
                      className="text-muted-foreground hover:text-destructive"
                      aria-label="Clear instrument"
                    >
                      <XCircle className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <InstrumentSearch
                    onSelect={(symbol) => {
                      api
                        .searchInstruments(symbol, { exchange: "NSE" })
                        .then((res) => setInstrument(res[0] ?? null))
                        .catch((e) =>
                          setError(
                            e instanceof Error ? e.message : "Instrument lookup failed."
                          )
                        );
                    }}
                  />
                )}
              </div>

              <div className="space-y-1.5">
                <Label>Side</Label>
                <div className="flex h-9 gap-1 rounded-md border p-1">
                  {(["BUY", "SELL"] as const).map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setSide(s)}
                      className={cn(
                        "flex-1 rounded text-sm font-medium transition-colors",
                        side === s
                          ? s === "BUY"
                            ? "bg-positive text-positive-foreground"
                            : "bg-negative text-negative-foreground"
                          : "text-muted-foreground hover:text-foreground"
                      )}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-1.5">
                <Label>Type</Label>
                <div className="flex h-9 gap-1 rounded-md border p-1">
                  {(["MARKET", "LIMIT"] as const).map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setOrderType(t)}
                      className={cn(
                        "flex-1 rounded text-sm font-medium transition-colors",
                        orderType === t
                          ? "bg-primary text-primary-foreground"
                          : "text-muted-foreground hover:text-foreground"
                      )}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="trade-qty">Quantity</Label>
                <Input
                  id="trade-qty"
                  type="number"
                  min={1}
                  step={1}
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="trade-limit">Limit price</Label>
                <Input
                  id="trade-limit"
                  type="number"
                  min={0}
                  step="0.01"
                  value={limitPrice}
                  onChange={(e) => setLimitPrice(e.target.value)}
                  disabled={orderType !== "LIMIT"}
                  placeholder={orderType === "LIMIT" ? "e.g. 100.00" : "Market"}
                />
              </div>

              <div className="flex items-end sm:col-span-2 lg:col-span-6">
                <Button
                  type="submit"
                  disabled={!selected || !instrument || placing}
                  className={cn(
                    side === "SELL" &&
                      "bg-negative text-negative-foreground hover:bg-negative/90"
                  )}
                >
                  {placing && <Loader2 className="h-4 w-4 animate-spin" />}
                  {side === "BUY" ? "Buy" : "Sell"} {orderType.toLowerCase()}
                </Button>
              </div>
            </form>

            {error && <p className="text-sm text-destructive">{error}</p>}
            {notice && <p className="text-sm text-muted-foreground">{notice}</p>}

            <section className="space-y-2">
              <h3 className="text-sm font-medium">Positions</h3>
              {positions.length === 0 ? (
                <p className="rounded-lg border border-dashed px-4 py-6 text-center text-sm text-muted-foreground">
                  No open positions yet.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                        <th className="pb-2 pr-3 font-medium">Symbol</th>
                        <th className="pb-2 pr-3 text-right font-medium">Qty</th>
                        <th className="hidden pb-2 pr-3 text-right font-medium sm:table-cell">
                          Avg price
                        </th>
                        <th className="hidden pb-2 pr-3 text-right font-medium sm:table-cell">
                          Last
                        </th>
                        <th className="pb-2 pr-3 text-right font-medium">Mkt value</th>
                        <th className="pb-2 text-right font-medium">Unrealized P&amp;L</th>
                      </tr>
                    </thead>
                    <tbody>
                      {positions.map((pos) => {
                        const upnl = Number(pos.unrealized_pnl);
                        return (
                          <tr key={pos.id} className="border-b last:border-0">
                            <td className="py-2.5 pr-3 font-medium">
                              {pos.symbol}
                              <span className="ml-2 text-xs text-muted-foreground">
                                {pos.exchange}
                              </span>
                            </td>
                            <td className="py-2.5 pr-3 text-right tabular-nums">
                              {pos.quantity}
                            </td>
                            <td className="hidden py-2.5 pr-3 text-right tabular-nums text-muted-foreground sm:table-cell">
                              ₹{inr.format(Number(pos.avg_price))}
                            </td>
                            <td className="hidden py-2.5 pr-3 text-right tabular-nums text-muted-foreground sm:table-cell">
                              ₹{inr.format(Number(pos.last_price))}
                            </td>
                            <td className="py-2.5 pr-3 text-right tabular-nums">
                              ₹{inr.format(Number(pos.market_value))}
                            </td>
                            <td
                              className={cn(
                                "py-2.5 text-right font-medium tabular-nums",
                                upnl >= 0 ? "text-positive" : "text-negative"
                              )}
                            >
                              {upnl >= 0 ? "+" : ""}
                              {inr.format(upnl)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            <section className="space-y-2">
              <h3 className="text-sm font-medium">Orders</h3>
              {orders.length === 0 ? (
                <p className="rounded-lg border border-dashed px-4 py-6 text-center text-sm text-muted-foreground">
                  No orders yet.
                </p>
              ) : (
                <ul className="grid gap-2 sm:grid-cols-2">
                  {orders.map((o) => (
                    <li
                      key={o.id}
                      className="flex items-start justify-between gap-3 rounded-lg border p-3"
                    >
                      <div className="min-w-0 space-y-0.5 text-sm">
                        <p className="flex items-center gap-2 font-medium">
                          {o.side} {o.quantity} {o.symbol}
                          <span
                            className={cn(
                              "rounded-full px-1.5 py-0.5 text-[10px] uppercase tracking-wide",
                              statusStyles[o.status] ?? "bg-muted text-muted-foreground"
                            )}
                          >
                            {o.status.replace("_", " ")}
                          </span>
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {o.order_type}
                          {o.limit_price ? ` @ ₹${o.limit_price}` : ""}
                          {o.avg_fill_price
                            ? ` · filled ₹${o.avg_fill_price}`
                            : ""}
                          {o.reject_reason ? ` · ${o.reject_reason}` : ""}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(o.created_at).toLocaleString()}
                        </p>
                      </div>
                      {o.status === "pending" && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="shrink-0 text-muted-foreground hover:text-destructive"
                          onClick={() => onCancel(o.id)}
                          disabled={cancellingId === o.id}
                          aria-label={`Cancel order ${o.symbol}`}
                        >
                          {cancellingId === o.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <XCircle className="h-4 w-4" />
                          )}
                        </Button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </CardContent>
    </Card>
  );
}
