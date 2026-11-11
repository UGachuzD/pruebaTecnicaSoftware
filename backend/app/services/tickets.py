from datetime import UTC, datetime
from uuid import uuid4

from app.domain.ticket import TicketPriority, TicketStatus, validate_transition
from app.realtime.manager import ConnectionManager, TicketEvent
from app.repositories.tickets import Document, TicketRepository
from app.schemas.ticket import (
    CommentCreate,
    TicketCreate,
    TicketDetail,
    TicketPage,
    TicketRead,
    TicketUpdate,
)


class TicketNotFoundError(Exception):
    def __init__(self, ticket_id: str) -> None:
        self.ticket_id = ticket_id
        super().__init__(f"No existe un ticket con id '{ticket_id}'.")


class TicketConflictError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(UTC)


def _to_detail(document: Document) -> TicketDetail:
    return TicketDetail.model_validate({**document, "id": str(document["_id"])})


def _to_read(document: Document) -> TicketRead:
    return TicketRead.model_validate({**document, "id": str(document["_id"])})


class TicketService:
    def __init__(self, repository: TicketRepository, notifier: ConnectionManager) -> None:
        self._repository = repository
        self._notifier = notifier

    async def create(self, data: TicketCreate) -> TicketDetail:
        now = _now()
        document = {
            **data.model_dump(),
            "estado": TicketStatus.ABIERTO,
            "comentarios": [],
            "creado_en": now,
            "actualizado_en": now,
        }
        ticket = _to_detail(await self._repository.insert(document))
        await self._publish(TicketEvent.CREADO, ticket)
        return ticket

    async def list(
        self,
        page: int,
        page_size: int,
        estado: TicketStatus | None = None,
        prioridad: TicketPriority | None = None,
    ) -> TicketPage:
        filters: Document = {}
        if estado is not None:
            filters["estado"] = estado
        if prioridad is not None:
            filters["prioridad"] = prioridad
        documents, total = await self._repository.find_page(
            filters, skip=(page - 1) * page_size, limit=page_size
        )
        return TicketPage(
            items=[_to_read(document) for document in documents],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get(self, ticket_id: str) -> TicketDetail:
        return _to_detail(await self._get_document(ticket_id))

    async def update(self, ticket_id: str, data: TicketUpdate) -> TicketDetail:
        document = await self._repository.update_fields(
            ticket_id, data.model_dump(exclude_unset=True), _now()
        )
        if document is None:
            raise TicketNotFoundError(ticket_id)
        ticket = _to_detail(document)
        await self._publish(TicketEvent.ACTUALIZADO, ticket)
        return ticket

    async def transition(self, ticket_id: str, target: TicketStatus) -> TicketDetail:
        current = TicketStatus((await self._get_document(ticket_id))["estado"])
        validate_transition(current, target)
        document = await self._repository.update_status(ticket_id, current, target, _now())
        if document is None:
            raise TicketConflictError(
                "El ticket cambió de estado mientras se procesaba la transición. "
                "Consulta su estado actual e inténtalo de nuevo."
            )
        ticket = _to_detail(document)
        await self._publish(TicketEvent.ACTUALIZADO, ticket)
        return ticket

    async def add_comment(self, ticket_id: str, data: CommentCreate) -> TicketDetail:
        now = _now()
        comment = {"id": uuid4().hex, **data.model_dump(), "creado_en": now}
        document = await self._repository.add_comment(ticket_id, comment, now)
        if document is None:
            raise TicketNotFoundError(ticket_id)
        ticket = _to_detail(document)
        await self._publish(TicketEvent.COMENTADO, ticket)
        return ticket

    async def _get_document(self, ticket_id: str) -> Document:
        document = await self._repository.find_by_id(ticket_id)
        if document is None:
            raise TicketNotFoundError(ticket_id)
        return document

    async def _publish(self, event: TicketEvent, ticket: TicketDetail) -> None:
        await self._notifier.broadcast(event, ticket.model_dump(mode="json"))
