"use client";

import { useEffect, useRef, useState } from "react";

import { TICKET_EVENT_TYPES, type TicketEvent } from "@/lib/types";

export type ConnectionStatus = "conectando" | "conectado" | "desconectado";

function isTicketEvent(value: unknown): value is TicketEvent {
  if (!value || typeof value !== "object") return false;
  const { tipo, datos } = value as Partial<TicketEvent>;
  return (
    typeof tipo === "string" &&
    (TICKET_EVENT_TYPES as readonly string[]).includes(tipo) &&
    typeof datos === "object" &&
    datos !== null &&
    typeof datos.id === "string"
  );
}

export function useTicketStream(onEvent: (event: TicketEvent) => void): ConnectionStatus {
  const [status, setStatus] = useState<ConnectionStatus>("conectando");
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    const url = process.env.NEXT_PUBLIC_WS_URL;
    if (!url) {
      console.error("NEXT_PUBLIC_WS_URL no está configurada.");
      setStatus("desconectado");
      return;
    }

    const socket = new WebSocket(url);
    socket.onopen = () => setStatus("conectado");
    socket.onclose = () => setStatus("desconectado");
    socket.onerror = () => setStatus("desconectado");
    socket.onmessage = (message: MessageEvent<string>) => {
      try {
        const event: unknown = JSON.parse(message.data);
        if (isTicketEvent(event)) {
          onEventRef.current(event);
        } else {
          console.warn("Evento WebSocket con formato desconocido:", event);
        }
      } catch (error) {
        console.error("No se pudo procesar el mensaje WebSocket:", error);
      }
    };

    return () => {
      socket.onopen = null;
      socket.onclose = null;
      socket.onerror = null;
      socket.onmessage = null;
      socket.close();
    };
  }, []);

  return status;
}
