# Deskly — Sistema de tickets de soporte

Prototipo funcional de un sistema de tickets con ciclo de vida controlado (máquina de estados),
ingesta por webhook firmado con HMAC-SHA256, notificaciones en tiempo real por WebSocket y vista de
detalle renderizada en servidor (SSR).

| Parte          | Tecnología                                         | Carpeta     |
| -------------- | -------------------------------------------------- | ----------- |
| Backend        | Python 3.12, FastAPI, Pydantic v2, PyMongo (async) | `backend/`  |
| Frontend       | Next.js 15 (App Router), React 19, TypeScript      | `frontend/` |
| Base de datos  | MongoDB 7                                          | —           |
| Infraestructura| Docker Compose                                     | raíz        |

## Arranque

Requisitos: Docker con Docker Compose v2.

```bash
git clone https://github.com/UGachuzD/pruebaTecnicaSoftware.git
cd pruebaTecnicaSoftware
cp .env.example .env
docker compose up --build
```

| Servicio            | URL                                  |
| ------------------- | ------------------------------------ |
| Frontend            | http://localhost:3000                |
| API (Swagger UI)    | http://localhost:8000/docs           |
| WebSocket           | ws://localhost:8000/ws/tickets       |

> Antes de usarlo fuera de local, cambia `WEBHOOK_SECRET` en `.env` por un valor aleatorio
> (por ejemplo `openssl rand -hex 32`). `.env` está en `.gitignore`; solo se versiona `.env.example`.

### Datos de ejemplo (seed)

La base arranca vacía. Para cargar 12 tickets de ejemplo, con el stack levantado y desde otra
terminal en la raíz del repositorio:

```bash
docker compose exec backend python -m app.seed
```

Los tickets cubren todos los estados y prioridades, algunos traen comentarios, y alcanzan para ver
dos páginas en el dashboard. El script (`backend/app/seed.py`) solo inserta si la colección está
vacía, así que ejecutarlo de nuevo no duplica datos ni toca tickets existentes. Para volver a
empezar desde cero: `docker compose down -v && docker compose up`.

## Verificación

1. Abre http://localhost:3000. El dashboard muestra el estado vacío y el indicador
   **Conectado en vivo**. Si ejecutas el seed, recarga la página para ver los tickets de ejemplo y
   prueba los filtros por estado y prioridad y la paginación.
2. Crea un ticket (en otra terminal):

   ```bash
   curl -X POST http://localhost:8000/api/tickets \
     -H "Content-Type: application/json" \
     -d '{"titulo":"No carga el panel","descripcion":"Pantalla en blanco al iniciar sesión","prioridad":"alta"}'
   ```

   El ticket aparece en el dashboard sin recargar la página.
3. Entra al detalle (`/tickets/<id>`): la página llega renderizada desde el servidor. Cambia el
   estado con los botones y añade comentarios. Con dos pestañas abiertas en el mismo ticket, los
   cambios se reflejan en ambas.
4. Prueba una transición inválida para ver el error controlado (`409`). El ejemplo crea un ticket
   nuevo (estado `abierto`) e intenta cerrarlo directamente, lo cual no está permitido:

   ```bash
   ID=$(curl -s -X POST http://localhost:8000/api/tickets \
     -H "Content-Type: application/json" \
     -d '{"titulo":"Prueba de transición","descripcion":"Ticket recién creado"}' \
     | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

   curl -i -X POST http://localhost:8000/api/tickets/$ID/transicion \
     -H "Content-Type: application/json" -d '{"estado":"cerrado"}'
   ```

   Respuesta esperada: `409 Conflict` con
   `"detail": "Transición inválida: no se puede pasar de 'abierto' a 'cerrado'."`.
   Que una transición dé `409` depende del estado actual del ticket: `resuelto → cerrado`, por
   ejemplo, es válida y responde `200`.

5. Detén el backend (`docker compose stop backend`) y el indicador pasa a **Desconectado**.
   Vuelve a levantarlo con `docker compose start backend` y **recarga la página**: no hay
   reconexión automática del WebSocket (es un punto bonus que quedó fuera), así que el indicador
   sigue en **Desconectado** hasta que recargas.

## API

| Método | Ruta                               | Descripción                                               |
| ------ | ---------------------------------- | --------------------------------------------------------- |
| POST   | `/api/tickets`                     | Crear ticket (estado inicial `abierto`)                   |
| GET    | `/api/tickets`                     | Listar: `page`, `page_size` (máx. 100), `estado`, `prioridad` |
| GET    | `/api/tickets/{id}`                | Detalle con hilo de comentarios                           |
| PATCH  | `/api/tickets/{id}`                | Actualizar `titulo`, `descripcion`, `prioridad`, `asignado_a` |
| POST   | `/api/tickets/{id}/transicion`     | Cambiar estado: `{"estado": "en_progreso"}`              |
| POST   | `/api/tickets/{id}/comentarios`    | Añadir comentario: `{"autor": "...", "contenido": "..."}` |
| POST   | `/api/webhooks/tickets`            | Ingesta de tickets externos firmada (`X-Signature`)       |
| WS     | `/ws/tickets`                      | Eventos `ticket.creado`, `ticket.actualizado`, `ticket.comentado` |

### Máquina de estados

```
abierto ──► en_progreso ──► resuelto ──► cerrado
                ▲               │
                │               ▼
                └────────── reabierto
```

- `cerrado` es terminal.
- `estado` no se puede modificar por `PATCH` (devuelve `422`); solo por `/transicion`, para que
  ningún camino evite la máquina de estados.
- Una transición inválida responde `409 Conflict` con `estado_actual`, `estado_solicitado` y
  `transiciones_permitidas`.
- Cada ticket expone `transiciones_permitidas`; el frontend dibuja los botones a partir de ese
  campo, así las reglas viven solo en el backend.

### Eventos WebSocket

```json
{ "tipo": "ticket.actualizado", "datos": { "id": "…", "estado": "en_progreso", "comentarios": [], "…": "…" } }
```

`datos` contiene el ticket completo tras el cambio. Si un envío a un cliente falla, se registra en
el log y ese cliente se elimina del conjunto de conexiones activas.

## Probar el webhook manualmente

El backend calcula `HMAC-SHA256(WEBHOOK_SECRET, cuerpo_crudo)` en hexadecimal y lo compara con el
header `X-Signature`. Desde la raíz del repositorio (con `.env` ya creado):

```bash
BODY='{"titulo":"Error al procesar pago","descripcion":"El cliente reporta cargo duplicado","prioridad":"urgente"}'
SECRET=$(grep '^WEBHOOK_SECRET=' .env | cut -d= -f2-)
SIGNATURE=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $NF}')

# Firma válida -> 201
curl -i -X POST http://localhost:8000/api/webhooks/tickets \
  -H "Content-Type: application/json" \
  -H "X-Signature: $SIGNATURE" \
  --data-raw "$BODY"

# Firma inválida -> 401
curl -i -X POST http://localhost:8000/api/webhooks/tickets \
  -H "Content-Type: application/json" \
  -H "X-Signature: firma-falsa" \
  --data-raw "$BODY"
```

La firma se calcula sobre los bytes exactos enviados: si cambias el cuerpo, recalcula `SIGNATURE`.
Un cuerpo con firma válida pero JSON inválido o campos incorrectos responde `422`.

## Tests y calidad de código

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest           # máquina de estados, webhook y seed
.venv/bin/ruff check .     # lint (PEP 8, imports, bugbear, pyupgrade…)
.venv/bin/ruff format --check .
```

```bash
cd frontend
npm ci
npm run lint               # ESLint con next/core-web-vitals + next/typescript
npx tsc --noEmit           # TypeScript en modo strict
```

Los tests del webhook usan un repositorio en memoria inyectado con `dependency_overrides`, por lo
que no requieren MongoDB.

### Integración continua (GitHub Actions)

`.github/workflows/ci.yml` se ejecuta en cada `push` y `pull_request` a `main`, con dos jobs en
paralelo:

| Job        | Pasos                                                                  |
| ---------- | ---------------------------------------------------------------------- |
| `backend`  | Python 3.12 → `pip install -r requirements-dev.txt` → `ruff check` → `ruff format --check` → `pytest` |
| `frontend` | Node 22 → `npm ci` → `npm run lint` → `npx tsc --noEmit`              |

Los comandos son los mismos que se corren en local, así que un fallo en CI se reproduce igual en la
máquina del desarrollador.

## Base de datos: MongoDB

**Por qué MongoDB:** el agregado principal es el ticket con su hilo de comentarios, que siempre se
lee y escribe junto (la vista de detalle los muestra a la vez). En MongoDB los comentarios viven
embebidos en el documento del ticket: el detalle es una sola lectura y añadir un comentario es un
`$push` atómico, sin joins ni tablas intermedias. El dominio no tiene relaciones entre entidades
que exijan integridad referencial (no hay usuarios ni equipos modelados: `asignado_a` es texto), y
los payloads de webhooks externos encajan bien en un modelo de documentos. El listado no necesita
los comentarios, así que se excluyen por proyección.

La contrapartida es que un ticket con miles de comentarios crecería hacia el límite de 16 MB por
documento; para el volumen de un prototipo de soporte no es un riesgo real, y si lo fuera se
moverían los comentarios a su propia colección.

### Índices

Se crean al arrancar el backend (`ensure_indexes`):

| Índice                         | Justificación                                                                 |
| ------------------------------ | ----------------------------------------------------------------------------- |
| `{ estado: 1, creado_en: -1 }` | El dashboard filtra por estado y ordena por fecha de creación descendente. El índice compuesto resuelve filtro y orden sin ordenar en memoria. |
| `{ prioridad: 1, creado_en: -1 }` | Mismo patrón para el filtro por prioridad.                                 |
| `{ creado_en: -1 }`            | Listado sin filtros (vista por defecto del dashboard), ordenado y paginado con `skip`/`limit`. |

La transición de estado usa un `find_one_and_update` condicionado al estado actual
(`{_id, estado: <actual>}`), de modo que dos transiciones simultáneas no se pisan: la segunda
recibe `409`.

## Estructura

```
.
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── api/            # rutas REST, webhook, WebSocket, dependencias y manejo de errores
│   │   ├── core/           # configuración y firma HMAC
│   │   ├── domain/         # enums y máquina de estados (sin dependencias de framework)
│   │   ├── realtime/       # gestor de conexiones WebSocket
│   │   ├── repositories/   # acceso a MongoDB
│   │   ├── schemas/        # modelos Pydantic v2 de entrada/salida
│   │   ├── services/       # casos de uso: orquestan dominio, repositorio y eventos
│   │   └── seed.py         # script manual que inserta tickets de ejemplo
│   └── tests/
└── frontend/
    └── src/
        ├── app/            # rutas App Router: / y /tickets/[id] (SSR, loading, error, not-found)
        ├── components/     # dashboard, detalle, badges, estados de UI
        ├── hooks/          # useTicketStream (WebSocket) y useTickets (listado)
        └── lib/            # cliente HTTP, tipos y formato
```

## Decisiones de frontend

- **Detalle (`/tickets/[id]`) con SSR**: Server Component con `dynamic = "force-dynamic"` que
  consulta al backend por la red interna de Docker (`API_URL=http://backend:8000`). El resultado
  se hidrata en un Client Component que escucha el WebSocket y reemplaza el ticket cuando llega un
  evento con su `id`.
- **Dashboard**: se carga en el cliente con `useTickets`, que cancela peticiones obsoletas con
  `AbortController` al cambiar de página o filtro. Al llegar un evento: `ticket.creado` recarga la
  página actual en segundo plano; `ticket.actualizado`/`ticket.comentado` reemplazan la fila en
  sitio, salvo que el ticket ya no cumpla el filtro, en cuyo caso se recarga.
- **Estados de UI diferenciados**: carga con *skeleton* de tabla, vacío con mensaje según haya o no
  filtros, error con mensaje y botón de reintento. En el detalle: `loading.tsx` (skeleton del
  detalle), `error.tsx` y `not-found.tsx`. Los botones muestran su propio estado ("Aplicando…",
  "Enviando…").
- **`useTicketStream`**: abre el socket en `useEffect` y en la limpieza desregistra los handlers y
  cierra la conexión. Guarda el callback en un `ref` para no reconectar en cada render y valida la
  forma de cada mensaje antes de entregarlo. Devuelve `conectando | conectado | desconectado`, que
  pinta `ConnectionIndicator`.
- Las fechas se muestran en UTC para que el HTML del servidor y la hidratación del cliente
  coincidan.
- `NEXT_PUBLIC_API_URL` y `NEXT_PUBLIC_WS_URL` se inyectan como `build args`, porque Next.js las
  incrusta en el bundle del cliente al compilar.

## Qué dejé fuera y por qué

- **Los puntos bonus salvo el pipeline de CI y el seed** (protección contra replay, idempotencia
  por `event_id`, reconexión automática del WebSocket, suscripción por ticket, optimistic UI,
  Dockerfiles multi-stage, tipos generados desde el esquema). Prioricé cerrar bien el alcance
  obligatorio. En particular, sin reconexión automática el indicador queda en "Desconectado" hasta
  recargar la página.
- **Autenticación de usuarios y de MongoDB**: no se piden. MongoDB no publica su puerto fuera de la
  red de Docker.
- **UI para crear o editar tickets**: el enunciado solo pide listado, detalle, comentarios y cambio
  de estado; la creación se hace por API o webhook.
- **Borrado de tickets**: no está entre los endpoints requeridos.
- **Tests de integración contra MongoDB y tests de frontend**: los tests pedidos (máquina de estados
  y webhook) están cubiertos; lo demás lo verifiqué manualmente contra el stack de Docker Compose.
- **Varias instancias del backend**: el gestor de WebSocket vive en memoria del proceso; escalar
  horizontalmente requeriría un bus de eventos (Redis Pub/Sub, change streams de MongoDB).

## Tiempo real invertido

5 horas.
