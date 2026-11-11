from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.ticket import InvalidTransitionError
from app.services.tickets import TicketConflictError, TicketNotFoundError


async def _invalid_transition(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, InvalidTransitionError)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": str(exc),
            "estado_actual": exc.current,
            "estado_solicitado": exc.target,
            "transiciones_permitidas": list(exc.allowed),
        },
    )


async def _not_found(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


async def _conflict(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(InvalidTransitionError, _invalid_transition)
    app.add_exception_handler(TicketNotFoundError, _not_found)
    app.add_exception_handler(TicketConflictError, _conflict)
