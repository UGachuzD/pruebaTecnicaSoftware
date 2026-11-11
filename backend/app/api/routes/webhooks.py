from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api.dependencies import SettingsDep, TicketServiceDep
from app.core.security import verify_signature
from app.schemas.ticket import TicketCreate, TicketDetail

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
async def ingest_ticket(
    request: Request,
    settings: SettingsDep,
    service: TicketServiceDep,
    x_signature: Annotated[str | None, Header()] = None,
) -> TicketDetail:
    body = await request.body()
    if not verify_signature(body, x_signature, settings.webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma inválida o ausente en el header X-Signature.",
        )
    try:
        payload = TicketCreate.model_validate_json(body)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors(include_url=False)) from exc
    return await service.create(payload)
