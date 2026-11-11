import type { ConnectionStatus } from "@/hooks/useTicketStream";

const LABELS: Record<ConnectionStatus, string> = {
  conectando: "Conectando…",
  conectado: "Conectado en vivo",
  desconectado: "Desconectado",
};

export function ConnectionIndicator({ status }: { status: ConnectionStatus }) {
  return (
    <span className={`connection connection--${status}`} role="status" aria-live="polite">
      <span className="connection__dot" aria-hidden="true" />
      {LABELS[status]}
    </span>
  );
}
