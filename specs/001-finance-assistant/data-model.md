# Data Model: Asistente de Finanzas Personales con IA (Demo)

**Fase 1** — Entidades, atributos, reglas de validación y relaciones. Base de datos: **SQLite**.
Regla global de dinero: los montos se guardan como **enteros en unidades menores (céntimos)**
(`*_minor`), nunca `float`. Fechas en ISO-8601 (`YYYY-MM-DD`). Timestamps en UTC ISO-8601.

---

## Diagrama de relaciones (resumen)

```text
Category (1) ───< Transaction (N)
Category (1) ───< Budget (N)          [única por (category_id, year_month)]
SavingsGoal (1) ───< GoalContribution (N)
```

- Una **Transacción** pertenece a 0..1 **Categoría** (NULL = "Sin categorizar").
- Un **Presupuesto** pertenece a 1 **Categoría** y a un mes (`year_month`), único por par.
- Una **Meta de ahorro** tiene N **Aportes** (contribuciones manuales).
- No hay entidad Usuario (demo de un solo usuario, sin login).

---

## Entidad: Category

Agrupa transacciones, presupuestos y reportes. Puede ser del sistema (por defecto) o del usuario.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `id` | INTEGER PK | autoincremental |
| `name` | TEXT | requerido, único (case-insensitive), no vacío |
| `kind` | TEXT | `expense` \| `income` \| `both` (para clasificar; presupuestos solo aplican a `expense`/`both`) |
| `is_system` | INTEGER (bool) | `1` = del sistema (no borrable ni renombrable); `0` = del usuario |
| `color` | TEXT | opcional (hex) para gráficas |
| `created_at` | TEXT | timestamp UTC |

**Reglas / lifecycle**:
- Categorías del sistema iniciales (seed): Comida, Transporte, Vivienda, Servicios, Ocio, Salud,
  Compras, Salario, Otros ingresos, etc. `is_system=1`.
- El usuario puede **crear** categorías (`is_system=0`) y **borrar solo las propias**.
- Al **borrar** una categoría propia: las transacciones que la referencian se ponen a `NULL`
  ("Sin categorizar") y se borran/oquedan huérfanos sus presupuestos (borrado en cascada del
  presupuesto de esa categoría). (FR-008, Clarificación Q3.)
- Categoría inexistente/borrada nunca debe romper reportes (edge case): las cifras "Sin categorizar"
  se agrupan aparte.

## Entidad: Transaction

Un ingreso o gasto.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `id` | INTEGER PK | autoincremental |
| `type` | TEXT | `income` \| `expense`, requerido |
| `amount_minor` | INTEGER | requerido, **> 0** (el signo lo da `type`, no el monto) |
| `currency` | TEXT | ISO 4217 (p. ej. `COP`), requerido; moneda única en la demo |
| `date` | TEXT | `YYYY-MM-DD`, requerido, fecha válida |
| `description` | TEXT | opcional (puede venir vacía en importación) |
| `category_id` | INTEGER FK→Category | NULL = "Sin categorizar" |
| `category_status` | TEXT | `ai_suggested` \| `user_confirmed` \| `uncategorized` |
| `ai_confidence` | REAL | 0..1, NULL si no aplica; **solo metadato**, no interviene en cálculos |
| `source` | TEXT | `manual` \| `imported` |
| `created_at` | TEXT | timestamp UTC |
| `updated_at` | TEXT | timestamp UTC |

**Reglas / validación (FR-001..FR-004)**:
- `amount_minor` entero positivo; rechazar vacío/no numérico/≤0 con mensaje claro y sin guardar.
- `date` parseable y válida; se cuenta en el mes de su `date` (edge case fin/inicio de mes).
- Al aceptar una sugerencia → `category_status = user_confirmed`. Al elegir manualmente otra categoría
  → `user_confirmed` (prevalece sobre la IA, FR-006). Sin categoría confiable → `uncategorized`.
- `ai_confidence` es informativo (badge en UI); **nunca** se usa en sumas ni reportes (Principio I).

**Estados de `category_status`**:
```text
uncategorized ──(IA sugiere)──> ai_suggested ──(usuario acepta/cambia)──> user_confirmed
      ^                                                                        │
      └────────────────(usuario quita categoría / se borra la categoría)───────┘
```

## Entidad: Budget

Límite mensual de gasto por categoría.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `id` | INTEGER PK | autoincremental |
| `category_id` | INTEGER FK→Category | requerido; categoría de gasto |
| `year_month` | TEXT | `YYYY-MM`, requerido |
| `limit_minor` | INTEGER | requerido, **> 0** |
| `currency` | TEXT | ISO 4217 |
| `created_at` | TEXT | timestamp UTC |

**Reglas (FR-009..FR-011)**:
- **Único** por `(category_id, year_month)`.
- Derivados calculados en `services/finance.py` (no persistidos):
  - `spent_minor` = suma de transacciones `expense` de esa categoría en ese mes.
  - `percent` = `spent_minor / limit_minor` (calculado con enteros/racionales, sin float acumulado).
  - `status`: `ok` (< umbral), `near` (≥ umbral de cercanía, por defecto **80%**), `exceeded`
    (> 100%); `over_by_minor` = `max(0, spent_minor − limit_minor)`.

## Entidad: SavingsGoal

Meta de ahorro con aportes manuales (Clarificación Q1).

| Campo | Tipo | Reglas |
|-------|------|--------|
| `id` | INTEGER PK | autoincremental |
| `name` | TEXT | requerido, no vacío |
| `target_minor` | INTEGER | requerido, **> 0** |
| `currency` | TEXT | ISO 4217 |
| `target_date` | TEXT | `YYYY-MM-DD` opcional |
| `created_at` | TEXT | timestamp UTC |

**Reglas (FR-012)**:
- Derivados (no persistidos): `saved_minor` = suma de `GoalContribution.amount_minor`;
  `percent` = `saved_minor / target_minor`; `status`: `in_progress` \| `reached` (≥100%) \|
  `overdue` (pasó `target_date` sin alcanzar).
- El progreso es **independiente** de las transacciones de ingreso/gasto.

## Entidad: GoalContribution

Aporte manual a una meta.

| Campo | Tipo | Reglas |
|-------|------|--------|
| `id` | INTEGER PK | autoincremental |
| `goal_id` | INTEGER FK→SavingsGoal | requerido, borrado en cascada con la meta |
| `amount_minor` | INTEGER | requerido, **> 0** |
| `date` | TEXT | `YYYY-MM-DD`, requerido |
| `note` | TEXT | opcional |
| `created_at` | TEXT | timestamp UTC |

---

## Entidades transitorias (no persistidas)

- **ImportPreview**: resultado de analizar un archivo — mapeo de columnas propuesto, filas válidas,
  filas inválidas (con motivo) y filas marcadas como posibles duplicados. Se confirma y recién
  entonces se insertan las transacciones.
- **ChatQuery/ChatAnswer**: pregunta del usuario y respuesta redactada, con `citations` (lista de
  fuentes: categoría, periodo, ids de transacciones/presupuesto usados) y las cifras calculadas.
  Puede persistirse un historial ligero de chat opcional (no requerido por la spec).
- **ReportResult**: agregados del dashboard (gasto por categoría, serie mensual ingresos/gastos,
  tendencias) siempre acompañados de la información de trazabilidad (periodo y, bajo demanda, las
  transacciones que componen cada cifra).

## Índices sugeridos

- `Transaction(date)`, `Transaction(category_id)`, `Transaction(type)` — filtros y agregaciones.
- `Budget(category_id, year_month)` UNIQUE.
- `GoalContribution(goal_id)`.
- Índice único case-insensitive en `Category(name)`.

## Notas de integridad

- `PRAGMA foreign_keys = ON`.
- Borrado de categoría propia: `ON DELETE SET NULL` en `Transaction.category_id`; presupuestos de esa
  categoría se borran (regla de aplicación o `ON DELETE CASCADE`).
- Borrado de meta: `ON DELETE CASCADE` en `GoalContribution`.
- "Empezar de cero" (reset): trunca todas las tablas de datos del usuario (transacciones, categorías
  del usuario, presupuestos, metas, aportes); mantiene el esquema y las categorías del sistema.
