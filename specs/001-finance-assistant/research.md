# Research: Asistente de Finanzas Personales con IA (Demo)

**Fase 0** — Decisiones técnicas. El stack vino especificado por el usuario, por lo que este
documento consolida decisiones y justificaciones (no quedan `NEEDS CLARIFICATION`).

---

## D1. Representación del dinero (precisión exacta)

- **Decisión**: almacenar y operar los montos como **enteros en unidades menores (céntimos)**.
  En la API los montos viajan como `amount_minor` (entero) + `currency` (ISO 4217, p. ej. `COP`/`USD`).
  El frontend divide por 100 solo para **mostrar**, nunca para sumar.
- **Rationale**: SQLite no tiene tipo decimal exacto y `float` viola el Principio I (precisión). Los
  enteros dan aritmética exacta y determinista; toda suma ocurre en el backend.
- **Alternativas consideradas**:
  - `Decimal` de Python persistido como texto: exacto, pero añade parseo en cada lectura y riesgo de
    formatos inconsistentes. Enteros son más simples y rápidos.
  - `REAL`/float en SQLite: rechazado — errores de redondeo inaceptables con dinero.

## D2. Persistencia: `sqlite3` de stdlib (sin ORM)

- **Decisión**: usar el módulo estándar `sqlite3` con una capa fina de `repositories/` (SQL explícito,
  una función por operación). Esquema creado en `db.py` al arrancar si no existe.
- **Rationale**: el usuario pidió "sin ORM pesado"; el Principio III premia la simplicidad. Sin
  dependencias extra, SQL visible y auditable, fácil de testear.
- **Alternativas consideradas**:
  - **SQLModel/SQLAlchemy**: menos boilerplate tipado pero arrastra SQLAlchemy (más pesado) y magia
    que oscurece el SQL. Rechazado para esta demo.
  - Archivos JSON: no soporta consultas/agregaciones cómodas; rechazado.
- **Notas**: activar `PRAGMA foreign_keys=ON`; conexión por request (SQLite es local y de un usuario);
  `check_same_thread=False` con acceso serializado simple dado el bajo volumen.

## D3. Integración con Gemini (categorización + chat)

- **Decisión**: adaptador único `app/llm/gemini.py` que lee `GEMINI_API_KEY` de `.env` vía
  `python-dotenv`. Expone funciones de alto nivel (`sugerir_categoria(...)`, `redactar_respuesta(...)`).
  Si no hay clave o la llamada falla/expira, devuelve un resultado de **degradación** explícito (no
  lanza hacia el usuario final sin control).
- **Rationale**: aísla el proveedor (Principio III), permite testear el resto sin red y cumple el
  requisito de clave solo por entorno. Alineado con el patrón previo del proyecto (adaptador `llm`).
- **Alternativas consideradas**:
  - Llamar al SDK directamente desde los servicios: acopla y dificulta el testeo. Rechazado.
  - Reusar el adaptador Node `src/llm.js`: pertenece al prototipo previo; el backend ahora es Python.
- **Modelo**: familia Gemini del tier gratis (p. ej. `gemini-2.0-flash` o el vigente en AI Studio),
  configurable por env `GEMINI_MODEL` con un valor por defecto sensato.

## D4. Categorización: IA con fallback por reglas

- **Decisión**: `services/categorize.py` intenta Gemini (salida JSON: `categoria`, `confianza`); si
  no hay clave, falla, o la confianza < umbral, aplica un **fallback determinista por palabras clave**
  (mapa comercio/keyword → categoría). Si tampoco hay match confiable → `"Sin categorizar"`.
- **Rationale**: cumple FR-005/FR-007 y la degradación controlada (Principio V) sin bloquear el
  registro. El fallback es puro y testeable en pytest sin red.
- **Alternativas consideradas**:
  - Solo IA: rompe si no hay clave. Rechazado (contradice FR-007).
  - Solo reglas: pierde el valor "IA" de la demo. Se combinan.
- **Umbral de confianza**: por defecto `0.6` (configurable); por debajo se trata como sugerencia débil
  y se prefiere el fallback o "Sin categorizar".

## D5. Chat anclado a datos reales (la IA no calcula)

- **Decisión**: `services/chat.py` primero **calcula de forma determinista** las cifras relevantes
  (con `services/finance.py`) según la intención detectada, arma un contexto compacto con esas cifras
  ya resueltas + sus fuentes, y solo entonces pide a Gemini que **redacte** la respuesta en lenguaje
  natural citando las fuentes. Las cifras del texto provienen del cálculo, no del modelo.
- **Rationale**: núcleo del Principio I y IV. Garantiza que la respuesta numérica coincida con el
  dashboard (SC-003) y sea trazable (FR-019/FR-020).
- **Detección de intención (demo, sin sobre-ingeniería)**: parseo ligero de la pregunta para extraer
  categoría y periodo (mes en curso por defecto, FR-022) e identificar el tipo de consulta
  (gasto por categoría / neto del mes / asequibilidad). Si falta un dato, se pide (FR-021).
- **Asequibilidad ("¿puedo permitirme X?")**: se evalúa X contra el presupuesto restante del mes
  y/o el neto disponible del mes (FR-021a); nunca contra un saldo bancario (no se modela).
- **Alternativas consideradas**:
  - Function-calling / tool-use con Gemini para que el modelo pida los cálculos: más elegante y una
    evolución natural (roadmap), pero añade complejidad. Para la demo basta el pipeline
    calcular→contexto→redactar. Se deja como mejora futura.

## D6. Privacidad: qué se envía a Gemini y política de logs

- **Decisión (envío mínimo)**: a Gemini solo se envía (a) para categorizar: la **descripción/comercio**
  y la lista de nombres de categorías; (b) para el chat: la pregunta del usuario y un **resumen
  agregado** ya calculado (p. ej. "gasto en Comida en 2026-07 = 320000 COP; presupuesto = 400000"),
  no volcados masivos de transacciones crudas.
- **Decisión (logs)**: logging estructurado que registra solo metadatos no sensibles (tipo de
  operación, códigos de error, latencias, conteos). Está **prohibido** loggear `amount_minor`,
  descripciones o el texto de la pregunta del chat. Un helper de logging centraliza esta política.
- **Rationale**: Principio II. La constitución permite el envío mínimo a un tercero si es explícito y
  documentado; esto lo documenta.
- **Alternativas consideradas**: procesar el lenguaje 100% local (sin Gemini) — fuera de alcance para
  una demo cuyo diferenciador es la IA; se mitiga minimizando el payload.

## D7. Importación CSV/Excel con pandas

- **Decisión**: `services/importer.py` usa `pandas.read_csv` / `read_excel` (con `openpyxl`).
  Detecta columnas candidatas (fecha, descripción, monto) por nombre; si es ambiguo, devuelve las
  columnas para que el usuario confirme el **mapeo** antes de confirmar la importación. Valida fila a
  fila; las inválidas se **omiten y se reportan**; nunca hay carga parcial silenciosa.
- **Duplicados**: se marca duplicado la coincidencia **exacta de fecha + monto + descripción** contra
  transacciones existentes (Clarificación Q4); se advierte antes de confirmar.
- **Flujo en dos pasos**: `POST /import/preview` (analiza, propone mapeo, marca inválidas y duplicados)
  → `POST /import/commit` (inserta las filas confirmadas). Evita efectos colaterales al explorar.
- **Rationale**: cumple FR-023..FR-026 y el Principio V. El parseo de montos/fechas se centraliza en
  `money.py`/utilidades y es testeable.
- **Alternativas consideradas**: parseo manual de CSV sin pandas — más código para Excel; el usuario
  pidió pandas explícitamente.

## D8. Datos de ejemplo (seed) y reset

- **Decisión**: `services/seed.py` genera ~3 meses de transacciones ficticias deterministas (ingresos
  recurrentes + gastos variados por categoría), más algunos presupuestos y una meta con aportes.
  `scripts/seed.py` lo ejecuta por CLI. `admin.py` expone `reset` (borra todo, con confirmación en el
  cliente) y `reseed` (recarga el ejemplo). Al arrancar con BD vacía, se siembra automáticamente
  (FR-027).
- **Rationale**: SC-001/SC-008. Datos deterministas hacen la demo reproducible y los tests estables.
- **Nota sobre reproducibilidad**: la generación usa una semilla fija y fechas ancladas al mes actual
  del sistema (los ~3 meses previos), para que "este mes" siempre tenga contenido.

## D9. Ejecución con dos comandos (sin Docker)

- **Decisión**: backend `uvicorn app.main:app --reload` (desde `backend/`); frontend `npm run dev`
  (desde `frontend/`, Vite). CORS habilitado en el backend para el origen de Vite. El frontend lee
  `VITE_API_BASE_URL`.
- **Rationale**: requisito explícito de simplicidad; sin orquestación.
- **Alternativas consideradas**: un `Makefile`/script único que levante ambos — opcional; no se exige.

## D10. Contrato de API y formato de errores

- **Decisión**: API REST JSON documentada en `contracts/openapi.yaml`. Errores con forma uniforme
  `{ "error": { "code": "...", "message": "...", "details": [...] } }`; nunca incluyen montos ni
  descripciones sensibles. Validación de entrada con Pydantic (422 con mensajes claros).
- **Rationale**: Principios IV y V; permite al frontend mostrar mensajes claros y trazables.
- **Alternativas consideradas**: GraphQL — innecesario para el alcance; REST es más simple.

---

**Resultado Fase 0**: todas las decisiones resueltas; sin incógnitas pendientes. Listo para Fase 1.
