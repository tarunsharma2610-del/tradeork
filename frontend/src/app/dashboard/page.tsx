"use client";

import { useRouter } from "next/navigation";
import * as React from "react";

import { DashboardHeader } from "@/components/dashboard-header";
import { MarketQuotesCard } from "@/components/market-quotes-card";
import { PortfoliosSection } from "@/components/portfolios-section";
import { StatGrid, type StatItem, statIcons } from "@/components/stat-cards";
import { StrategiesPanel } from "@/components/strategies-panel";
import { TradingPanel } from "@/components/trading-panel";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type Portfolio } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const inr = new Intl.NumberFormat("en-IN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export default function DashboardPage() {
  const { user, tokens, restoring } = useAuth();
  const router = useRouter();
  const [portfolios, setPortfolios] = React.useState<Portfolio[]>([]);
  const [health, setHealth] = React.useState<string | null>(null);
  const [feedInfo, setFeedInfo] = React.useState<{
    mode: string;
    isMock: boolean | null;
    source: string | null;
  } | null>(null);

  const token = tokens?.access_token ?? null;

  React.useEffect(() => {
    if (!restoring && !user) {
      router.replace("/login");
    }
  }, [user, restoring, router]);

  React.useEffect(() => {
    if (!token) return;
    api
      .listPortfolios(token)
      .then(setPortfolios)
      .catch(() => setPortfolios([]));
  }, [token]);

  React.useEffect(() => {
    api
      .health()
      .then((h) => setHealth(h.database === "ok" && h.redis === "ok" ? "Healthy" : "Degraded"))
      .catch(() => setHealth("Unavailable"));
  }, []);

  const totalCapital = portfolios.reduce(
    (sum, p) => sum + Number(p.initial_capital),
    0
  );

  const stats: StatItem[] = [
    {
      label: "Portfolios",
      value: String(portfolios.length),
      hint: "Across your account",
      icon: statIcons.Wallet,
    },
    {
      label: "Total capital",
      value: `₹${inr.format(totalCapital)}`,
      hint: "INR, paper money",
      icon: statIcons.BarChart3,
    },
    {
      label: "Data mode",
      value: feedInfo
        ? feedInfo.isMock === null
          ? "…"
          : feedInfo.isMock
            ? "Mock"
            : "Live"
        : "Mock",
      hint: feedInfo
        ? feedInfo.source
          ? `source: ${feedInfo.source} · mode: ${feedInfo.mode}`
          : `mode: ${feedInfo.mode}`
        : "is_mock: true (default)",
      icon: statIcons.Database,
      accent: feedInfo?.isMock === false ? "positive" : "default",
    },
    {
      label: "Platform",
      value: health ?? "…",
      hint: "Backend health",
      icon: statIcons.Activity,
    },
  ];

  if (restoring) {
    return (
      <main className="flex min-h-dvh items-center justify-center bg-background">
        <p className="text-sm text-muted-foreground">Checking your session…</p>
      </main>
    );
  }

  return (
    <main className="flex min-h-dvh flex-col bg-background">
      <DashboardHeader />
      <div className="mx-auto w-full max-w-7xl flex-1 space-y-6 p-4 sm:p-6">
        <section className="space-y-1.5">
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Welcome back, {user?.full_name?.split(" ")[0] || "trader"}
          </h1>
          <p className="text-muted-foreground">
            Your paper-trading workspace at a glance.
          </p>
        </section>

        <StatGrid items={stats} />

        <div className="grid gap-6 lg:grid-cols-2">
          <PortfoliosSection token={token} />
          <MarketQuotesCard token={token} onFeedInfo={setFeedInfo} />
        </div>

        <TradingPanel token={token} portfolios={portfolios} />

        <StrategiesPanel token={token} portfolios={portfolios} />

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Account</CardTitle>
            <CardDescription>
              Signed in as {user?.email}
              {user?.full_name ? ` (${user.full_name})` : ""}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-x-8 gap-y-2 text-sm sm:grid-cols-3">
            <p className="flex flex-col">
              <span className="text-xs text-muted-foreground">Account ID</span>
              <code className="mt-0.5 rounded bg-muted px-1.5 py-0.5">
                {user?.id}
              </code>
            </p>
            <p className="flex flex-col">
              <span className="text-xs text-muted-foreground">Status</span>
              <span>{user?.is_active ? "Active" : "Disabled"}</span>
            </p>
            <p className="flex flex-col">
              <span className="text-xs text-muted-foreground">Member since</span>
              <span>
                {user ? new Date(user.created_at).toLocaleDateString("en-IN") : "—"}
              </span>
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
