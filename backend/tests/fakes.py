from itertools import count

from app.repositories.tickets import Document


class InMemoryTicketRepository:
    def __init__(self) -> None:
        self.documents: dict[str, Document] = {}
        self._ids = count(1)

    async def insert(self, document: Document) -> Document:
        ticket_id = str(next(self._ids))
        stored = {**document, "_id": ticket_id}
        self.documents[ticket_id] = stored
        return stored
