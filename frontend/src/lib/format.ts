import type { TicketPriority, TicketStatus } from "./types";

export const STATUS_LABELS: Record<TicketStatus, string> = {
  abierto: "Abierto",
  en_progreso: "En progreso",
  resuelto: "Resuelto",
  cerrado: "Cerrado",
  reabierto: "Reabierto",
};

export const PRIORITY_LABELS: Record<TicketPriority, string> = {
  baja: "Baja",
  media: "Media",
  alta: "Alta",
  urgente: "Urgente",
};

const dateFormatter = new Intl.DateTimeFormat("es-MX", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "UTC",
});

export function formatDate(value: string): string {
  return `${dateFormatter.format(new Date(value))} UTC`;
}
