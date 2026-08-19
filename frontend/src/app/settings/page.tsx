"use client";

import { KeyRound, Loader2, Settings as SettingsIcon, ShieldCheck } from "lucide-react";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  api,
  type BrokerConnection,
  type ExecutionSettings,
  type Portfolio,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function SettingsPage() {
  const { user, tokens, restoring } = useAuth();
  const router = useRouter();
  const token = tokens?.access_token ?? null;

  const [portfolios, setPortfolios] = React.useState<Portfolio[]>([]);
  const [execSettings, setExecSettings] = React.useState<ExecutionSettings | null>(
    null
  );
  const [connections, setConnections] = React.useState<BrokerConnection[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [updatingId, setUpdatingId] = React.useState<string | null>(null);
  const [confirmingLiveId, setConfirmingLiveId] = React.useState<string | null>(
    null
  );
  const [addLabel, setAddLabel] = React.useState("");
  const [addToken, setAddToken] = React.useState("");
  const [addApiKey, setAddApiKey] = React.useState("");
  const [savingConnection, setSavingConnection] = React.useState(false);
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [editToken, setEditToken] = React.useState("");
  const [confirmingDeleteId, setConfirmingDeleteId] = React.useState<
    string | null
  >(null);

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
        const [p, s, c] = await Promise.all([
          api.listPortfolios(token),
          api.executionSettings(token),
          api.listBrokerConnections(token),
        ]);
        if (cancelled) return;
        setPortfolios(p);
        setExecSettings(s);
        setConnections(c);
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

  async function onAddConnection() {
    if (!token || !addToken.trim()) return;
    setSavingConnection(true);
    setError(null);
    try {
      const created = await api.createBrokerConnection(token, {
        provider: "upstox",
        label: addLabel.trim() || null,
        access_token: addToken.trim(),
        api_key: addApiKey.trim() || null,
      });
      setConnections((prev) => [created, ...prev]);
      setAddLabel("");
      setAddToken("");
      setAddApiKey("");
      setExecSettings((prev) =>
        prev ? { ...prev, broker_connected: true } : prev
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save connection.");
    } finally {
      setSavingConnection(false);
    }
  }

  async function onUpdateConnectionToken(conn: BrokerConnection) {
    if (!token || !editToken.trim()) return;
    setUpdatingId(conn.id);
    setError(null);
    try {
      const updated = await api.updateBrokerConnection(token, conn.id, {
        access_token: editToken.trim(),
      });
      setConnections((prev) =>
        prev.map((item) => (item.id === conn.id ? updated : item))
      );
      setEditingId(null);
      setEditToken("");
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Failed to update connection."
      );
    } finally {
      setUpdatingId(null);
    }
  }

  async function onDeleteConnection(conn: BrokerConnection) {
    if (!token) return;
    setUpdatingId(conn.id);
    setError(null);
    try {
      await api.deleteBrokerConnection(token, conn.id);
      setConnections((prev) => prev.filter((item) => item.id !== conn.id));
      setConfirmingDeleteId(null);
      if (conn.is_active) {
        setExecSettings((prev) =>
          prev ? { ...prev, broker_connected: false } : prev
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to disconnect.");
      setConfirmingDeleteId(null);
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
                      execSettings?.broker_connected
                        ? "font-medium"
                        : "text-muted-foreground"
                    }
                  >
                    {execSettings?.broker_connected
                      ? "Upstox (your account)"
                      : execSettings?.broker_is_mock
                        ? "Mock (simulated)"
                        : `${execSettings?.broker_adapter} (server config)`}
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
                  {liveAvailable &&
                    !execSettings?.broker_connected &&
                    " Add your Upstox API below before live orders will work."}
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

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <KeyRound className="h-5 w-5" />
                  Broker connection
                </CardTitle>
                <CardDescription>
                  Add your Upstox API so live portfolios trade through your own
                  broker account. Tokens are encrypted at rest and only ever
                  shown masked.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {connections.length === 0 ? (
                  <div className="rounded-lg border border-dashed px-4 py-6 text-center">
                    <p className="text-sm text-muted-foreground">
                      No broker connection yet. Add your Upstox API access token
                      below to enable live trading on this account.
                    </p>
                  </div>
                ) : (
                  <ul className="grid gap-3">
                    {connections.map((conn) => (
                      <li
                        key={conn.id}
                        className="flex flex-col gap-3 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className="min-w-0 space-y-1">
                          <div className="flex items-center gap-2">
                            <p className="truncate font-medium">
                              {conn.label ?? conn.provider}
                            </p>
                            <span
                              className={
                                conn.is_active
                                  ? "rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-400"
                                  : "rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                              }
                            >
                              {conn.is_active ? "connected" : "inactive"}
                            </span>
                          </div>
                          <p className="text-sm tabular-nums text-muted-foreground">
                            {conn.provider} · token {conn.access_token_masked}
                            {conn.api_key_masked ? ` · api ${conn.api_key_masked}` : ""}
                          </p>
                          {editingId === conn.id && (
                            <div className="flex flex-col gap-2 pt-2 sm:flex-row">
                              <Input
                                type="password"
                                placeholder="New access token"
                                value={editToken}
                                onChange={(e) => setEditToken(e.target.value)}
                                className="max-w-xs"
                              />
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  disabled={updatingId === conn.id}
                                  onClick={() =>
                                    onUpdateConnectionToken(conn)
                                  }
                                >
                                  Save token
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    setEditingId(null);
                                    setEditToken("");
                                  }}
                                >
                                  Cancel
                                </Button>
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="flex shrink-0 items-center gap-2">
                          {confirmingDeleteId === conn.id ? (
                            <>
                              <span className="text-xs text-muted-foreground">
                                Disconnect this broker? Live orders for this
                                account will stop using it.
                              </span>
                              <Button
                                variant="destructive"
                                size="sm"
                                disabled={updatingId === conn.id}
                                onClick={() => onDeleteConnection(conn)}
                              >
                                Disconnect
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setConfirmingDeleteId(null)}
                              >
                                Cancel
                              </Button>
                            </>
                          ) : (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setEditingId(conn.id);
                                  setEditToken("");
                                }}
                              >
                                Update token
                              </Button>
                              <Button
                                variant="destructive"
                                size="sm"
                                disabled={updatingId === conn.id}
                                onClick={() => setConfirmingDeleteId(conn.id)}
                              >
                                Disconnect
                              </Button>
                            </>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}

                <div className="rounded-lg border p-4">
                  <p className="mb-3 text-sm font-medium">
                    Add Upstox API
                  </p>
                  <div className="grid gap-3">
                    <div className="grid gap-2">
                      <Label htmlFor="conn-label" className="text-xs">
                        Label (optional)
                      </Label>
                      <Input
                        id="conn-label"
                        placeholder="e.g. My main Upstox account"
                        value={addLabel}
                        onChange={(e) => setAddLabel(e.target.value)}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="conn-token" className="text-xs">
                        Access token
                      </Label>
                      <Input
                        id="conn-token"
                        type="password"
                        placeholder="Upstox long-lived access token"
                        value={addToken}
                        onChange={(e) => setAddToken(e.target.value)}
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="conn-apikey" className="text-xs">
                        API key / client ID (optional)
                      </Label>
                      <Input
                        id="conn-apikey"
                        type="password"
                        placeholder="Upstox app client ID"
                        value={addApiKey}
                        onChange={(e) => setAddApiKey(e.target.value)}
                      />
                    </div>
                    <div>
                      <Button
                        disabled={savingConnection || !addToken.trim()}
                        onClick={onAddConnection}
                      >
                        {savingConnection ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          "Save connection"
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </main>
  );
}
