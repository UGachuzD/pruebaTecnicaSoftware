"use client";

import Link from "next/link";
import { useEffect } from "react";

interface TicketErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function TicketError({ error, reset }: TicketErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="card error-state" role="alert">
      <p className="error-state__title">No se pudo cargar el ticket</p>
      <p className="error-state__message">
        El servidor no respondió correctamente. Intenta de nuevo en unos segundos.
      </p>
      <div className="actions">
        <button type="button" className="button" onClick={reset}>
          Reintentar
        </button>
        <Link href="/" className="button button--ghost">
          Volver al listado
        </Link>
      </div>
    </div>
  );
}
