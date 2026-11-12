# Decisiones

### [Decisión] MongoDB o PostgreSQL

**Contexto:** el enunciado permite PostgreSQL o MongoDB. Había que elegir y modelar tickets y su
hilo de comentarios.

**Uso de LLM:** le indiqué a Claude Code que usara MongoDB como BD y le pedí implementar el hilo de los comentarios 
para los tickets mediante un arreglo

**Salida del modelo:** propuso embeber los comentarios como arreglo dentro del documento del ticket
(`$push` atómico para comentar), excluirlos por proyección en el listado, usar `ObjectId` como `id`
y la API asíncrona nativa de PyMongo (`AsyncMongoClient`) en lugar de Motor, que está deprecado.

**Mi decisión:** acepté. El detalle siempre muestra ticket y comentarios juntos, así que una sola
lectura es lo natural; descarté una colección aparte de comentarios porque solo se justifica si un
ticket pudiera acumular suficientes comentarios para acercarse al límite de 16 MB por documento que tiene mongo.
Con PostgreSQL necesitaría una tabla `comentarios` relacionada con `tickets` y hacer un join para
mostrar el detalle; no tengo mucho conocimiento sobre joins, y con MongoDB el ticket y sus
comentarios se leen en una sola consulta, sin necesidad de relacionar tablas.

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
reconexión automática no la implementé porque es un punto bonus; preferí priorizar el resto de los
requisitos obligatorios y asegurarme de que funcionaran correctamente.

### [Decisión] Agregar Pipeline de Github Actions

**Contexto:** es parte del bonus agregar un pipeline con lints y test para que cada que se suban cambios 
a main poder checar que todo esta bien antes de subir cambios a una rama en especifico 

**Uso de LLM:** le pedí que creara el .yml con el codigo para que por cada carpeta del monorepo ejecutara los test y lints.

**Salida del modelo:** el archivo `.github/workflows/ci.yml`, que se ejecuta en cada `push` y
`pull_request` a `main` con dos jobs en paralelo, uno por carpeta del monorepo: `backend` corre
`ruff check`, `ruff format --check` y `pytest`, y `frontend` corre `npm run lint` y
`npx tsc --noEmit`. Usa las mismas versiones que los Dockerfiles (Python 3.12 y Node 22) para que
CI pruebe lo mismo que se ejecuta en los contenedores, e instala el frontend con `npm ci` en lugar
de `npm install` para que las dependencias sean exactamente las del `package-lock.json`. Las
actions (`checkout`, `setup-python` y `setup-node`) se actualizaron a la versión 7 después de
revisar sus notas de versión y confirmar que no tenían cambios incompatibles con el workflow.

**Mi decisión:** acepté. Considero importante para codigo desplegado antes de poder unirlo que se verifique con anterioridad 
que lo que se esta tratando de subir no rompa lo que ya esta y se sigan los estandares del proyecto

### [Decisión] Seed de datos de ejemplo manual en lugar de automático

**Contexto:** uno de los bonus es un script de seed que cargue datos de ejemplo al iniciar.

**Uso de LLM:** le pedí que agregara el script de seed.

**Salida del modelo:** en su primera versión, `seed.py` se ejecutaba automáticamente al arrancar
el backend si la colección estaba vacía, controlado por una variable `SEED_SAMPLE_DATA=true` en
`.env.example`. Así, con los 4 comandos de arranque el dashboard ya aparecía con 12 tickets.

**Mi decisión:** modifiqué. No quise que la base se llenara sola, así que le pedí que fuera un
script de Python que se ejecute de forma manual (`docker compose exec backend python -m app.seed`);
se eliminó la carga al arrancar y la variable `SEED_SAMPLE_DATA`. Mi razón es que, para probar el
código, quiero ver primero el estado del dashboard sin ningún ticket y después, al ejecutar el
seed, comprobar cómo se manejan los estados, filtros y paginación con datos. Esto me desvía a
propósito del "al iniciar" del bonus. Una consecuencia es que, después de ejecutar el script, hay
que recargar la página: el seed escribe directo en MongoDB sin pasar por el servicio del backend
que emite los eventos WebSocket. La alternativa de que el seed creara los tickets a través de la
API sí los mostraría en vivo, pero la descarté porque todos quedarían con fecha de creación de
"ahora" y no es necesario para lo que busco probar.

### [Decisión] Corregir el ejemplo de transición inválida del README

**Contexto:** seguí el paso del README para probar una transición inválida (`{"estado":"cerrado"}`)
y en lugar del `409` esperado obtuve `200` y el ticket quedó cerrado.

**Uso de LLM:** le mostré la salida del `curl` y le pregunté por qué no me daba el error `409`.

**Salida del modelo:** revisó los logs del backend y encontró que ese ticket ya estaba en
`resuelto`, porque yo lo había movido desde la interfaz, y `resuelto → cerrado` es una transición
válida. El backend funcionaba bien; el error estaba en el README, que asumía un ticket en `abierto`
sin decirlo. Propuso cambiar el ejemplo para que cree un ticket nuevo y de inmediato intente
cerrarlo, y aclarar que el `409` depende del estado actual del ticket.

**Mi decisión:** acepté el cambio. Un ejemplo que depende de lo que se haya hecho antes no es
reproducible para quien evalúa; con el ticket recién creado el resultado siempre es el mismo. Me
sirvió también para no dar por buena la documentación sin ejecutarla.