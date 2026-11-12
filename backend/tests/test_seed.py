import asyncio
from itertools import count

from app.domain.ticket import TicketPriority, TicketStatus
from app.repositories.tickets import Document
from app.schemas.ticket import TicketDetail
from app.seed import SAMPLE_TICKETS, seed_sample_data


class FakeCollection:
    def __init__(self, documents: list[Document] | None = None) -> None:
        self.documents = list(documents or [])
        self._ids = count(1)

    async def count_documents(self, _filter: Document, limit: int = 0) -> int:
        total = len(self.documents)
        return min(total, limit) if limit else total

    async def insert_many(self, documents: list[Document]) -> None:
        for document in documents:
            document["_id"] = str(next(self._ids))
            self.documents.append(document)


def test_seed_inserts_valid_tickets_when_collection_is_empty() -> None:
    collection = FakeCollection()

    inserted = asyncio.run(seed_sample_data(collection))

    assert inserted == len(SAMPLE_TICKETS) == len(collection.documents)
    for document in collection.documents:
        TicketDetail.model_validate({**document, "id": document["_id"]})


def test_seed_covers_every_status_and_priority() -> None:
    collection = FakeCollection()

    asyncio.run(seed_sample_data(collection))

    assert {document["estado"] for document in collection.documents} == set(TicketStatus)
    assert {document["prioridad"] for document in collection.documents} == set(TicketPriority)


def test_seed_is_skipped_when_collection_has_tickets() -> None:
    collection = FakeCollection([{"_id": "existente", "titulo": "Ticket real"}])

    inserted = asyncio.run(seed_sample_data(collection))

    assert inserted == 0
    assert len(collection.documents) == 1
