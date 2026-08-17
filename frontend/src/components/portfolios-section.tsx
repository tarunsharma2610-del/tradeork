"use client";

import { FolderPlus, Loader2, Trash2 } from "lucide-react";
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
import { api, type Portfolio } from "@/lib/api";

interface PortfoliosSectionProps {
  token: string | null;
}

const inr = new Intl.NumberFormat("en-IN", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function PortfoliosSection({ token }: PortfoliosSectionProps) {
  const [portfolios, setPortfolios] = React.useState<Portfolio[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [name, setName] = React.useState("");
  const [capital, setCapital] = React.useState("100000");
  const [error, setError] = React.useState<string | null>(null);
  const [confirmingId, setConfirmingId] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await api.listPortfolios(token);
      setPortfolios(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load portfolios.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  React.useEffect(() => {
    load();
  }, [load]);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setError(null);
    try {
      await api.createPortfolio(token, {
        name: name.trim(),
        description: null,
        initial_capital: capital,
      });
      setName("");
      setCapital("100000");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create portfolio.");
    }
  }

  async function onDelete(id: string) {
    if (!token) return;
    setError(null);
    try {
      await api.deletePortfolio(token, id);
      setPortfolios((prev) => prev.filter((p) => p.id !== id));
      setConfirmingId(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete portfolio.");
      setConfirmingId(null);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolios</CardTitle>
        <CardDescription>
          Paper-trading portfolios scoped to your account
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={onCreate} className="flex gap-2">
          <Input
            placeholder="Portfolio name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            aria-label="Portfolio name"
          />
          <Input
            placeholder="Initial capital (INR)"
            value={capital}
            onChange={(e) => setCapital(e.target.value)}
            className="max-w-[180px]"
            aria-label="Initial capital in INR"
          />
          <Button
            type="submit"
            disabled={!name.trim() || loading}
            className="shrink-0"
          >
            <FolderPlus className="h-4 w-4" />
            Create
          </Button>
        </form>

        {error && <p className="text-sm text-destructive">{error}</p>}

        {loading && portfolios.length === 0 ? (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading…
          </p>
        ) : portfolios.length === 0 ? (
          <div className="rounded-lg border border-dashed px-4 py-8 text-center">
            <p className="text-sm text-muted-foreground">
              No portfolios yet. Create one to start paper trading.
            </p>
          </div>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {portfolios.map((p) => (
              <li
                key={p.id}
                className="flex items-start justify-between gap-3 rounded-lg border p-4"
              >
                <div className="min-w-0 space-y-1">
                  <div className="flex items-center gap-2">
                    <p className="truncate font-medium">{p.name}</p>
                    <span className="rounded-full bg-muted px-2 py-0.5 text-xs capitalize text-muted-foreground">
                      {p.status}
                    </span>
                  </div>
                  <p className="text-sm tabular-nums text-muted-foreground">
                    ₹{inr.format(Number(p.initial_capital))} {p.currency}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Created{" "}
                    {new Date(p.created_at).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </p>
                </div>
                {confirmingId === p.id ? (
                  <div className="flex shrink-0 items-center gap-1.5">
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => onDelete(p.id)}
                      aria-label={`Confirm delete portfolio ${p.name}`}
                    >
                      Confirm
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setConfirmingId(null)}
                      aria-label={`Cancel delete portfolio ${p.name}`}
                    >
                      Cancel
                    </Button>
                  </div>
                ) : (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="shrink-0 text-muted-foreground hover:text-destructive"
                    onClick={() => setConfirmingId(p.id)}
                    aria-label={`Delete portfolio ${p.name}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
