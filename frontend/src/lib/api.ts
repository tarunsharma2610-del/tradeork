const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface ExecutionSettings {
  live_execution_enabled: boolean;
  broker_adapter: string;
  broker_is_mock: boolean;
  broker_connected: boolean;
  market_data_provider: string;
  market_data_is_mock: boolean;
}

export type BrokerProvider = "upstox";

export interface BrokerConnection {
  id: string;
  user_id: string;
  provider: BrokerProvider;
  label: string | null;
  access_token_masked: string;
  api_key_masked: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Portfolio {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  initial_capital: string;
  cash: string;
  currency: string;
  status: string;
  execution_mode: string;
  created_at: string;
  updated_at: string;
}

export type OrderSide = "BUY" | "SELL";
export type OrderType = "MARKET" | "LIMIT";

export interface Order {
  id: string;
  portfolio_id: string;
  instrument_id: string;
  symbol: string;
  exchange: string;
  side: OrderSide;
  order_type: OrderType;
  quantity: number;
  limit_price: string | null;
  execution_mode: string;
  broker_order_id: string | null;
  status: string;
  filled_quantity: number;
  avg_fill_price: string | null;
  filled_at: string | null;
  reject_reason: string | null;
  created_at: string;
}

export interface Position {
  id: string;
  portfolio_id: string;
  instrument_id: string;
  symbol: string;
  exchange: string;
  quantity: number;
  avg_price: string;
  realized_pnl: string;
  last_price: string;
  market_value: string;
  unrealized_pnl: string;
  updated_at: string;
}

export interface PortfolioSummary {
  portfolio_id: string;
  name: string;
  initial_capital: string;
  cash: string;
  realized_pnl: string;
  unrealized_pnl: string;
  total_pnl: string;
  equity: string;
  positions_count: number;
  open_orders_count: number;
}

export type StrategyType =
  | "manual"
  | "rsi"
  | "ema_crossover"
  | "vwap"
  | "supertrend"
  | "breakout"
  | "custom";
export type StrategyStatus = "active" | "inactive" | "archived";

export interface Strategy {
  id: string;
  user_id: string;
  portfolio_id: string;
  name: string;
  description: string | null;
  strategy_type: StrategyType;
  parameters: Record<string, unknown>;
  status: StrategyStatus;
  created_at: string;
  updated_at: string;
}

export interface Quote {
  symbol: string;
  exchange: string;
  last_price: string;
  open: string;
  high: string;
  low: string;
  prev_close: string;
  volume: number;
  quote_time: string;
  is_mock: boolean;
  source: string;
}

export interface Instrument {
  id: string;
  symbol: string;
  name: string;
  exchange: string;
  instrument_type: string;
  segment: string | null;
  expiry: string | null;
  strike_price: string | null;
  option_type: string | null;
  lot_size: number;
  tick_size: string;
  is_active: boolean;
}

interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string | null;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${API_PREFIX}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // non-JSON error body; keep statusText
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export const api = {
  executionSettings: (token: string) =>
    request<ExecutionSettings>("/settings/execution", {}, token),
  listBrokerConnections: (token: string) =>
    request<BrokerConnection[]>("/settings/broker", {}, token),
  createBrokerConnection: (
    token: string,
    payload: {
      provider?: BrokerProvider;
      label?: string | null;
      access_token: string;
      api_key?: string | null;
    }
  ) =>
    request<BrokerConnection>("/settings/broker", {
      method: "POST",
      body: JSON.stringify(payload),
    }, token),
  updateBrokerConnection: (
    token: string,
    id: string,
    payload: {
      label?: string | null;
      access_token?: string | null;
      api_key?: string | null;
      is_active?: boolean;
    }
  ) =>
    request<BrokerConnection>(
      `/settings/broker/${id}`,
      { method: "PATCH", body: JSON.stringify(payload) },
      token
    ),
  deleteBrokerConnection: (token: string, id: string) =>
    request<void>(`/settings/broker/${id}`, { method: "DELETE" }, token),
  register: (payload: RegisterPayload) =>
    request<AuthTokens>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  login: (payload: { email: string; password: string }) =>
    request<AuthTokens>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  logout: () =>
    request<void>("/auth/logout", {
      method: "POST",
      body: JSON.stringify({}),
    }),
  refresh: (refreshToken?: string) =>
    request<AuthTokens>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify(
        refreshToken ? { refresh_token: refreshToken } : {}
      ),
    }),
  me: (token: string) => request<User>("/users/me", {}, token),
  listPortfolios: (token: string) =>
    request<Portfolio[]>("/portfolios", {}, token),
  createPortfolio: (
    token: string,
    payload: { name: string; description?: string | null; initial_capital: string }
  ) =>
    request<Portfolio>("/portfolios", {
      method: "POST",
      body: JSON.stringify(payload),
    }, token),
  deletePortfolio: (token: string, id: string) =>
    request<void>(`/portfolios/${id}`, { method: "DELETE" }, token),
  updatePortfolio: (
    token: string,
    id: string,
    payload: {
      name?: string;
      description?: string | null;
      initial_capital?: string;
      status?: string;
      execution_mode?: string;
    }
  ) =>
    request<Portfolio>(
      `/portfolios/${id}`,
      {
        method: "PATCH",
        body: JSON.stringify(payload),
      },
      token
    ),
  createOrder: (
    token: string,
    portfolioId: string,
    payload: {
      instrument_id: string;
      side: OrderSide;
      order_type: OrderType;
      quantity: number;
      limit_price?: string | null;
    }
  ) =>
    request<Order>(
      `/portfolios/${portfolioId}/orders`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      token
    ),
  listOrders: (token: string, portfolioId: string, status?: string) =>
    request<Order[]>(
      `/portfolios/${portfolioId}/orders` +
        (status ? `?status=${encodeURIComponent(status)}` : ""),
      {},
      token
    ),
  cancelOrder: (token: string, portfolioId: string, orderId: string) =>
    request<Order>(
      `/portfolios/${portfolioId}/orders/${orderId}`,
      { method: "DELETE" },
      token
    ),
  listPositions: (token: string, portfolioId: string) =>
    request<Position[]>(`/portfolios/${portfolioId}/positions`, {}, token),
  portfolioSummary: (token: string, portfolioId: string) =>
    request<PortfolioSummary>(`/portfolios/${portfolioId}/summary`, {}, token),
  listStrategies: (token: string, portfolioId: string, status?: string) =>
    request<Strategy[]>(
      `/portfolios/${portfolioId}/strategies` +
        (status ? `?status=${encodeURIComponent(status)}` : ""),
      {},
      token
    ),
  createStrategy: (
    token: string,
    portfolioId: string,
    payload: {
      name: string;
      description?: string | null;
      strategy_type?: StrategyType;
      parameters?: Record<string, unknown>;
      status?: StrategyStatus;
    }
  ) =>
    request<Strategy>(
      `/portfolios/${portfolioId}/strategies`,
      { method: "POST", body: JSON.stringify(payload) },
      token
    ),
  updateStrategy: (
    token: string,
    portfolioId: string,
    strategyId: string,
    payload: {
      name?: string;
      description?: string | null;
      strategy_type?: StrategyType;
      parameters?: Record<string, unknown>;
      status?: StrategyStatus;
    }
  ) =>
    request<Strategy>(
      `/portfolios/${portfolioId}/strategies/${strategyId}`,
      { method: "PATCH", body: JSON.stringify(payload) },
      token
    ),
  deleteStrategy: (
    token: string,
    portfolioId: string,
    strategyId: string
  ) =>
    request<void>(
      `/portfolios/${portfolioId}/strategies/${strategyId}`,
      { method: "DELETE" },
      token
    ),
  getQuotes: (token: string, symbols: string[], exchange: string) =>
    request<Quote[]>(
      `/market/quotes?symbols=${encodeURIComponent(symbols.join(","))}&exchange=${exchange}`,
      {},
      token
    ),
  searchInstruments: (
    q: string,
    opts: { exchange?: string; instrument_type?: string; limit?: number } = {}
  ) =>
    request<Instrument[]>(
      `/instruments?q=${encodeURIComponent(q)}` +
        (opts.exchange ? `&exchange=${opts.exchange}` : "") +
        (opts.instrument_type ? `&instrument_type=${opts.instrument_type}` : "") +
        `&limit=${opts.limit ?? 10}`
    ),
};
