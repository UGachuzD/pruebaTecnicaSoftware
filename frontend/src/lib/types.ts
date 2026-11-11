export const TICKET_STATUSES = [
  "abierto",
  "en_progreso",
  "resuelto",
  "cerrado",
  "reabierto",
] as const;

export const TICKET_PRIORITIES = ["baja", "media", "alta", "urgente"] as const;

export type TicketStatus = (typeof TICKET_STATUSES)[number];
export type TicketPriority = (typeof TICKET_PRIORITIES)[number];

export interface Ticket {
  id: string;
  titulo: string;
  descripcion: string;
  prioridad: TicketPriority;
  estado: TicketStatus;
  asignado_a: string | null;
  creado_en: string;
  actualizado_en: string;
  transiciones_permitidas: TicketStatus[];
}

export interface Comment {
  id: string;
  autor: string;
  contenido: string;
  creado_en: string;
}

export interface TicketDetail extends Ticket {
  comentarios: Comment[];
}

export interface TicketPage {
  items: Ticket[];
  total: number;
  page: number;
  page_size: number;
}

export interface TicketFilters {
  estado?: TicketStatus;
  prioridad?: TicketPriority;
}

export const TICKET_EVENT_TYPES = [
  "ticket.creado",
  "ticket.actualizado",
  "ticket.comentado",
] as const;

export type TicketEventType = (typeof TICKET_EVENT_TYPES)[number];

export interface TicketEvent {
  tipo: TicketEventType;
  datos: TicketDetail;
}
