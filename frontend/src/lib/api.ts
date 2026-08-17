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

export interface HealthStatus {
  status: string;
  database: string;
  redis: string;
  environment: string;
}

export interface Portfolio {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  initial_capital: string;
  currency: string;
  status: string;
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
  health: () => request<HealthStatus>("/health"),
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
  getQuotes: (token: string, symbols: string[], exchange: string) =>
    request<Quote[]>(
      `/market/quotes?symbols=${encodeURIComponent(symbols.join(","))}&exchange=${exchange}`,
      {},
      token
    ),
};
