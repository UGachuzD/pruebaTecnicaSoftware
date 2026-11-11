from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.domain.ticket import TicketPriority, TicketStatus, allowed_transitions


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TicketCreate(InputModel):
    titulo: str = Field(min_length=3, max_length=200)
    descripcion: str = Field(min_length=1, max_length=5000)
    prioridad: TicketPriority = TicketPriority.MEDIA
    asignado_a: str | None = Field(default=None, max_length=100)


class TicketUpdate(InputModel):
    titulo: str | None = Field(default=None, min_length=3, max_length=200)
    descripcion: str | None = Field(default=None, min_length=1, max_length=5000)
    prioridad: TicketPriority | None = None
    asignado_a: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def check_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Debes enviar al menos un campo para actualizar.")
        non_nullable = {"titulo", "descripcion", "prioridad"}
        nulls = sorted(
            name for name in non_nullable & self.model_fields_set if getattr(self, name) is None
        )
        if nulls:
            raise ValueError(f"Los campos {', '.join(nulls)} no pueden ser nulos.")
        return self


class TransitionRequest(InputModel):
    estado: TicketStatus


class CommentCreate(InputModel):
    autor: str = Field(min_length=1, max_length=100)
    contenido: str = Field(min_length=1, max_length=2000)


class CommentRead(BaseModel):
    id: str
    autor: str
    contenido: str
    creado_en: datetime


class TicketRead(BaseModel):
    id: str
    titulo: str
    descripcion: str
    prioridad: TicketPriority
    estado: TicketStatus
    asignado_a: str | None
    creado_en: datetime
    actualizado_en: datetime

    @computed_field
    @property
    def transiciones_permitidas(self) -> list[TicketStatus]:
        return list(allowed_transitions(self.estado))


class TicketDetail(TicketRead):
    comentarios: list[CommentRead]


class TicketPage(BaseModel):
    items: list[TicketRead]
    total: int
    page: int
    page_size: int
