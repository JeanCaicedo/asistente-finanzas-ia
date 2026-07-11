# Asistente de Finanzas IA (Demo)

Demo de finanzas personales de un solo usuario (sin login) con datos de ejemplo
precargados (~3 meses). **Backend Python/FastAPI + SQLite** concentra TODA la lógica de
cálculo financiero (totales, presupuestos, metas) de forma determinista y con tests en
pytest; la IA (**Google Gemini**, clave por entorno) solo sugiere categorías y redacta las
respuestas del chat — **nunca calcula cifras**. Frontend en **React + Vite + TypeScript**
con Recharts. Degradación controlada si Gemini falla o no hay clave.

Especificación completa en [`specs/001-finance-assistant/`](specs/001-finance-assistant/)
(spec, plan, contratos OpenAPI, data-model, quickstart).

## Características

- Registro, listado, edición y borrado de transacciones con datos de ejemplo precargados.
- Categorización automática con IA (con confianza) y **fallback determinista por palabras
  clave**; la corrección del usuario siempre prevalece.
- Dashboard con gasto por categoría, ingresos vs gastos y tendencia del neto; cada cifra
  es **trazable** (drill-down a las transacciones que la componen) y la suma por categoría
  cuadra con el total.
- Presupuestos mensuales con alertas (cerca del 80% / excedido) y metas de ahorro con
  aportes manuales.
- Chat en lenguaje natural cuyas cifras coinciden exactamente con el dashboard y citan sus
  fuentes; degradación explícita si no hay IA.
- Importación CSV/Excel con mapeo de columnas, validación fila a fila y aviso de duplicados.
- Precisión exacta de dinero: montos como **enteros en unidades menores (céntimos)**, nunca
  `float`. El frontend nunca hace aritmética; solo formatea.

## Requisitos

- Python 3.11+ (probado con 3.14)
- Node.js 18+
- (Opcional) Clave gratis de Gemini: https://aistudio.google.com/apikey — sin ella la app
  funciona igual (categorización por fallback y chat en modo degradado).

## Arranque (dos comandos)

### 1) Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate  |  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # opcional: pon GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

Al primer arranque la BD (`backend/data/finanzas.db`) se crea y **se siembra
automáticamente** con ~3 meses de datos de ejemplo.

### 2) Frontend (otra terminal)

```bash
cd frontend
npm install
cp .env.example .env        # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Abre el frontend (Vite suele servir en http://localhost:5173).

## Variables de entorno

`backend/.env`:

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `GEMINI_API_KEY` | Clave de Gemini (vacío ⇒ chat degradado + fallback de categorías) | — |
| `GEMINI_MODEL` | Modelo de Gemini | `gemini-2.5-flash` |
| `DEFAULT_CURRENCY` | Moneda única de la demo (ISO 4217) | `COP` |
| `DB_PATH` | Ruta del archivo SQLite | `backend/data/finanzas.db` |

`frontend/.env`: `VITE_API_BASE_URL` (URL del backend).

## Pruebas

```bash
cd backend && pytest -q
```

Cubre utilidades de dinero, cálculos financieros (totales, presupuestos, metas), reportes,
fallback de categorización, importación, chat y privacidad de logs.

## Sembrar / reiniciar datos

```bash
cd backend && python -m scripts.seed          # siembra datos de ejemplo
cd backend && python -m scripts.seed --reset  # borra datos de usuario y re-siembra
```

Desde la UI: **"Recargar datos de ejemplo"** y **"Empezar de cero"** (en Transacciones).

## Arquitectura

```
backend/app/
  money.py, config.py, db.py, schemas.py, errors.py, logging_util.py
  repositories/   # acceso a datos (SQL explícito, sin ORM)
  services/       # finance.py (CÁLCULOS puros y testeados), reports, categorize, chat, importer, seed
  llm/gemini.py   # adaptador de IA (degrada sin lanzar)
  routers/        # endpoints FastAPI
frontend/src/
  api/client.ts, lib/format.ts (solo presentación), types.ts
  pages/          # Dashboard, Transactions, Budgets, ImportPage, Chat
```

Separación deliberada de cálculo (`services/finance.py`), acceso a datos (`repositories/`)
e IA (`llm/gemini.py`) para cumplir precisión y testabilidad.

## Prototipo previo (Node.js)

El directorio `src/` conserva el prototipo Node original (adaptador `llm.js` y
`categorizar.js`) como referencia histórica; no se extiende. El backend activo es Python.
