import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_settings, get_ticket_service
from app.core.config import Settings
from app.core.security import compute_signature
from app.main import app
from app.realtime.manager import ConnectionManager
from app.services.tickets import TicketService
from tests.fakes import InMemoryTicketRepository

SECRET = "secreto-de-prueba"
URL = "/api/webhooks/tickets"
PAYLOAD = {
    "titulo": "Fallo en el pago",
    "descripcion": "El checkout devuelve 500",
    "prioridad": "alta",
}


@pytest.fixture
def repository() -> InMemoryTicketRepository:
    return InMemoryTicketRepository()


@pytest.fixture
def client(repository: InMemoryTicketRepository) -> Iterator[TestClient]:
    service = TicketService(repository, ConnectionManager())
    app.dependency_overrides[get_ticket_service] = lambda: service
    app.dependency_overrides[get_settings] = lambda: Settings(webhook_secret=SECRET)
    yield TestClient(app)
    app.dependency_overrides.clear()


def _post(client: TestClient, body: bytes, signature: str | None):
    headers = {"Content-Type": "application/json"}
    if signature is not None:
        headers["X-Signature"] = signature
    return client.post(URL, content=body, headers=headers)


def test_valid_signature_creates_ticket(
    client: TestClient, repository: InMemoryTicketRepository
) -> None:
    body = json.dumps(PAYLOAD).encode()

    response = _post(client, body, compute_signature(body, SECRET))

    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == PAYLOAD["titulo"]
    assert data["estado"] == "abierto"
    assert len(repository.documents) == 1


def test_invalid_signature_returns_401(
    client: TestClient, repository: InMemoryTicketRepository
) -> None:
    body = json.dumps(PAYLOAD).encode()

    response = _post(client, body, compute_signature(body, "otro-secreto"))

    assert response.status_code == 401
    assert repository.documents == {}


def test_missing_signature_returns_401(
    client: TestClient, repository: InMemoryTicketRepository
) -> None:
    response = _post(client, json.dumps(PAYLOAD).encode(), None)

    assert response.status_code == 401
    assert repository.documents == {}


def test_malformed_payload_with_valid_signature_returns_422(
    client: TestClient, repository: InMemoryTicketRepository
) -> None:
    body = b'{"titulo": "x"'

    response = _post(client, body, compute_signature(body, SECRET))

    assert response.status_code == 422
    assert repository.documents == {}
