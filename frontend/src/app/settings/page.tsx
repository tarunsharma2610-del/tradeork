"use client";

import { Loader2, Settings as SettingsIcon, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import * as React from "react";

import { DashboardHeader } from "@/components/dashboard-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { api, type ExecutionSettings, type Portfolio } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function SettingsPage() {
  const { user, tokens, restoring } = useAuth();
  const router = useRouter();
  const token = tokens?.access_token ?? null;

  const [portfolios, setPortfolios] = React.useState<Portfolio[]>([]);
  const [execSettings, setExecSettings] = React.useState<ExecutionSettings | null>(
    null
  );
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [updatingId, setUpdatingId] = React.useState<string | null>(null);
  const [confirmingLiveId, setConfirmingLiveId] = React.useState<string | null>(
    null
  );

  React.useEffect(() => {
    if (!restoring && !user) {
      router.replace("/login");
    }
  }, [user, restoring, router]);

  React.useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const [p, s] = await Promise.all([
          api.listPortfolios(token),
          api.executionSettings(token),
        ]);
        if (cancelled) return;
        setPortfolios(p);
        setExecSettings(s);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load settings.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function onSwitchMode(p: Portfolio, mode: "paper" | "live") {
    if (!token) return;
    setUpdatingId(p.id);
    setError(null);
    try {
      const updated = await api.updatePortfolio(token, p.id, {
        execution_mode: mode,
      });
      setPortfolios((prev) =>
        prev.map((item) => (item.id === p.id ? updated : item))
      );
      setConfirmingLiveId(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to switch mode.");
      setConfirmingLiveId(null);
    } finally {
      setUpdatingId(null);
    }
  }

  const liveAvailable = execSettings?.live_execution_enabled ?? false;

  return (
    <main className="flex min-h-dvh flex-col bg-background">
      <DashboardHeader />
      <div className="mx-auto w-full max-w-7xl flex-1 space-y-6 p-4 sm:p-6">
        <section className="space-y-1.5">
          <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight sm:text-3xl">
            <SettingsIcon className="h-7 w-7" />
            Settings
          </h1>
          <p className="text-muted-foreground">
            Trading mode and execution configuration for your account.
          </p>
        </section>

        {loading ? (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading…
          </p>
        ) : (
          <>
            {error && <p className="text-sm text-destructive">{error}</p>}

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <ShieldCheck className="h-5 w-5" />
                  Execution
                </CardTitle>
                <CardDescription>
                  Server-side configuration. Broker credentials are never
                  exposed here.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-x-8 gap-y-2 text-sm sm:grid-cols-3">
                <p className="flex flex-col gap-1">
                  <span className="text-xs text-muted-foreground">
                    Broker adapter
                  </span>
                  <span
                    className={
                      execSettings?.broker_is_mock
                        ? "text-muted-foreground"
                        : "font-medium"
                    }
                  >
                    {execSettings?.broker_is_mock
                      ? "Mock (simulated)"
                      : `${execSettings?.broker_adapter} (live)`}
                  </span>
                </p>
                <p className="flex flex-col gap-1">
                  <span className="text-xs text-muted-foreground">
                    Market data
                  </span>
                  <span
                    className={
                      execSettings?.market_data_is_mock
                        ? "text-muted-foreground"
                        : "font-medium"
                    }
                  >
                    {execSettings?.market_data_is_mock
                      ? "Mock (simulated)"
                      : `${execSettings?.market_data_provider} (live)`}
                  </span>
                </p>
                <p className="flex flex-col gap-1">
                  <span className="text-xs text-muted-foreground">
                    Live portfolios
                  </span>
                  <span
                    className={
                      liveAvailable ? "font-medium" : "text-muted-foreground"
                    }
                  >
                    {liveAvailable
                      ? "Enabled"
                      : "Disabled on this server"}
                  </span>
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Portfolio mode</CardTitle>
                <CardDescription>
                  Choose how orders are executed for each portfolio.
                  {!liveAvailable &&
                    " Live mode is currently disabled on this server — only paper trading is available."}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {portfolios.length === 0 ? (
                  <div className="rounded-lg border border-dashed px-4 py-8 text-center">
                    <p className="text-sm text-muted-foreground">
                      No portfolios yet. Create one on the dashboard to
                      configure its trading mode.
                    </p>
                  </div>
                ) : (
                  <ul className="grid gap-3">
                    {portfolios.map((p) => (
                      <li
                        key={p.id}
                        className="flex flex-col gap-3 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className="min-w-0 space-y-1">
                          <div className="flex items-center gap-2">
                            <p className="truncate font-medium">{p.name}</p>
                            <span
                              className={
                                p.execution_mode === "live"
                                  ? "rounded-full bg-destructive/15 px-2 py-0.5 text-xs font-medium text-destructive"
                                  : "rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                              }
                            >
                              {p.execution_mode}
                            </span>
                          </div>
                          <p className="text-sm tabular-nums text-muted-foreground">
                            {p.execution_mode === "live"
                              ? "Orders route to the connected broker."
                              : "Orders simulate against market quotes."}
                          </p>
                        </div>

                        <div className="flex shrink-0 items-center gap-2">
                          {confirmingLiveId === p.id ? (
                            <>
                              <span className="text-xs text-muted-foreground">
                                Switch to live mode — real orders may be
                                placed. Confirm?
                              </span>
                              <Button
                                variant="destructive"
                                size="sm"
                                disabled={updatingId === p.id}
                                onClick={() => onSwitchMode(p, "live")}
                              >
                                Confirm live
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setConfirmingLiveId(null)}
                              >
                                Cancel
                              </Button>
                            </>
                          ) : (
                            <>
                              <Button
                                variant={
                                  p.execution_mode === "paper"
                                    ? "default"
                                    : "outline"
                                }
                                size="sm"
                                disabled={
                                  updatingId === p.id ||
                                  p.execution_mode === "paper"
                                }
                                onClick={() => onSwitchMode(p, "paper")}
                              >
                                Paper
                              </Button>
                              <Button
                                variant={
                                  p.execution_mode === "live"
                                    ? "destructive"
                                    : "outline"
                                }
                                size="sm"
                                disabled={
                                  updatingId === p.id ||
                                  !liveAvailable ||
                                  p.execution_mode === "live"
                                }
                                onClick={() => setConfirmingLiveId(p.id)}
                              >
                                Live
                              </Button>
                            </>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </main>
  );
}
