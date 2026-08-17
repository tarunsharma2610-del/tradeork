"use client";

import { Loader2, Search } from "lucide-react";
import * as React from "react";

import { Input } from "@/components/ui/input";
import { api, type Instrument } from "@/lib/api";
import { cn } from "@/lib/utils";

interface InstrumentSearchProps {
  onSelect: (symbol: string) => void;
  className?: string;
}

/**
 * Debounced search combobox over the instrument catalog. Selecting a result
 * emits its symbol (e.g. "RELIANCE"); results reset to the default after use.
 */
export function InstrumentSearch({ onSelect, className }: InstrumentSearchProps) {
  const [query, setQuery] = React.useState("");
  const [results, setResults] = React.useState<Instrument[]>([]);
  const [open, setOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const boxRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  React.useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setResults([]);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const data = await api.searchInstruments(trimmed, {
          instrument_type: "EQUITY",
          limit: 10,
        });
        setResults(data);
        setError(null);
      } catch (e) {
        setResults([]);
        setError(e instanceof Error ? e.message : "Search failed.");
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  const handleSelect = (symbol: string) => {
    onSelect(symbol);
    setQuery("");
    setResults([]);
    setOpen(false);
  };

  const showDropdown = open && (query.trim() !== "" || loading || error !== null);

  return (
    <div ref={boxRef} className={cn("relative", className)}>
      <div className="relative">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          role="combobox"
          aria-expanded={showDropdown}
          aria-label="Search instruments"
          placeholder="Add symbol (e.g. HDFCBANK)…"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => {
            if (e.key === "Escape") setOpen(false);
            if (e.key === "Enter" && results.length > 0) {
              handleSelect(results[0].symbol);
            }
          }}
          className="pl-9"
        />
        {loading && (
          <Loader2 className="absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        )}
      </div>

      {showDropdown && (
        <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-lg border bg-popover shadow-lg">
          {error ? (
            <p className="px-3 py-2 text-sm text-destructive">{error}</p>
          ) : results.length === 0 ? (
            <p className="px-3 py-2 text-sm text-muted-foreground">
              {loading ? "Searching…" : "No instruments match."}
            </p>
          ) : (
            <ul className="max-h-72 overflow-y-auto">
              {results.map((inst) => (
                <li key={inst.id}>
                  <button
                    type="button"
                    onClick={() => handleSelect(inst.symbol)}
                    className="flex w-full items-baseline justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground"
                  >
                    <span className="font-medium">{inst.symbol}</span>
                    <span className="truncate text-xs text-muted-foreground">
                      {inst.name}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
