export default function TicketLoading() {
  return (
    <article className="card" aria-busy="true" aria-label="Cargando ticket">
      <span className="skeleton skeleton--title" />
      <div className="skeleton-meta">
        {Array.from({ length: 5 }, (_, index) => (
          <span key={index} className="skeleton" />
        ))}
      </div>
      <span className="skeleton skeleton--block" />
      <span className="skeleton skeleton--block" />
    </article>
  );
}
