import type { TicketDetail, TicketFilters, TicketPage, TicketStatus } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function resolveBaseUrl(): string {
  const url =
    typeof window === "undefined" ? process.env.API_URL : process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    throw new Error("La URL del API no está configurada (API_URL / NEXT_PUBLIC_API_URL).");
  }
  return url;
}

function extractMessage(body: unknown, status: number): string {
  if (body && typeof body === "object" && "detail" in body) {
    const { detail } = body as { detail: unknown };
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (item && typeof item === "object" && "msg" in item ? item.msg : ""))
        .filter(Boolean)
        .join(" · ");
    }
  }
  return `Error inesperado del servidor (${status}).`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${resolveBaseUrl()}${path}`, {
    ...init,
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(extractMessage(body, response.status), response.status);
  }
  return body as T;
}

export function fetchTickets(
  page: number,
  pageSize: number,
  filters: TicketFilters,
  signal?: AbortSignal,
): Promise<TicketPage> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (filters.estado) params.set("estado", filters.estado);
  if (filters.prioridad) params.set("prioridad", filters.prioridad);
  return request<TicketPage>(`/api/tickets?${params}`, { signal });
}

export function fetchTicket(id: string): Promise<TicketDetail> {
  return request<TicketDetail>(`/api/tickets/${encodeURIComponent(id)}`);
}

export function transitionTicket(id: string, estado: TicketStatus): Promise<TicketDetail> {
  return request<TicketDetail>(`/api/tickets/${encodeURIComponent(id)}/transicion`, {
    method: "POST",
    body: JSON.stringify({ estado }),
  });
}

export function addComment(
  id: string,
  comment: { autor: string; contenido: string },
): Promise<TicketDetail> {
  return request<TicketDetail>(`/api/tickets/${encodeURIComponent(id)}/comentarios`, {
    method: "POST",
    body: JSON.stringify(comment),
  });
}
