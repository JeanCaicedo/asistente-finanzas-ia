# Quickstart & Validación: Asistente de Finanzas IA (Demo)

Guía para levantar la app con **dos comandos** y validar de extremo a extremo que la feature funciona.
Detalles de datos en [data-model.md](./data-model.md) y de la API en [contracts/openapi.yaml](./contracts/openapi.yaml).

## Prerrequisitos

- Python 3.11+
- Node.js 18+ (para Vite)
- (Opcional) Clave de Gemini del tier gratis desde https://aistudio.google.com/apikey
  - Sin clave, la app funciona igual: la categorización usa el fallback por palabras clave y el chat
    degrada con un mensaje claro.

## Configuración

```bash
# Backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate  |  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # editar y poner GEMINI_API_KEY si se dispone

# Frontend
cd ../frontend
npm install
cp .env.example .env        # VITE_API_BASE_URL=http://localhost:8000
```

`.env` del backend (nunca commitear):

```env
GEMINI_API_KEY=            # opcional; vacío => chat degradado + fallback de categorías
GEMINI_MODEL=gemini-2.0-flash
```

## Arranque (dos comandos)

```bash
# Terminal 1 — Backend (crea/siembra la BD si está vacía)
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Abrir el frontend (Vite suele servir en http://localhost:5173).
Al primer arranque, la BD se siembra automáticamente con ~3 meses de datos de ejemplo (FR-027).

## Escenarios de validación

Cada escenario mapea a historias de usuario y criterios de éxito de la spec.

### V1 — Arranque con datos de ejemplo (US1 / SC-001)
1. Abrir el frontend sin introducir nada.
2. **Esperado**: la lista de transacciones y el dashboard aparecen poblados (~3 meses) en < 5 s.

### V2 — Alta/edición/borrado manual (US1 / FR-001..FR-004)
1. Crear un gasto: monto, fecha, categoría, descripción.
2. **Esperado**: aparece en la lista y en los totales del mes.
3. Editar su monto → los totales se recalculan. Borrarlo → desaparece de lista y totales.
4. Intentar guardar un monto vacío/negativo → **rechazo con mensaje claro**, sin crear la transacción.

### V3 — Categorización IA corregible (US2 / FR-005..FR-007)
1. Crear "Pago Rappi restaurante".
2. **Esperado**: categoría sugerida (p. ej. Comida) marcada como **sugerencia** con confianza.
3. Cambiarla manualmente → queda **confirmada por el usuario** y persiste.
4. Sin clave de Gemini: la sugerencia proviene del **fallback** o queda "Sin categorizar" (nunca inventada).

### V4 — Dashboard con cifras cuadradas y trazables (US3 / FR-013/SC-002)
1. Abrir "gasto por categoría" del mes.
2. **Esperado**: la **suma de categorías == total de gastos** del mes (sin descuadres de redondeo).
3. Ver evolución mensual: 3 meses con ingresos, gastos y neto correctos.
4. Inspeccionar una cifra → muestra el periodo y las transacciones que la componen (FR-016).

### V5 — Presupuestos y metas con alertas (US4 / FR-009..FR-012, SC-006)
1. Definir un presupuesto de Comida.
2. Registrar gastos hasta ≥80% → estado **"cerca del límite"**; superar 100% → **"excedido"** con el exceso.
3. Crear una meta, registrar un **aporte manual** → el progreso sube (independiente de ingresos/gastos).

### V6 — Chat anclado a datos reales (US5 / FR-018..FR-022, SC-003)
1. Preguntar "¿cuánto gasté en comida este mes?".
2. **Esperado**: el monto **coincide exactamente** con V4 y la respuesta **cita** categoría y periodo.
3. Preguntar "¿puedo permitirme un gasto de X?" → responde comparando con presupuesto restante / neto
   del mes, citando fuentes; no inventa un saldo bancario.
4. Sin clave/Gemini caído → respuesta **degradada** con mensaje claro, sin romper la app.

### V7 — Importación CSV/Excel (US6 / FR-023..FR-026, SC-007)
1. Subir un CSV con filas válidas, alguna inválida y alguna duplicada (misma fecha+monto+descripción).
2. **Esperado** (preview): mapeo propuesto, filas inválidas listadas con motivo, duplicados marcados.
3. Confirmar → se crean solo las válidas; **ninguna carga parcial**; el reporte indica omitidas.

### V8 — Reset y reseed (US1 / FR-028, SC-008)
1. "Empezar de cero" (con confirmación) → app vacía, sin datos residuales.
2. "Recargar datos de ejemplo" → vuelven los ~3 meses.

### V9 — Privacidad en logs (FR-030 / SC-009)
1. Ejercitar V2–V7.
2. Inspeccionar la salida de logs del backend.
3. **Esperado**: **ningún** log contiene montos ni descripciones de transacciones (solo metadatos).

## Pruebas automatizadas (backend)

```bash
cd backend && pytest -q
```

Cubre (Principio III de la constitución): utilidades de dinero (`test_money.py`), cálculos de
finanzas — totales, gasto por categoría, presupuestos, progreso de metas (`test_finance.py`),
fallback de categorización (`test_categorize_fallback.py`) y parseo/duplicados de importación
(`test_importer.py`). Toda la lógica de cálculo se prueba con casos normal, límite y error.

## Comprobación rápida de la API

```bash
curl http://localhost:8000/health
# { "status": "ok", "ai_available": true|false }
```
