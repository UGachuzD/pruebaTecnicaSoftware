const SKELETON_ROWS = 5;

export function TicketTableSkeleton() {
  return (
    <div className="skeleton-table" aria-busy="true" aria-label="Cargando tickets">
      {Array.from({ length: SKELETON_ROWS }, (_, index) => (
        <div key={index} className="skeleton-row">
          <span className="skeleton skeleton--wide" />
          <span className="skeleton" />
          <span className="skeleton" />
          <span className="skeleton" />
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ filtered }: { filtered: boolean }) {
  return (
    <div className="empty-state">
      <p className="empty-state__title">No hay tickets</p>
      <p className="empty-state__hint">
        {filtered
          ? "Ningún ticket coincide con los filtros seleccionados."
          : "Cuando se cree un ticket (vía API o webhook) aparecerá aquí automáticamente."}
      </p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="error-state" role="alert">
      <p className="error-state__title">No se pudieron cargar los tickets</p>
      <p className="error-state__message">{message}</p>
      <button type="button" className="button" onClick={onRetry}>
        Reintentar
      </button>
    </div>
  );
}
