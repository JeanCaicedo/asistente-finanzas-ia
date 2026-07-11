---
description: "Task list for Asistente de Finanzas Personales con IA (Demo)"
---

# Tasks: Asistente de Finanzas Personales con IA (Demo)

**Input**: Design documents from `specs/001-finance-assistant/`

**Prerequisites**: plan.md, spec.md (required); research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Se incluyen tareas de test para la lógica de cálculo del backend porque la **constitución v1.0.0
(Principio III)** lo exige y el plan las pide en pytest. No se genera suite obligatoria de frontend.

**Organization**: Tareas agrupadas por historia de usuario (US1–US6) para implementación y prueba
independientes. Prioridades del spec: US1=P1, US2=P2, US3=P2, US4=P3, US5=P3, US6=P4.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Puede ir en paralelo (archivo distinto, sin dependencias pendientes)
- **[Story]**: US1..US6; Setup/Foundational/Polish no llevan etiqueta de historia
- Rutas exactas incluidas en cada descripción

## Path Conventions

Monorepo web (plan.md): backend en `backend/`, frontend en `frontend/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización de proyectos backend y frontend.

- [X] T001 Crear estructura del backend (`backend/app/`, `backend/tests/unit/`, `backend/scripts/`, `backend/data/`) y `backend/requirements.txt` con fastapi, uvicorn, pydantic, pandas, openpyxl, google-genai, python-dotenv, pytest
- [X] T002 [P] Crear `backend/.env.example` (GEMINI_API_KEY vacío, GEMINI_MODEL) y `backend/app/config.py` que carga `.env` con python-dotenv (nunca hardcodear la clave)
- [X] T003 [P] Scaffolding del frontend en `frontend/` (Vite + React + TypeScript) con `frontend/package.json` incluyendo `recharts`
- [X] T004 [P] Crear `frontend/.env.example` (VITE_API_BASE_URL=http://localhost:8000), cliente base `frontend/src/api/client.ts`, formato de presentación `frontend/src/lib/format.ts` (céntimos→display, SIN sumas) y shell/routing en `frontend/src/App.tsx`
- [X] T005 [P] Añadir `backend/data/` y artefactos locales a `.gitignore` (no versionar `finanzas.db` ni `.env`)

**Checkpoint**: Ambos proyectos compilan/arrancan vacíos.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura central que DEBE existir antes de cualquier historia.

**⚠️ CRITICAL**: Ninguna historia puede empezar hasta completar esta fase.

- [X] T006 Implementar `backend/app/db.py`: conexión sqlite3 (`PRAGMA foreign_keys=ON`) e init del esquema completo (tablas Category, Transaction, Budget, SavingsGoal, GoalContribution con FKs, unicidades e índices) según `data-model.md`
- [X] T007 [P] Implementar utilidades de dinero en `backend/app/money.py` (parseo texto→céntimos, formato, aritmética entera exacta; nunca float)
- [X] T008 [P] Tests de dinero en `backend/tests/unit/test_money.py` (casos normal, límite, error: decimales, cero, negativos, no numérico)
- [X] T009 [P] Definir esquemas Pydantic base en `backend/app/schemas.py` (Transaction, Category, Budget, Goal, montos como enteros `*_minor` + `currency`) espejando `contracts/openapi.yaml`
- [X] T010 Manejo de errores y logging en `backend/app/main.py` + `backend/app/logging_util.py`: formato de error uniforme `{error:{code,message,details}}` y helper de logging que PROHÍBE montos/descripciones (Principio II, FR-030)
- [X] T011 [P] Adaptador de IA en `backend/app/llm/gemini.py`: lee env, selecciona modelo, y degrada de forma explícita (sin clave o fallo → resultado controlado, nunca excepción hacia el usuario)
- [X] T012 Repositorio de categorías `backend/app/repositories/categories.py` + sembrado de categorías del sistema (`is_system=1`: Comida, Transporte, Vivienda, Servicios, Ocio, Salud, Compras, Salario, Otros ingresos) al iniciar, y endpoint de solo lectura `GET /categories` en `backend/app/routers/categories.py` (US1 lo necesita para elegir categoría)
- [X] T013 App FastAPI en `backend/app/main.py`: CORS para el origen de Vite, registro de routers y endpoint `GET /health` (status + `ai_available`, sin exponer la clave)
- [X] T014 [P] Tipos TS espejo de los contratos en `frontend/src/types.ts` y navegación entre páginas (Dashboard, Transactions, Budgets, Import, Chat) en `frontend/src/App.tsx`

**Checkpoint**: Esquema, dinero, errores/logging, adaptador IA y navegación listos.

---

## Phase 3: User Story 1 - Ver y registrar mis finanzas desde el primer segundo (Priority: P1) 🎯 MVP

**Goal**: Registro/listado/edición/borrado de transacciones, datos de ejemplo precargados y reset/reseed.

**Independent Test**: Abrir la app y ver ~3 meses de datos; añadir/editar/borrar una transacción; "empezar de cero" → vacío; "recargar ejemplo" → vuelven los datos.

- [X] T015 [US1] Repositorio de transacciones `backend/app/repositories/transactions.py` (crear, listar con filtros mes/categoría/tipo, obtener, actualizar, borrar)
- [X] T016 [US1] Reglas de validación de transacción en `backend/app/services/finance.py` o `backend/app/schemas.py` (monto entero > 0, fecha válida, tipo income/expense; rechazo sin guardado parcial — FR-003)
- [X] T017 [US1] Funciones de totales en `backend/app/services/finance.py` (ingresos/gastos/neto por mes) usadas por lista y dashboard
- [X] T018 [P] [US1] Tests en `backend/tests/unit/test_finance.py` para totales mensuales (casos normal, mes vacío, límites de fin/inicio de mes)
- [X] T019 [US1] Router de transacciones `backend/app/routers/transactions.py` (`POST/GET/PATCH/DELETE /transactions`) conforme a `contracts/openapi.yaml`
- [X] T020 [US1] Generador de datos de ejemplo `backend/app/services/seed.py` (~3 meses deterministas: ingresos recurrentes + gastos variados, anclados al mes actual)
- [X] T021 [US1] CLI `backend/scripts/seed.py` y auto-sembrado en `db.py`/`main.py` cuando la BD está vacía (FR-027)
- [X] T022 [US1] Router admin `backend/app/routers/admin.py` (`POST /admin/reset`, `POST /admin/reseed`) que borra datos de usuario y recarga ejemplo (FR-028)
- [X] T023 [P] [US1] Página `frontend/src/pages/Transactions.tsx`: lista con filtros, alta/edición/borrado, mensajes de validación claros
- [X] T024 [P] [US1] Controles de "empezar de cero" (con confirmación) y "recargar datos de ejemplo" en `frontend/src/pages/Transactions.tsx` (o componente compartido)

**Checkpoint**: US1 funcional e independientemente testeable (MVP).

---

## Phase 4: User Story 2 - Categorización automática con IA, siempre corregible (Priority: P2)

**Goal**: Sugerencia de categoría por IA (con confianza), fallback por reglas, y corrección del usuario que prevalece.

**Independent Test**: Crear "Pago Rappi restaurante" → sugerencia de comida marcada como tal con confianza; cambiarla → persiste como confirmada por el usuario.

- [X] T025 [US2] Fallback determinista por palabras clave en `backend/app/services/categorize.py` (mapa comercio/keyword→categoría; sin match confiable → "Sin categorizar")
- [X] T026 [US2] Ruta IA en `backend/app/services/categorize.py` usando `llm/gemini.py` (salida JSON categoria+confianza; umbral 0.6; degrada al fallback)
- [X] T027 [P] [US2] Tests en `backend/tests/unit/test_categorize_fallback.py` (match por keyword, ambiguo→sin categorizar, sin clave→fallback)
- [X] T028 [US2] Integrar sugerencia en la creación de transacción (`routers/transactions.py` + `repositories/transactions.py`): asignar `category_status` (ai_suggested/user_confirmed/uncategorized) y `ai_confidence` (metadato, nunca en cálculos — FR-005..FR-007)
- [X] T029 [US2] Endpoints de categorías del usuario en `backend/app/routers/categories.py` (`POST /categories`, `DELETE /categories/{id}`: bloquear borrado de sistema=403; al borrar propia, reasignar transacciones a "Sin categorizar" — FR-008). El `GET /categories` ya existe desde T012.
- [X] T030 [P] [US2] UI en `frontend/src/pages/Transactions.tsx`: badge de sugerencia + confianza, distinción visual de categoría confirmada vs autogenerada, corrección en 1 acción (SC-005)
- [X] T031 [P] [US2] UI de gestión de categorías (crear/borrar propias) en `frontend/src/pages/` + componente en `frontend/src/components/`

**Checkpoint**: US2 funcional; corrección persiste y se refleja en reportes/presupuestos.

---

## Phase 5: User Story 3 - Dashboard con reportes claros (Priority: P2)

**Goal**: Gasto por categoría (cuadrado), evolución mensual ingresos vs gastos, tendencias; cada cifra trazable.

**Independent Test**: Con datos de ejemplo, la suma por categoría == total de gastos del mes; la serie muestra 3 meses correctos; inspeccionar una cifra revela sus transacciones.

- [X] T032 [US3] Agregación de gasto por categoría en `backend/app/services/reports.py` (consumiendo sumas puras de `finance.py`) con `transaction_ids` por item; garantizar suma(items)==total (FR-013/SC-002); agrupar "Sin categorizar"
- [X] T033 [US3] Serie mensual + tendencias en `backend/app/services/reports.py` (ingresos, gastos, neto por mes; variación entre meses), usando los totales puros de `finance.py`
- [X] T034 [P] [US3] Tests en `backend/tests/unit/test_reports.py` (igualdad suma==total, periodo vacío → estado vacío, trazabilidad de ids)
- [X] T035 [US3] Router de reportes `backend/app/routers/reports.py` (`GET /reports/by-category`, `GET /reports/monthly`)
- [X] T036 [P] [US3] `frontend/src/pages/Dashboard.tsx` con Recharts: gráfica gasto por categoría, ingresos vs gastos, tendencia
- [X] T037 [P] [US3] Drill-down (ver transacciones tras una cifra) y estados vacíos explícitos en `frontend/src/pages/Dashboard.tsx` (FR-016/FR-017)

**Checkpoint**: US3 funcional; cifras cuadran y son trazables.

---

## Phase 6: User Story 4 - Presupuestos y metas de ahorro con alertas (Priority: P3)

**Goal**: Presupuestos mensuales por categoría con alertas (cerca 80% / excedido) y metas con aportes manuales.

**Independent Test**: Presupuesto de comida → alerta "cerca" a ≥80% y "excedido" a >100%; meta con aporte manual → progreso sube.

- [X] T038 [US4] Repositorio y schemas de presupuestos `backend/app/repositories/budgets.py` (único por categoría+mes)
- [X] T039 [US4] Cálculo de progreso de presupuesto en `backend/app/services/finance.py` (spent, percent, status ok/near@80%/exceeded, over_by — FR-010/FR-011)
- [X] T040 [US4] Router de presupuestos `backend/app/routers/budgets.py` (`GET /budgets?year_month`, `POST`, `DELETE`)
- [X] T041 [US4] Repositorio de metas y aportes `backend/app/repositories/goals.py` (SavingsGoal + GoalContribution, cascada)
- [X] T042 [US4] Cálculo de progreso de meta en `backend/app/services/finance.py` (saved=suma aportes, percent, status in_progress/reached/overdue — FR-012)
- [X] T043 [P] [US4] Tests en `backend/tests/unit/test_finance.py` (umbral 80%, exceso, meta cumplida/vencida, presupuesto sin gasto=0%)
- [X] T044 [US4] Router de metas `backend/app/routers/goals.py` (`GET /goals`, `POST /goals`, `POST /goals/{id}/contributions`)
- [X] T045 [P] [US4] `frontend/src/pages/Budgets.tsx`: presupuestos con progreso y alertas visuales (cerca/excedido — SC-006)
- [X] T046 [P] [US4] UI de metas y aportes manuales en `frontend/src/pages/Budgets.tsx` (o componente en `frontend/src/components/`)

**Checkpoint**: US4 funcional; alertas y progreso de metas correctos.

---

## Phase 7: User Story 5 - Chat de IA anclado a mis datos reales (Priority: P3)

**Goal**: Preguntas en lenguaje natural respondidas con cifras calculadas determinísticamente y fuentes citadas.

**Independent Test**: "¿cuánto gasté en comida este mes?" → monto idéntico al dashboard, citando categoría y periodo; asequibilidad usa presupuesto restante/neto; sin IA → degradado.

- [X] T047 [US5] Parseo de intención en `backend/app/services/chat.py` (extraer categoría y periodo; mes en curso por defecto — FR-022; tipos: gasto por categoría / neto del mes / asequibilidad)
- [X] T048 [US5] Pipeline determinista en `backend/app/services/chat.py`: calcular cifras con `finance.py`, construir contexto mínimo + `citations`, lógica de asequibilidad (presupuesto restante y/o neto del mes — FR-021a) y `needs_input` cuando falte un dato (FR-021)
- [X] T049 [US5] Redacción con Gemini + degradación en `backend/app/services/chat.py` (la IA solo redacta; `degraded=true` si no disponible — FR-019)
- [X] T050 [P] [US5] Tests en `backend/tests/unit/test_chat.py` (cifra == reporte, cita fuentes, degradado sin clave, needs_input, fuera de alcance)
- [X] T051 [US5] Router de chat `backend/app/routers/chat.py` (`POST /chat`) devolviendo answer/citations/degraded/needs_input
- [X] T052 [P] [US5] `frontend/src/pages/Chat.tsx`: conversación + renderizado de citas y estado degradado

**Checkpoint**: US5 funcional; los números del chat coinciden con los reportes (SC-003).

---

## Phase 8: User Story 6 - Importar movimientos desde CSV/Excel (Priority: P4)

**Goal**: Importación con mapeo de columnas, validación fila a fila, categorización y aviso de duplicados.

**Independent Test**: Importar CSV con filas válidas, inválidas y duplicadas → preview correcto; commit crea solo válidas, sin cargas parciales.

- [X] T053 [US6] Lectura CSV/Excel en `backend/app/services/importer.py` (pandas + openpyxl; detección de columnas fecha/descripción/monto y mapeo propuesto — FR-023/FR-024)
- [X] T054 [US6] Validación de filas y detección de duplicados en `backend/app/services/importer.py` (inválidas omitidas y reportadas; duplicado = fecha+monto+descripción exactos — FR-025/FR-026)
- [X] T055 [P] [US6] Tests en `backend/tests/unit/test_importer.py` (mapeo, filas inválidas, duplicados, archivo corrupto→rechazo)
- [X] T056 [US6] Routers de importación `backend/app/routers/imports.py` (`POST /import/preview`, `POST /import/commit`) con categorización de filas vía `categorize.py`
- [X] T057 [P] [US6] `frontend/src/pages/ImportPage.tsx`: subida, confirmación de mapeo, reporte de inválidas/duplicados y commit

**Checkpoint**: US6 funcional; importación robusta sin cargas parciales.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Verificaciones transversales y cierre.

- [X] T058 [P] Test de privacidad de logs en `backend/tests/unit/test_logging_privacy.py`: tras ejercitar flujos, ningún log contiene montos ni descripciones (SC-009/FR-030)
- [X] T059 [P] Documentar arranque en dos comandos y variables `.env` en `README.md` (o `backend/README.md`/`frontend/README.md`)
- [X] T060 Ejecutar la guía `quickstart.md` (V1–V9) de extremo a extremo y corregir desviaciones
- [X] T061 [P] Repaso de consistencia de mensajes de error y edge cases (categoría borrada→Sin categorizar, límites de mes, meta vencida) en backend/frontend

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup; BLOQUEA todas las historias.
- **US1 (Phase 3)**: depende de Foundational. Es el MVP.
- **US2 (Phase 4)**: depende de Foundational + US1 (transacciones existen).
- **US3 (Phase 5)**: depende de Foundational + US1 (datos); se enriquece con US2.
- **US4 (Phase 6)**: depende de Foundational + US1 (gastos) + categorías (US2).
- **US5 (Phase 7)**: depende de US1/US3/US4 (cifras a citar).
- **US6 (Phase 8)**: depende de US1 (transacciones) + US2 (categorización de filas).
- **Polish (Phase 9)**: depende de las historias implementadas.

### Within Each User Story

- Repositorio/servicio (cálculo) → tests → router → UI.
- Los cálculos financieros MUST tener test antes de darse por terminados (Principio III).

### Parallel Opportunities

- Setup: T002, T003, T004, T005 en paralelo.
- Foundational: T007, T008, T009, T011, T014 en paralelo (tras T006).
- Dentro de cada historia, las tareas [P] (tests y UI de frontend) van en paralelo a la lógica de backend en archivos distintos.
- Con equipo: tras Foundational, US1 primero; luego US2 y US3 pueden avanzar en paralelo; US4 en paralelo a US5 una vez existan cálculos.

---

## Parallel Example: User Story 1

```bash
# Backend (secuencial por dependencias de archivo): T015 → T016 → T017 → T019 → T020 → T021 → T022
# En paralelo:
Tarea T018: "Tests de totales en backend/tests/unit/test_finance.py"
Tarea T023: "Página Transactions en frontend/src/pages/Transactions.tsx"
Tarea T024: "Controles reset/reseed en el frontend"
```

---

## Implementation Strategy

### MVP First (solo US1)

1. Fase 1 Setup → 2. Fase 2 Foundational → 3. Fase 3 US1.
4. **PARAR y VALIDAR**: abrir la app, ver datos de ejemplo, alta/edición/borrado, reset/reseed.
5. Demostrable como MVP.

### Incremental Delivery

US1 (MVP) → US2 (categorización) → US3 (dashboard) → US4 (presupuestos/metas) → US5 (chat) → US6 (import).
Cada historia añade valor sin romper las anteriores; validar de forma independiente en cada checkpoint.

### Notes

- [P] = archivos distintos, sin dependencias pendientes.
- Toda cifra de dinero se calcula en el backend con enteros; el frontend nunca suma.
- La IA (categorización/chat) siempre degrada de forma controlada; nunca bloquea el registro.
- Commit por tarea o grupo lógico; validar tests de cálculo antes de avanzar.
