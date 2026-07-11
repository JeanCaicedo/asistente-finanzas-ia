# Implementation Plan: Asistente de Finanzas Personales con IA (Demo)

**Branch**: `001-finance-assistant` | **Date**: 2026-07-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-finance-assistant/spec.md`

## Summary

Demo de finanzas personales de un solo usuario (sin login) con datos de ejemplo precargados
(~3 meses). Backend en **Python/FastAPI** con **SQLite** local que concentra TODA la lógica de
cálculo financiero (totales, presupuestos, progreso de metas) de forma determinista y con tests
en pytest; la IA (**Google Gemini**, clave por env) solo sugiere categorías y redacta las
respuestas del chat, nunca calcula cifras. Frontend en **React + Vite + TypeScript** con
**Recharts** para el dashboard. Importación CSV/Excel con **pandas**. Degradación controlada si
Gemini falla o no hay clave. Ejecutable con dos comandos (backend + frontend), sin Docker.

## Technical Context

**Language/Version**: Backend Python 3.11+ (FastAPI); Frontend TypeScript 5.x + React 18 (Vite 5)

**Primary Dependencies**:
- Backend: `fastapi`, `uvicorn`, `pydantic`, `pandas` + `openpyxl` (Excel), `google-genai` (Gemini),
  `python-dotenv`. Persistencia con el módulo estándar `sqlite3` (sin ORM).
- Frontend: `react`, `react-dom`, `recharts`; cliente HTTP con `fetch` nativo.
- Tests: `pytest` (backend). Frontend sin suite obligatoria en esta fase (validación manual/quickstart).

**Storage**: SQLite (archivo local `backend/data/finanzas.db`). Montos almacenados como **enteros en
unidades menores (céntimos)** para precisión exacta; nunca `float` para dinero.

**Testing**: `pytest` para toda la lógica de cálculo (servicio de finanzas), parsers de importación y
fallback de categorización. Objetivo: casos normal, límite y error por función de cálculo.

**Target Platform**: Escritorio/local del desarrollador (navegador para el frontend, API local FastAPI).

**Project Type**: Web (frontend + backend separados en un monorepo).

**Performance Goals**: App usable de inmediato con datos de ejemplo (SC-001: dashboard poblado < 5 s en
carga local). No hay metas de alta concurrencia (demo de un usuario).

**Constraints**:
- Sin autenticación, un solo usuario.
- Sin Docker ni microservicios; arranque con **dos comandos** (uno backend, uno frontend).
- Clave de Gemini SOLO desde variable de entorno (`.env`), nunca hardcodeada.
- El frontend NO hace aritmética de dinero: consume cifras ya calculadas por el backend.
- Sin datos financieros sensibles (montos, descripciones) en logs.

**Scale/Scope**: Demo de un usuario; miles de transacciones como máximo realista. 6 historias de
usuario (P1–P4), ~9 grupos de endpoints, 5 entidades de datos.

**Nota de contexto**: el repositorio contiene un prototipo previo en Node.js/ESM (Fases 1–2, incluido
`src/llm.js`). Este plan **pivota el backend a Python/FastAPI**; el código Node se conserva como
referencia histórica y no se extiende. El nuevo backend vive en `backend/`.

## Constitution Check

*GATE: Debe pasar antes de la investigación (Fase 0). Re-evaluado tras el diseño (Fase 1).*

Constitución v1.0.0 — evaluación de los 5 principios:

| Principio | Cumplimiento en este plan | Estado |
|-----------|---------------------------|--------|
| **I. Precisión sobre Velocidad** | Montos como enteros (céntimos); cálculos deterministas en el backend con enteros; la IA nunca es fuente de aritmética (FR-019); datos faltantes → el chat pide el dato. | ✅ PASS |
| **II. Privacidad** | SQLite local; clave en `.env`; a Gemini solo se envía el **mínimo contexto** (agregados/resúmenes necesarios), documentado en `research.md`; política de logging que prohíbe montos/descripciones. | ✅ PASS |
| **III. Código Simple y Testeable** | Sin ORM pesado (stdlib `sqlite3`); lógica de cálculo aislada en `services/finance.py` testeable sin red; acceso a IA vía adaptador `llm/gemini.py`; sin Docker; dos comandos. | ✅ PASS |
| **IV. Trazabilidad de Cada Número** | Los endpoints de reportes devuelven el desglose y las transacciones/periodo que componen cada cifra; el chat cita fuentes (FR-016, FR-020). | ✅ PASS |
| **V. Manejo Explícito de Errores** | Validación Pydantic + reglas de dominio; fallback explícito de Gemini (mensaje claro, "Sin categorizar"); importación reporta filas inválidas sin cargas parciales; errores sin filtrar datos sensibles. | ✅ PASS |

**Resultado del gate**: PASS. No hay violaciones que justificar en Seguimiento de Complejidad.

*Punto de atención (no es violación)*: el chat envía contexto financiero agregado a un tercero
(Gemini). La constitución lo permite explícitamente si se envía el mínimo necesario y se documenta;
ver decisión en `research.md`. Si no hay clave, el chat degrada y no envía nada.

## Project Structure

### Documentation (this feature)

```text
specs/001-finance-assistant/
├── plan.md              # Este archivo (/speckit-plan)
├── research.md          # Fase 0 (/speckit-plan)
├── data-model.md        # Fase 1 (/speckit-plan)
├── quickstart.md        # Fase 1 (/speckit-plan)
├── contracts/           # Fase 1 (/speckit-plan) — contrato de la API HTTP
│   └── openapi.yaml
└── tasks.md             # Fase 2 (/speckit-tasks — NO lo crea /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py              # App FastAPI, CORS, registro de routers, manejador de errores
│   ├── config.py            # Carga de .env (GEMINI_API_KEY, rutas)
│   ├── db.py                # Conexión sqlite3, init de esquema, helpers
│   ├── schemas.py           # Modelos Pydantic (entrada/salida) — montos como enteros (céntimos)
│   ├── money.py             # Utilidades de dinero (parseo, formato, aritmética entera exacta)
│   ├── repositories/        # Acceso a datos (una función por operación, SQL explícito)
│   │   ├── transactions.py
│   │   ├── categories.py
│   │   ├── budgets.py
│   │   └── goals.py
│   ├── services/
│   │   ├── finance.py       # CÁLCULOS: totales, gasto por categoría, presupuestos, metas (PURO, testeado)
│   │   ├── reports.py       # Ensambla reportes del dashboard con trazabilidad
│   │   ├── categorize.py    # Gemini + fallback por palabras clave
│   │   ├── chat.py          # Arma contexto determinista, llama a Gemini, cita fuentes
│   │   ├── importer.py      # pandas CSV/Excel, mapeo de columnas, detección de duplicados
│   │   └── seed.py          # Generación de datos de ejemplo (~3 meses)
│   ├── llm/
│   │   └── gemini.py        # Adaptador de proveedor: lee env, degradación si falla/no hay clave
│   └── routers/
│       ├── transactions.py
│       ├── categories.py
│       ├── budgets.py
│       ├── goals.py
│       ├── reports.py
│       ├── imports.py
│       ├── chat.py
│       └── admin.py         # reset ("empezar de cero") y reseed ("recargar datos de ejemplo")
├── tests/
│   └── unit/
│       ├── test_money.py
│       ├── test_finance.py       # presupuestos, totales, progreso de metas
│       ├── test_categorize_fallback.py
│       └── test_importer.py
├── scripts/
│   └── seed.py              # CLI: siembra la BD con datos de ejemplo
├── requirements.txt
├── .env.example
└── data/                    # finanzas.db (git-ignored)

frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   └── client.ts        # Envoltura de fetch a la API del backend
│   ├── types.ts             # Tipos TS espejo de los contratos
│   ├── pages/
│   │   ├── Dashboard.tsx     # Recharts: gasto por categoría, ingresos vs gastos, tendencias
│   │   ├── Transactions.tsx  # Lista/alta/edición/borrado + corrección de categoría
│   │   ├── Budgets.tsx       # Presupuestos y metas con alertas visuales
│   │   ├── ImportPage.tsx    # Carga CSV/Excel + mapeo + reporte de filas
│   │   └── Chat.tsx          # Chat con IA + citación de fuentes
│   ├── components/           # Gráficas, tarjetas de presupuesto, badges de estado de categoría
│   └── lib/format.ts         # SOLO formato de presentación (céntimos→display), nunca sumas
├── package.json
├── vite.config.ts
└── .env.example              # VITE_API_BASE_URL

# Prototipo Node.js previo (referencia histórica, no se extiende)
src/                          # llm.js, categorizar.js (Fases 1–2)
```

**Structure Decision**: Aplicación web (Opción 2) en monorepo: `backend/` (Python/FastAPI/SQLite) y
`frontend/` (React/Vite/TS). Se separa deliberadamente el cálculo (`services/finance.py`, puro y
testeado) del acceso a datos (`repositories/`) y de la IA (`llm/gemini.py`), para cumplir los
principios de precisión y testabilidad. El prototipo Node en `src/` queda fuera del alcance activo.

## Complexity Tracking

> No aplica: el Constitution Check pasa sin violaciones. No se introduce complejidad que requiera
> justificación (sin ORM, sin Docker, sin capas extra más allá de repos/servicios/routers).
