"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchTickets } from "@/lib/api";
import type { Ticket, TicketFilters, TicketPage } from "@/lib/types";

export type TicketsState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: TicketPage };

interface Result {
  key: string;
  data?: TicketPage;
  error?: string;
}

export function useTickets(page: number, pageSize: number, filters: TicketFilters) {
  const { estado, prioridad } = filters;
  const key = `${page}|${pageSize}|${estado ?? ""}|${prioridad ?? ""}`;
  const [result, setResult] = useState<Result | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    fetchTickets(page, pageSize, { estado, prioridad }, controller.signal)
      .then((data) => setResult({ key, data }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message = error instanceof Error ? error.message : "Error desconocido.";
        setResult({ key, error: message });
      });
    return () => controller.abort();
  }, [key, page, pageSize, estado, prioridad, refreshToken]);

  const refresh = useCallback(() => setRefreshToken((token) => token + 1), []);

  const retry = useCallback(() => {
    setResult(null);
    setRefreshToken((token) => token + 1);
  }, []);

  const replaceTicket = useCallback((ticket: Ticket) => {
    setResult((previous) => {
      if (!previous?.data) return previous;
      const items = previous.data.items.map((item) => (item.id === ticket.id ? ticket : item));
      return { ...previous, data: { ...previous.data, items } };
    });
  }, []);

  let state: TicketsState;
  if (!result || result.key !== key) {
    state = { status: "loading" };
  } else if (result.error !== undefined) {
    state = { status: "error", message: result.error };
  } else {
    state = { status: "success", data: result.data as TicketPage };
  }

  return { state, refresh, retry, replaceTicket };
}
