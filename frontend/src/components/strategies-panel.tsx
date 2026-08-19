"use client";

import { Check, Loader2, Pencil, Plus, Trash2, X } from "lucide-react";
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
import { Label } from "@/components/ui/label";
import {
  api,
  type Portfolio,
  type Strategy,
  type StrategyStatus,
  type StrategyType,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const STRATEGY_TYPES: StrategyType[] = [
  "manual",
  "rsi",
  "ema_crossover",
  "vwap",
  "supertrend",
  "breakout",
  "custom",
];

const statusStyles: Record<string, string> = {
  active: "bg-positive/10 text-positive",
  inactive: "bg-muted text-muted-foreground",
  archived: "bg-muted text-muted-foreground",
};

interface StrategiesPanelProps {
  token: string | null;
  portfolios: Portfolio[];
}

export function StrategiesPanel({ token, portfolios }: StrategiesPanelProps) {
  const [selectedId, setSelectedId] = React.useState<string | "">("");
  const [strategies, setStrategies] = React.useState<Strategy[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const [name, setName] = React.useState("");
  const [type, setType] = React.useState<StrategyType>("manual");
  const [description, setDescription] = React.useState("");
  const [adding, setAdding] = React.useState(false);

  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [editName, setEditName] = React.useState("");
  const [editType, setEditType] = React.useState<StrategyType>("manual");
  const [editDescription, setEditDescription] = React.useState("");
  const [busyId, setBusyId] = React.useState<string | null>(null);
  const [confirmingDeleteId, setConfirmingDeleteId] = React.useState<string | null>(
    null
  );

  const selected = portfolios.find((p) => p.id === selectedId) ?? null;

  const load = React.useCallback(
    async (portfolioId: string) => {
      if (!token) return;
      setLoading(true);
      setError(null);
      try {
        setStrategies(await api.listStrategies(token, portfolioId));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load strategies.");
      } finally {
        setLoading(false);
      }
    },
    [token]
  );

  React.useEffect(() => {
    const first = portfolios[0];
    if (first && selectedId === "") {
      setSelectedId(first.id);
    }
  }, [portfolios, selectedId]);

  React.useEffect(() => {
    if (selectedId) {
      load(selectedId);
    }
  }, [selectedId, load]);

  function startEdit(s: Strategy) {
    setEditingId(s.id);
    setEditName(s.name);
    setEditType(s.strategy_type);
    setEditDescription(s.description ?? "");
  }

  function resetAdd() {
    setName("");
    setType("manual");
    setDescription("");
  }

  async function onAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !selected) return;
    setAdding(true);
    setError(null);
    try {
      await api.createStrategy(token, selected.id, {
        name: name.trim(),
        strategy_type: type,
        description: description.trim() || null,
      });
      resetAdd();
      await load(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add strategy.");
    } finally {
      setAdding(false);
    }
  }

  async function onSaveEdit(s: Strategy) {
    if (!token || !selected) return;
    setBusyId(s.id);
    setError(null);
    try {
      await api.updateStrategy(token, selected.id, s.id, {
        name: editName.trim(),
        strategy_type: editType,
        description: editDescription.trim() || null,
      });
      setEditingId(null);
      await load(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save strategy.");
    } finally {
      setBusyId(null);
    }
  }

  async function onToggleStatus(s: Strategy) {
    if (!token || !selected) return;
    const next: StrategyStatus = s.status === "active" ? "inactive" : "active";
    setBusyId(s.id);
    setError(null);
    try {
      await api.updateStrategy(token, selected.id, s.id, { status: next });
      await load(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update strategy.");
    } finally {
      setBusyId(null);
    }
  }

  async function onDelete(s: Strategy) {
    if (!token || !selected) return;
    setBusyId(s.id);
    setError(null);
    try {
      await api.deleteStrategy(token, selected.id, s.id);
      setConfirmingDeleteId(null);
      await load(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete strategy.");
      setConfirmingDeleteId(null);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Strategies</CardTitle>
        <CardDescription>
          Add and edit strategies for each portfolio
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {portfolios.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Create a portfolio above to add strategies.
          </p>
        ) : (
          <>
            <div className="space-y-1">
              <Label htmlFor="strategy-portfolio">Portfolio</Label>
              <select
                id="strategy-portfolio"
                className="h-9 rounded-md border border-input bg-background px-3 text-sm"
                value={selectedId}
                onChange={(e) => setSelectedId(e.target.value)}
              >
                {portfolios.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <form
              onSubmit={onAdd}
              className="grid gap-3 rounded-lg border p-4 sm:grid-cols-2 lg:grid-cols-12"
            >
              <div className="space-y-1.5 sm:col-span-2 lg:col-span-4">
                <Label htmlFor="strategy-name">Name</Label>
                <Input
                  id="strategy-name"
                  placeholder="e.g. RSI pullback"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  aria-label="Strategy name"
                />
              </div>
              <div className="space-y-1.5 lg:col-span-3">
                <Label htmlFor="strategy-type">Type</Label>
                <select
                  id="strategy-type"
                  className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={type}
                  onChange={(e) => setType(e.target.value as StrategyType)}
                >
                  {STRATEGY_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5 lg:col-span-4">
                <Label htmlFor="strategy-desc">Description</Label>
                <Input
                  id="strategy-desc"
                  placeholder="What does it do?"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  aria-label="Strategy description"
                />
              </div>
              <div className="flex items-end lg:col-span-1">
                <Button
                  type="submit"
                  disabled={!name.trim() || adding}
                  className="w-full"
                  aria-label="Add strategy"
                >
                  {adding ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                  <span className="lg:hidden">Add</span>
                </Button>
              </div>
            </form>

            {error && <p className="text-sm text-destructive">{error}</p>}

            {loading && strategies.length === 0 ? (
              <p className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading…
              </p>
            ) : strategies.length === 0 ? (
              <div className="rounded-lg border border-dashed px-4 py-8 text-center">
                <p className="text-sm text-muted-foreground">
                  No strategies yet. Add one above to start.
                </p>
              </div>
            ) : (
              <ul className="grid gap-3">
                {strategies.map((s) => (
                  <li
                    key={s.id}
                    className="rounded-lg border p-4"
                  >
                    {editingId === s.id ? (
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-12">
                        <div className="space-y-1.5 sm:col-span-2 lg:col-span-4">
                          <Label htmlFor={`edit-name-${s.id}`}>Name</Label>
                          <Input
                            id={`edit-name-${s.id}`}
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                          />
                        </div>
                        <div className="space-y-1.5 lg:col-span-3">
                          <Label htmlFor={`edit-type-${s.id}`}>Type</Label>
                          <select
                            id={`edit-type-${s.id}`}
                            className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                            value={editType}
                            onChange={(e) =>
                              setEditType(e.target.value as StrategyType)
                            }
                          >
                            {STRATEGY_TYPES.map((t) => (
                              <option key={t} value={t}>
                                {t}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="space-y-1.5 lg:col-span-4">
                          <Label htmlFor={`edit-desc-${s.id}`}>
                            Description
                          </Label>
                          <Input
                            id={`edit-desc-${s.id}`}
                            value={editDescription}
                            onChange={(e) => setEditDescription(e.target.value)}
                          />
                        </div>
                        <div className="flex items-end gap-1.5 lg:col-span-1">
                          <Button
                            variant="default"
                            size="icon"
                            disabled={busyId === s.id || !editName.trim()}
                            onClick={() => onSaveEdit(s)}
                            aria-label="Save strategy"
                          >
                            <Check className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setEditingId(null)}
                            aria-label="Cancel edit"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="truncate font-medium">{s.name}</p>
                            <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                              {s.strategy_type}
                            </span>
                            <span
                              className={cn(
                                "rounded-full px-2 py-0.5 text-xs capitalize",
                                statusStyles[s.status] ?? "bg-muted text-muted-foreground"
                              )}
                            >
                              {s.status}
                            </span>
                          </div>
                          {s.description && (
                            <p className="text-sm text-muted-foreground">
                              {s.description}
                            </p>
                          )}
                          <p className="text-xs text-muted-foreground">
                            Added{" "}
                            {new Date(s.created_at).toLocaleDateString("en-IN", {
                              day: "numeric",
                              month: "short",
                              year: "numeric",
                            })}
                          </p>
                        </div>
                        <div className="flex shrink-0 items-center gap-1.5">
                          {s.status !== "archived" && (
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={busyId === s.id}
                              onClick={() => onToggleStatus(s)}
                            >
                              {s.status === "active" ? "Deactivate" : "Activate"}
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => startEdit(s)}
                            aria-label={`Edit strategy ${s.name}`}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          {confirmingDeleteId === s.id ? (
                            <>
                              <Button
                                variant="destructive"
                                size="sm"
                                disabled={busyId === s.id}
                                onClick={() => onDelete(s)}
                              >
                                Confirm
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
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-muted-foreground hover:text-destructive"
                              onClick={() => setConfirmingDeleteId(s.id)}
                              aria-label={`Delete strategy ${s.name}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
