import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

from app.core.config import get_settings
from app.domain.ticket import TicketPriority, TicketStatus
from app.repositories.tickets import COLLECTION_NAME, Document, ensure_indexes
from app.schemas.ticket import CommentCreate, TicketCreate

logger = logging.getLogger(__name__)

COMMENT_INTERVAL = timedelta(minutes=20)


@dataclass(frozen=True)
class SampleTicket:
    ticket: TicketCreate
    estado: TicketStatus
    hours_ago: int
    comments: tuple[CommentCreate, ...] = ()


def _ticket(
    titulo: str, descripcion: str, prioridad: TicketPriority, asignado_a: str | None = None
) -> TicketCreate:
    return TicketCreate(
        titulo=titulo, descripcion=descripcion, prioridad=prioridad, asignado_a=asignado_a
    )


def _comment(autor: str, contenido: str) -> CommentCreate:
    return CommentCreate(autor=autor, contenido=contenido)


SAMPLE_TICKETS: tuple[SampleTicket, ...] = (
    SampleTicket(
        _ticket(
            "No puedo iniciar sesión",
            "Al ingresar mis credenciales la página se recarga sin mostrar ningún error.",
            TicketPriority.ALTA,
        ),
        TicketStatus.ABIERTO,
        hours_ago=1,
    ),
    SampleTicket(
        _ticket(
            "Cargo duplicado en la tarjeta",
            "El cliente reporta dos cargos por la misma suscripción mensual.",
            TicketPriority.URGENTE,
            "ana.lopez",
        ),
        TicketStatus.EN_PROGRESO,
        hours_ago=3,
        comments=(
            _comment("ana.lopez", "Confirmado en la pasarela de pago, solicito reembolso."),
            _comment("carlos.ruiz", "Revisemos también si afecta a otros clientes."),
        ),
    ),
    SampleTicket(
        _ticket(
            "Error 500 al exportar reporte",
            "Exportar el reporte mensual a CSV devuelve un error 500.",
            TicketPriority.ALTA,
            "carlos.ruiz",
        ),
        TicketStatus.EN_PROGRESO,
        hours_ago=6,
        comments=(_comment("carlos.ruiz", "Reproducido con más de 10 000 filas."),),
    ),
    SampleTicket(
        _ticket(
            "Cambiar correo de facturación",
            "Solicitan actualizar el correo al que llegan las facturas.",
            TicketPriority.BAJA,
            "maria.diaz",
        ),
        TicketStatus.RESUELTO,
        hours_ago=10,
        comments=(_comment("maria.diaz", "Correo actualizado, pendiente de confirmación."),),
    ),
    SampleTicket(
        _ticket(
            "La app móvil se cierra al abrir notificaciones",
            "En Android 14 la aplicación se cierra al tocar una notificación.",
            TicketPriority.MEDIA,
        ),
        TicketStatus.ABIERTO,
        hours_ago=14,
    ),
    SampleTicket(
        _ticket(
            "Solicitud de factura de marzo",
            "El cliente necesita la factura de marzo para su contabilidad.",
            TicketPriority.BAJA,
            "maria.diaz",
        ),
        TicketStatus.CERRADO,
        hours_ago=26,
        comments=(
            _comment("maria.diaz", "Factura enviada por correo."),
            _comment("cliente", "Recibida, gracias."),
        ),
    ),
    SampleTicket(
        _ticket(
            "Lentitud en el dashboard",
            "El dashboard tarda más de 10 segundos en cargar por las mañanas.",
            TicketPriority.MEDIA,
            "carlos.ruiz",
        ),
        TicketStatus.REABIERTO,
        hours_ago=30,
        comments=(
            _comment("carlos.ruiz", "Se agregó caché a la consulta principal."),
            _comment("cliente", "Sigue lento a primera hora del día."),
        ),
    ),
    SampleTicket(
        _ticket(
            "No llegan los correos de recuperación",
            "Los correos para restablecer contraseña no llegan a dominios corporativos.",
            TicketPriority.URGENTE,
        ),
        TicketStatus.ABIERTO,
        hours_ago=34,
    ),
    SampleTicket(
        _ticket(
            "Agregar usuario al equipo de ventas",
            "Dar acceso al nuevo integrante del equipo de ventas.",
            TicketPriority.BAJA,
            "ana.lopez",
        ),
        TicketStatus.RESUELTO,
        hours_ago=48,
    ),
    SampleTicket(
        _ticket(
            "Integración con CRM sin sincronizar",
            "Los contactos nuevos no aparecen en el CRM desde ayer.",
            TicketPriority.ALTA,
            "ana.lopez",
        ),
        TicketStatus.EN_PROGRESO,
        hours_ago=52,
        comments=(_comment("ana.lopez", "El token de la integración expiró, renovándolo."),),
    ),
    SampleTicket(
        _ticket(
            "Traducción incorrecta en el checkout",
            "El botón de pagar aparece en inglés para usuarios en español.",
            TicketPriority.BAJA,
        ),
        TicketStatus.CERRADO,
        hours_ago=72,
    ),
    SampleTicket(
        _ticket(
            "Duda sobre límites del plan",
            "El cliente pregunta cuántos agentes incluye el plan básico.",
            TicketPriority.MEDIA,
        ),
        TicketStatus.ABIERTO,
        hours_ago=96,
    ),
)


def build_documents(now: datetime) -> list[Document]:
    documents: list[Document] = []
    for sample in SAMPLE_TICKETS:
        created_at = now - timedelta(hours=sample.hours_ago)
        comments = [
            {
                "id": uuid4().hex,
                **comment.model_dump(),
                "creado_en": created_at + COMMENT_INTERVAL * (index + 1),
            }
            for index, comment in enumerate(sample.comments)
        ]
        documents.append(
            {
                **sample.ticket.model_dump(),
                "estado": sample.estado,
                "comentarios": comments,
                "creado_en": created_at,
                "actualizado_en": comments[-1]["creado_en"] if comments else created_at,
            }
        )
    return documents


async def seed_sample_data(collection: AsyncCollection) -> int:
    if await collection.count_documents({}, limit=1) > 0:
        logger.info("La colección ya contiene tickets; se omite la carga de datos de ejemplo.")
        return 0
    documents = build_documents(datetime.now(UTC))
    await collection.insert_many(documents)
    logger.info("Datos de ejemplo cargados: %d tickets.", len(documents))
    return len(documents)


async def main() -> None:
    settings = get_settings()
    client: AsyncMongoClient = AsyncMongoClient(settings.mongo_uri, tz_aware=True)
    try:
        database = client[settings.mongo_db]
        await ensure_indexes(database)
        await seed_sample_data(database[COLLECTION_NAME])
    finally:
        await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    asyncio.run(main())
