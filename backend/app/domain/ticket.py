from enum import StrEnum


class TicketStatus(StrEnum):
    ABIERTO = "abierto"
    EN_PROGRESO = "en_progreso"
    RESUELTO = "resuelto"
    CERRADO = "cerrado"
    REABIERTO = "reabierto"


class TicketPriority(StrEnum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


TRANSITIONS: dict[TicketStatus, tuple[TicketStatus, ...]] = {
    TicketStatus.ABIERTO: (TicketStatus.EN_PROGRESO,),
    TicketStatus.EN_PROGRESO: (TicketStatus.RESUELTO,),
    TicketStatus.RESUELTO: (TicketStatus.CERRADO, TicketStatus.REABIERTO),
    TicketStatus.REABIERTO: (TicketStatus.EN_PROGRESO,),
    TicketStatus.CERRADO: (),
}


class InvalidTransitionError(Exception):
    def __init__(self, current: TicketStatus, target: TicketStatus) -> None:
        self.current = current
        self.target = target
        self.allowed = allowed_transitions(current)
        super().__init__(f"Transición inválida: no se puede pasar de '{current}' a '{target}'.")


def allowed_transitions(current: TicketStatus) -> tuple[TicketStatus, ...]:
    return TRANSITIONS[current]


def validate_transition(current: TicketStatus, target: TicketStatus) -> None:
    if target not in TRANSITIONS[current]:
        raise InvalidTransitionError(current, target)
