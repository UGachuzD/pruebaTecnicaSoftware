from typing import Annotated

from fastapi import Depends, Request
from starlette.requests import HTTPConnection

from app.core.config import Settings, get_settings
from app.realtime.manager import ConnectionManager
from app.repositories.tickets import COLLECTION_NAME, MongoTicketRepository
from app.services.tickets import TicketService


def get_connection_manager(connection: HTTPConnection) -> ConnectionManager:
    return connection.app.state.connection_manager


def get_ticket_service(request: Request) -> TicketService:
    repository = MongoTicketRepository(request.app.state.database[COLLECTION_NAME])
    return TicketService(repository, get_connection_manager(request))


SettingsDep = Annotated[Settings, Depends(get_settings)]
TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]
ConnectionManagerDep = Annotated[ConnectionManager, Depends(get_connection_manager)]
