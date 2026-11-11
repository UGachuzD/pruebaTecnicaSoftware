import { notFound } from "next/navigation";

import { TicketDetailView } from "@/components/TicketDetailView";
import { ApiError, fetchTicket } from "@/lib/api";
import type { TicketDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

interface TicketPageProps {
  params: Promise<{ id: string }>;
}

async function loadTicket(id: string): Promise<TicketDetail | null> {
  try {
    return await fetchTicket(id);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export default async function TicketPage({ params }: TicketPageProps) {
  const { id } = await params;
  const ticket = await loadTicket(id);
  if (!ticket) notFound();

  return <TicketDetailView key={ticket.id} initialTicket={ticket} />;
}
