from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.dependencies import TicketServiceDep
from app.domain.ticket import TicketPriority, TicketStatus
from app.schemas.ticket import (
    CommentCreate,
    TicketCreate,
    TicketDetail,
    TicketPage,
    TicketUpdate,
    TransitionRequest,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_ticket(payload: TicketCreate, service: TicketServiceDep) -> TicketDetail:
    return await service.create(payload)


@router.get("")
async def list_tickets(
    service: TicketServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    estado: TicketStatus | None = None,
    prioridad: TicketPriority | None = None,
) -> TicketPage:
    return await service.list(page, page_size, estado, prioridad)


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, service: TicketServiceDep) -> TicketDetail:
    return await service.get(ticket_id)


@router.patch("/{ticket_id}")
async def update_ticket(
    ticket_id: str, payload: TicketUpdate, service: TicketServiceDep
) -> TicketDetail:
    return await service.update(ticket_id, payload)


@router.post("/{ticket_id}/transicion")
async def transition_ticket(
    ticket_id: str, payload: TransitionRequest, service: TicketServiceDep
) -> TicketDetail:
    return await service.transition(ticket_id, payload.estado)


@router.post("/{ticket_id}/comentarios", status_code=status.HTTP_201_CREATED)
async def add_comment(
    ticket_id: str, payload: CommentCreate, service: TicketServiceDep
) -> TicketDetail:
    return await service.add_comment(ticket_id, payload)
