import Link from "next/link";

export default function TicketNotFound() {
  return (
    <div className="card empty-state">
      <p className="empty-state__title">Ticket no encontrado</p>
      <p className="empty-state__hint">El identificador no corresponde a ningún ticket.</p>
      <Link href="/" className="button">
        Volver al listado
      </Link>
    </div>
  );
}
