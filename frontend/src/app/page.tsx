import {
  ArrowRight,
  CandlestickChart,
  LineChart,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import Link from "next/link";

import { BrandMark } from "@/components/brand";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const ticker = [
  { symbol: "RELIANCE", price: "2,984.50", change: 1.24 },
  { symbol: "TCS", price: "4,102.80", change: -0.42 },
  { symbol: "HDFCBANK", price: "1,683.20", change: 0.78 },
  { symbol: "INFY", price: "1,851.60", change: -0.15 },
  { symbol: "NIFTY", price: "24,612.35", change: 0.31 },
  { symbol: "BANKNIFTY", price: "55,870.10", change: 0.92 },
  { symbol: "GOLD", price: "73,940.00", change: 0.54 },
  { symbol: "CRUDEOIL", price: "6,842.00", change: -1.02 },
];

const metrics = [
  { value: "₹10L", label: "Virtual capital" },
  { value: "3", label: "Exchanges (NSE · BSE · MCX)" },
  { value: "EQ · F&O", label: "Instrument types" },
  { value: "100%", label: "Risk-free practice" },
];

const features = [
  {
    icon: CandlestickChart,
    title: "Realistic execution",
    description:
      "Order book, fills and margin handling modelled on live broker APIs — the same engine that will drive real trading.",
  },
  {
    icon: Target,
    title: "Strategy & backtesting",
    description:
      "Define strategies, replay history and measure P&L against transaction costs before committing capital.",
  },
  {
    icon: LineChart,
    title: "Full P&L accounting",
    description:
      "Entry and exit prices, gross and net P&L, and costs preserved at Decimal precision for every trade.",
  },
  {
    icon: ShieldCheck,
    title: "Built for going live",
    description:
      "Strict paper/live separation with a broker adapter layer, so your live account inherits the tested engine.",
  },
];

const steps = [
  {
    step: "01",
    title: "Create your portfolio",
    description: "Open an account and seed a virtual portfolio with capital.",
  },
  {
    step: "02",
    title: "Place simulated orders",
    description: "Trade equities, futures and options across Indian exchanges.",
  },
  {
    step: "03",
    title: "Measure and refine",
    description: "Review P&L, test strategies and build a track record safely.",
  },
];

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col">
      <SiteHeader />

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-[420px] bg-gradient-to-b from-primary/10 to-transparent"
        />
        <div className="relative mx-auto grid w-full max-w-7xl gap-12 px-4 py-20 sm:px-6 lg:grid-cols-2 lg:items-center lg:py-28">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border bg-background/60 px-3 py-1 text-xs font-medium text-muted-foreground">
              <Sparkles className="h-3.5 w-3.5 text-primary" />
              Paper trading for Indian markets
            </div>
            <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
              Practice trading with{" "}
              <span className="text-primary">zero risk</span>
            </h1>
            <p className="max-w-xl text-lg text-muted-foreground">
              Tradeork is a multi-user paper trading platform for NSE, BSE and
              MCX. Equity, futures and options with realistic execution,
              strategies and analytics — before you ever risk real money.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link href="/register">
                  Start paper trading
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/login">Sign in</Link>
              </Button>
            </div>
          </div>

          {/* Live ticker preview */}
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              <div className="flex items-center justify-between border-b px-5 py-3">
                <span className="text-sm font-medium">Market watch</span>
                <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-positive" />
                  Live · simulated
                </span>
              </div>
              <div className="divide-y">
                {ticker.map((row) => (
                  <div
                    key={row.symbol}
                    className="flex items-center justify-between px-5 py-2.5 text-sm"
                  >
                    <span className="font-medium">{row.symbol}</span>
                    <span className="tabular-nums">₹{row.price}</span>
                    <span
                      className={`w-20 text-right font-medium tabular-nums ${
                        row.change >= 0 ? "text-positive" : "text-negative"
                      }`}
                    >
                      {row.change >= 0 ? "▲" : "▼"}{" "}
                      {Math.abs(row.change).toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Metrics band */}
      <section className="border-y bg-muted/40">
        <div className="mx-auto grid w-full max-w-7xl grid-cols-2 gap-6 px-4 py-10 sm:px-6 lg:grid-cols-4">
          {metrics.map((m) => (
            <div key={m.label} className="space-y-1">
              <p className="text-2xl font-bold tracking-tight sm:text-3xl">
                {m.value}
              </p>
              <p className="text-sm text-muted-foreground">{m.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto w-full max-w-7xl px-4 py-20 sm:px-6">
        <div className="mx-auto max-w-2xl space-y-4 text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Built like a real brokerage
          </h2>
          <p className="text-lg text-muted-foreground">
            One execution engine powers manual trading, automation and
            backtesting — and later, live brokerage through a strict adapter
            layer.
          </p>
        </div>
        <div className="mt-14 grid gap-6 sm:grid-cols-2">
          {features.map((f) => (
            <Card key={f.title} className="transition-shadow hover:shadow-lg">
              <CardContent className="p-6">
                <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <f.icon className="h-5 w-5" strokeWidth={2} />
                </div>
                <h3 className="mb-1.5 font-semibold">{f.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {f.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="border-t bg-muted/40">
        <div className="mx-auto grid w-full max-w-7xl gap-10 px-4 py-20 sm:px-6 lg:grid-cols-3">
          {steps.map((s) => (
            <div key={s.step} className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-primary font-semibold text-primary-foreground">
                  {s.step}
                </span>
              </div>
              <h3 className="text-xl font-semibold">{s.title}</h3>
              <p className="text-muted-foreground">{s.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto w-full max-w-7xl px-4 py-20 sm:px-6">
        <div className="flex flex-col items-center gap-6 rounded-2xl border bg-gradient-to-b from-primary/10 to-transparent px-6 py-16 text-center">
          <BrandMark className="h-12 w-12" />
          <h2 className="max-w-xl text-3xl font-bold tracking-tight sm:text-4xl">
            Start building your track record today
          </h2>
          <p className="max-w-lg text-muted-foreground">
            Free, multi-user and ready in minutes. No brokerage account needed.
          </p>
          <Button asChild size="lg">
            <Link href="/register">
              Create your free account
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t">
        <div className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-4 px-4 py-8 text-sm text-muted-foreground sm:flex-row sm:px-6">
          <p>© {new Date().getFullYear()} Tradeork. Paper trading platform.</p>
          <p>NSE · BSE · MCX — Equity, Futures & Options</p>
        </div>
      </footer>
    </main>
  );
}
