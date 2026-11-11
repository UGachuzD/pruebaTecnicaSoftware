# Decisiones

### [Decisión] MongoDB o PostgresSQL

**Contexto:** el enunciado permite PostgreSQL o MongoDB. Había que elegir y modelar tickets y su
hilo de comentarios.

**Uso de LLM:** le indiqué a Claude Code que usara MongoDB como BD y le pedí implementar el hilo de los comentarios para los tickets mediante un arreglo

**Salida del modelo:** propuso embeber los comentarios como arreglo dentro del documento del ticket
(`$push` atómico para comentar), excluirlos por proyección en el listado, usar `ObjectId` como `id`
y la API asíncrona nativa de PyMongo (`AsyncMongoClient`) en lugar de Motor, que está deprecado.

**Mi decisión:** acepté. El detalle siempre muestra ticket y comentarios juntos, así que una sola
lectura es lo natural; descarté una colección aparte de comentarios porque solo se justifica si un
ticket pudiera acumular suficientes comentarios para acercarse al límite de 16 MB por documento que tiene mongo.

### [Decisión] A donde va el estado de reabierto

**Contexto:** el enunciado fija `abierto → en_progreso → resuelto → cerrado` y `reabierto` desde
`resuelto`, pero no dice a dónde va un ticket `reabierto` ni qué código devolver ante una
transición inválida.

**Uso de LLM:** le pedí implementar la máquina de estados con transiciones explícitas y error claro.

**Salida del modelo:** un diccionario `estado → transiciones permitidas` en `app/domain/ticket.py`
sin dependencias de FastAPI; `reabierto → en_progreso`; `cerrado` terminal; `409 Conflict` con
`estado_actual`, `estado_solicitado` y `transiciones_permitidas`; prohibir `estado` en el `PATCH`;
exponer `transiciones_permitidas` en cada ticket para que el frontend no duplique las reglas; y
aplicar la transición con un update condicionado al estado leído para evitar condiciones de carrera.

**Mi decisión:** acepté. `reabierto → en_progreso` refleja que un ticket reabierto vuelve a
trabajarse antes de resolverse. Elegí `409` sobre `400`/`422` porque la petición es válida en forma
pero entra en conflicto con el estado actual del recurso.

### [Decisión] Verificar la firma del webhook antes de validar el payload

**Contexto:** el webhook debe responder `401` con firma inválida y `422` con payload malformado.
Si FastAPI parsea el body como parámetro Pydantic, valida antes de que el endpoint pueda revisar la
firma, y una petición no autenticada recibiría `422` en vez de `401`.

**Uso de LLM:** le pedí implementar el webhook con HMAC-SHA256 en `X-Signature` y su test.

**Salida del modelo:** leer el cuerpo crudo con `request.body()`, calcular el HMAC sobre esos bytes,
compararlo con `hmac.compare_digest` (tiempo constante) y solo después validar con
`TicketCreate.model_validate_json`, convirtiendo el error en `RequestValidationError` para mantener
el formato estándar de `422`. Tests con un repositorio en memoria vía `dependency_overrides`.

**Mi decisión:** acepté. La firma debe calcularse sobre los bytes exactos recibidos (re-serializar
el JSON cambiaría la firma) y no tiene sentido procesar contenido de un emisor no autenticado.

### [Decisión] Difusión WebSocket y limpieza de clientes

**Contexto:** el servidor debe dejar de enviar mensajes a clientes desconectados sin errores
silenciosos, y el cliente necesita un hook con limpieza correcta.

**Uso de LLM:** le pedí el gestor de conexiones del backend y el hook `useTicketStream`.

**Salida del modelo:** backend: un `set` de conexiones; el endpoint elimina al cliente en `finally`
al recibir `WebSocketDisconnect`; `broadcast` envía en paralelo con `asyncio.gather`, registra en el
log cada envío fallido y descarta ese cliente. Frontend: el socket se crea en `useEffect`, la
limpieza desregistra handlers y cierra; el callback se guarda en un `ref` para no reconectar en cada
render; los mensajes se validan antes de usarse.

**Mi decisión:** acepté. Envío en paralelo para que un cliente lento no retrase al resto. La
reconexión automática no la implemente. 

