import pytest

from app.domain.ticket import (
    InvalidTransitionError,
    TicketStatus,
    allowed_transitions,
    validate_transition,
)

S = TicketStatus


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (S.ABIERTO, S.EN_PROGRESO),
        (S.EN_PROGRESO, S.RESUELTO),
        (S.RESUELTO, S.CERRADO),
        (S.RESUELTO, S.REABIERTO),
        (S.REABIERTO, S.EN_PROGRESO),
    ],
)
def test_valid_transition_is_accepted(current: TicketStatus, target: TicketStatus) -> None:
    validate_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (S.ABIERTO, S.CERRADO),
        (S.ABIERTO, S.RESUELTO),
        (S.EN_PROGRESO, S.ABIERTO),
        (S.CERRADO, S.REABIERTO),
        (S.ABIERTO, S.REABIERTO),
        (S.EN_PROGRESO, S.EN_PROGRESO),
    ],
)
def test_invalid_transition_raises_error(current: TicketStatus, target: TicketStatus) -> None:
    with pytest.raises(InvalidTransitionError) as exc_info:
        validate_transition(current, target)

    assert exc_info.value.current == current
    assert exc_info.value.target == target
    assert exc_info.value.allowed == allowed_transitions(current)


def test_closed_is_a_terminal_state() -> None:
    assert allowed_transitions(S.CERRADO) == ()
