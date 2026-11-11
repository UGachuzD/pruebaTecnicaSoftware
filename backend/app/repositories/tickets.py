from datetime import datetime
from typing import Any, Protocol

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from app.domain.ticket import TicketStatus

Document = dict[str, Any]

COLLECTION_NAME = "tickets"
LIST_PROJECTION = {"comentarios": 0}


class TicketRepository(Protocol):
    async def insert(self, document: Document) -> Document: ...

    async def find_by_id(self, ticket_id: str) -> Document | None: ...

    async def find_page(
        self, filters: Document, skip: int, limit: int
    ) -> tuple[list[Document], int]: ...

    async def update_fields(
        self, ticket_id: str, fields: Document, updated_at: datetime
    ) -> Document | None: ...

    async def update_status(
        self,
        ticket_id: str,
        current: TicketStatus,
        target: TicketStatus,
        updated_at: datetime,
    ) -> Document | None: ...

    async def add_comment(
        self, ticket_id: str, comment: Document, updated_at: datetime
    ) -> Document | None: ...


def _to_object_id(ticket_id: str) -> ObjectId | None:
    return ObjectId(ticket_id) if ObjectId.is_valid(ticket_id) else None


async def ensure_indexes(database: AsyncDatabase) -> None:
    collection = database[COLLECTION_NAME]
    await collection.create_index([("creado_en", DESCENDING)])
    await collection.create_index([("estado", ASCENDING), ("creado_en", DESCENDING)])
    await collection.create_index([("prioridad", ASCENDING), ("creado_en", DESCENDING)])


class MongoTicketRepository:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection

    async def insert(self, document: Document) -> Document:
        result = await self._collection.insert_one(document)
        return {**document, "_id": result.inserted_id}

    async def find_by_id(self, ticket_id: str) -> Document | None:
        object_id = _to_object_id(ticket_id)
        if object_id is None:
            return None
        return await self._collection.find_one({"_id": object_id})

    async def find_page(
        self, filters: Document, skip: int, limit: int
    ) -> tuple[list[Document], int]:
        cursor = (
            self._collection.find(filters, LIST_PROJECTION)
            .sort("creado_en", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        items = await cursor.to_list()
        total = await self._collection.count_documents(filters)
        return items, total

    async def update_fields(
        self, ticket_id: str, fields: Document, updated_at: datetime
    ) -> Document | None:
        return await self._find_and_update(
            {"_id": _to_object_id(ticket_id)},
            {"$set": {**fields, "actualizado_en": updated_at}},
        )

    async def update_status(
        self,
        ticket_id: str,
        current: TicketStatus,
        target: TicketStatus,
        updated_at: datetime,
    ) -> Document | None:
        return await self._find_and_update(
            {"_id": _to_object_id(ticket_id), "estado": current},
            {"$set": {"estado": target, "actualizado_en": updated_at}},
        )

    async def add_comment(
        self, ticket_id: str, comment: Document, updated_at: datetime
    ) -> Document | None:
        return await self._find_and_update(
            {"_id": _to_object_id(ticket_id)},
            {"$push": {"comentarios": comment}, "$set": {"actualizado_en": updated_at}},
        )

    async def _find_and_update(self, query: Document, update: Document) -> Document | None:
        if query["_id"] is None:
            return None
        return await self._collection.find_one_and_update(
            query, update, return_document=ReturnDocument.AFTER
        )
