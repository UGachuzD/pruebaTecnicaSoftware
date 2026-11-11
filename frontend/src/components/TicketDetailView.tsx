"use client";

import Link from "next/link";
import { type FormEvent, useCallback, useState } from "react";

import { PriorityBadge, StatusBadge } from "@/components/Badges";
import { ConnectionIndicator } from "@/components/ConnectionIndicator";
import { useTicketStream } from "@/hooks/useTicketStream";
import { addComment, transitionTicket } from "@/lib/api";
import { formatDate, STATUS_LABELS } from "@/lib/format";
import type { Comment, TicketDetail, TicketEvent, TicketStatus } from "@/lib/types";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Error desconocido.";
}

export function TicketDetailView({ initialTicket }: { initialTicket: TicketDetail }) {
  const [ticket, setTicket] = useState(initialTicket);

  const handleEvent = useCallback(
    (event: TicketEvent) => {
      if (event.datos.id === initialTicket.id) setTicket(event.datos);
    },
    [initialTicket.id],
  );
  const connection = useTicketStream(handleEvent);

  return (
    <article className="card">
      <Link href="/" className="back-link">
        ← Volver al listado
      </Link>
      <header className="card__header">
        <h1>{ticket.titulo}</h1>
        <ConnectionIndicator status={connection} />
      </header>

      <dl className="ticket-meta">
        <div>
          <dt>Estado</dt>
          <dd>
            <StatusBadge status={ticket.estado} />
          </dd>
        </div>
        <div>
          <dt>Prioridad</dt>
          <dd>
            <PriorityBadge priority={ticket.prioridad} />
          </dd>
        </div>
        <div>
          <dt>Asignado a</dt>
          <dd>{ticket.asignado_a ?? "Sin asignar"}</dd>
        </div>
        <div>
          <dt>Creado</dt>
          <dd>{formatDate(ticket.creado_en)}</dd>
        </div>
        <div>
          <dt>Actualizado</dt>
          <dd>{formatDate(ticket.actualizado_en)}</dd>
        </div>
      </dl>

      <p className="ticket-description">{ticket.descripcion}</p>

      <StatusActions ticket={ticket} onUpdated={setTicket} />
      <CommentThread comments={ticket.comentarios} />
      <CommentForm ticketId={ticket.id} onCreated={setTicket} />
    </article>
  );
}

type TicketHandler = (ticket: TicketDetail) => void;

function StatusActions({ ticket, onUpdated }: { ticket: TicketDetail; onUpdated: TicketHandler }) {
  const [pending, setPending] = useState<TicketStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleTransition(target: TicketStatus) {
    setPending(target);
    setError(null);
    try {
      onUpdated(await transitionTicket(ticket.id, target));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPending(null);
    }
  }

  return (
    <section className="section">
      <h2>Cambiar estado</h2>
      {ticket.transiciones_permitidas.length === 0 ? (
        <p className="muted">Este ticket está cerrado y no admite más transiciones.</p>
      ) : (
        <div className="actions">
          {ticket.transiciones_permitidas.map((target) => (
            <button
              key={target}
              type="button"
              className="button"
              disabled={pending !== null}
              onClick={() => handleTransition(target)}
            >
              {pending === target ? "Aplicando…" : `Mover a ${STATUS_LABELS[target]}`}
            </button>
          ))}
        </div>
      )}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </section>
  );
}

function CommentThread({ comments }: { comments: Comment[] }) {
  return (
    <section className="section">
      <h2>Comentarios ({comments.length})</h2>
      {comments.length === 0 ? (
        <p className="muted">Aún no hay comentarios en este ticket.</p>
      ) : (
        <ol className="comments">
          {comments.map((comment) => (
            <li key={comment.id} className="comment">
              <p className="comment__meta">
                <strong>{comment.autor}</strong> · {formatDate(comment.creado_en)}
              </p>
              <p>{comment.contenido}</p>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function CommentForm({ ticketId, onCreated }: { ticketId: string; onCreated: TicketHandler }) {
  const [autor, setAutor] = useState("");
  const [contenido, setContenido] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      onCreated(await addComment(ticketId, { autor, contenido }));
      setContenido("");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="section comment-form" onSubmit={handleSubmit}>
      <h2>Añadir comentario</h2>
      <label>
        Autor
        <input value={autor} onChange={(e) => setAutor(e.target.value)} required maxLength={100} />
      </label>
      <label>
        Comentario
        <textarea
          value={contenido}
          onChange={(e) => setContenido(e.target.value)}
          required
          maxLength={2000}
          rows={3}
        />
      </label>
      <button type="submit" className="button" disabled={submitting}>
        {submitting ? "Enviando…" : "Comentar"}
      </button>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
