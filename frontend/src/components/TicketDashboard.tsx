"use client";

import Link from "next/link";
import { useCallback, useState } from "react";

import { PriorityBadge, StatusBadge } from "@/components/Badges";
import { ConnectionIndicator } from "@/components/ConnectionIndicator";
import { EmptyState, ErrorState, TicketTableSkeleton } from "@/components/TicketListStates";
import { useTicketStream } from "@/hooks/useTicketStream";
import { useTickets } from "@/hooks/useTickets";
import { formatDate, PRIORITY_LABELS, STATUS_LABELS } from "@/lib/format";
import {
  TICKET_PRIORITIES,
  TICKET_STATUSES,
  type Ticket,
  type TicketEvent,
  type TicketPriority,
  type TicketStatus,
} from "@/lib/types";

const PAGE_SIZE = 10;

export function TicketDashboard() {
  const [page, setPage] = useState(1);
  const [estado, setEstado] = useState<TicketStatus | undefined>();
  const [prioridad, setPrioridad] = useState<TicketPriority | undefined>();
  const { state, refresh, retry, replaceTicket } = useTickets(page, PAGE_SIZE, {
    estado,
    prioridad,
  });

  const handleEvent = useCallback(
    (event: TicketEvent) => {
      const ticket = event.datos;
      const matchesFilters =
        (!estado || ticket.estado === estado) && (!prioridad || ticket.prioridad === prioridad);
      if (event.tipo === "ticket.creado" || !matchesFilters) {
        refresh();
      } else {
        replaceTicket(ticket);
      }
    },
    [estado, prioridad, refresh, replaceTicket],
  );

  const connection = useTicketStream(handleEvent);

  return (
    <section className="card">
      <header className="card__header">
        <h1>Tickets de soporte</h1>
        <ConnectionIndicator status={connection} />
      </header>

      <div className="filters">
        <label>
          Estado
          <select
            value={estado ?? ""}
            onChange={(event) => {
              setEstado((event.target.value || undefined) as TicketStatus | undefined);
              setPage(1);
            }}
          >
            <option value="">Todos</option>
            {TICKET_STATUSES.map((value) => (
              <option key={value} value={value}>
                {STATUS_LABELS[value]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Prioridad
          <select
            value={prioridad ?? ""}
            onChange={(event) => {
              setPrioridad((event.target.value || undefined) as TicketPriority | undefined);
              setPage(1);
            }}
          >
            <option value="">Todas</option>
            {TICKET_PRIORITIES.map((value) => (
              <option key={value} value={value}>
                {PRIORITY_LABELS[value]}
              </option>
            ))}
          </select>
        </label>
      </div>

      {state.status === "loading" && <TicketTableSkeleton />}
      {state.status === "error" && <ErrorState message={state.message} onRetry={retry} />}
      {state.status === "success" &&
        (state.data.items.length === 0 ? (
          <EmptyState filtered={Boolean(estado || prioridad)} />
        ) : (
          <>
            <TicketTable tickets={state.data.items} />
            <Pagination
              page={state.data.page}
              total={state.data.total}
              pageSize={state.data.page_size}
              onChange={setPage}
            />
          </>
        ))}
    </section>
  );
}

function TicketTable({ tickets }: { tickets: Ticket[] }) {
  return (
    <table className="ticket-table">
      <thead>
        <tr>
          <th>Título</th>
          <th>Estado</th>
          <th>Prioridad</th>
          <th>Asignado a</th>
          <th>Actualizado</th>
        </tr>
      </thead>
      <tbody>
        {tickets.map((ticket) => (
          <tr key={ticket.id}>
            <td>
              <Link href={`/tickets/${ticket.id}`}>{ticket.titulo}</Link>
            </td>
            <td>
              <StatusBadge status={ticket.estado} />
            </td>
            <td>
              <PriorityBadge priority={ticket.prioridad} />
            </td>
            <td>{ticket.asignado_a ?? <span className="muted">Sin asignar</span>}</td>
            <td>{formatDate(ticket.actualizado_en)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

interface PaginationProps {
  page: number;
  total: number;
  pageSize: number;
  onChange: (page: number) => void;
}

function Pagination({ page, total, pageSize, onChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <nav className="pagination" aria-label="Paginación">
      <button
        type="button"
        className="button button--ghost"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
      >
        Anterior
      </button>
      <span>
        Página {page} de {totalPages} · {total} tickets
      </span>
      <button
        type="button"
        className="button button--ghost"
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
      >
        Siguiente
      </button>
    </nav>
  );
}
