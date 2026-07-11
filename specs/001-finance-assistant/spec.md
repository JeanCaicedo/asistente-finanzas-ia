# Feature Specification: Asistente de Finanzas Personales con IA (Demo)

**Feature Branch**: `001-finance-assistant`

**Created**: 2026-07-10

**Status**: Draft

**Input**: User description: "Desarrolla un asistente de finanzas personales con IA, pensado como proyecto de portafolio/demo. El usuario registra sus gastos e ingresos de dos formas: entrada manual e importación de CSV/Excel del banco. Las transacciones se categorizan automáticamente con sugerencia de la IA, corregible por el usuario. Presupuestos mensuales por categoría y metas de ahorro con alertas visuales. Dashboard con reportes. Chat con IA en lenguaje natural sobre las finanzas, basado solo en datos reales y citando cada número. Sin login, demo de un solo usuario. Arranca con 3 meses de datos de ejemplo, con opción de borrarlos."

## Clarifications

### Session 2026-07-10

- Q: ¿De dónde sale el "monto ahorrado" de una meta de ahorro? → A: El usuario hace aportes
  manuales a la meta; cada aporte suma al progreso y la meta es independiente del flujo de
  transacciones (ingresos/gastos).
- Q: ¿Contra qué se evalúa "¿puedo permitirme X?" en el chat? → A: Contra el presupuesto restante
  del mes en curso (límites por categoría − gasto acumulado) y/o el neto disponible del mes
  (ingresos − gastos del mes); la respuesta cita el presupuesto y el periodo usados. No se modela
  un saldo de cuenta bancaria.
- Q: ¿Puede el usuario gestionar categorías propias? → A: Hay categorías por defecto del sistema
  (no borrables ni renombrables) y el usuario puede crear categorías propias; puede borrar las
  propias, y al hacerlo sus transacciones pasan a "Sin categorizar".
- Q: ¿Qué define un duplicado al importar? → A: Coincidencia exacta de fecha + monto + descripción
  con una transacción existente.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver y registrar mis finanzas desde el primer segundo (Priority: P1)

Quien abre la demo ve de inmediato una aplicación viva: tres meses de transacciones de
ejemplo ya cargadas. Puede listar y filtrar esas transacciones, registrar nuevas
manualmente (monto, fecha, categoría, descripción, tipo ingreso/gasto), editarlas y
borrarlas. En cualquier momento puede borrar todos los datos de ejemplo y empezar de cero,
o recargar los datos de ejemplo.

**Why this priority**: Es el cimiento. Sin un registro de transacciones fiable no existe
nada que categorizar, presupuestar, graficar ni consultar. Los datos precargados hacen que
la demo entregue valor visible al instante, sin que el evaluador tenga que teclear nada.

**Independent Test**: Abrir la app sin tocar nada y confirmar que aparecen ~3 meses de
transacciones; añadir una transacción manual y verla en la lista; editar su monto; borrarla;
usar "empezar de cero" y confirmar lista vacía; recargar datos de ejemplo.

**Acceptance Scenarios**:

1. **Given** una instalación nueva, **When** el usuario abre la app por primera vez, **Then**
   se muestran transacciones de ejemplo que abarcan los últimos 3 meses con ingresos y gastos
   en varias categorías.
2. **Given** la vista de transacciones, **When** el usuario registra un gasto con monto, fecha,
   categoría y descripción, **Then** la transacción aparece en la lista y queda reflejada en los
   totales.
3. **Given** una transacción existente, **When** el usuario edita su monto o categoría, **Then**
   el cambio persiste y los totales derivados se recalculan.
4. **Given** una transacción existente, **When** el usuario la elimina y confirma, **Then**
   desaparece de la lista y de los totales.
5. **Given** datos cargados, **When** el usuario elige "empezar de cero" y confirma, **Then**
   todas las transacciones, presupuestos y metas se borran y la app queda vacía.
6. **Given** una app vacía, **When** el usuario elige "recargar datos de ejemplo", **Then**
   vuelven a aparecer los 3 meses de datos ficticios.
7. **Given** un monto inválido (vacío, no numérico o negativo donde no corresponde), **When** el
   usuario intenta guardar, **Then** el sistema rechaza el guardado con un mensaje claro y no
   crea la transacción.

---

### User Story 2 - Categorización automática con IA, siempre corregible (Priority: P2)

Al registrar o importar una transacción, la IA sugiere una categoría a partir de la
descripción/comercio. La sugerencia se muestra como tal (no como hecho), con su nivel de
confianza, y el usuario puede aceptarla o cambiarla. La categoría elegida por el usuario
siempre prevalece.

**Why this priority**: Es el diferenciador de "IA" más visible sobre el registro base, pero
depende de que exista el registro (US1). La corrección manual es requisito de precisión y
control del usuario.

**Independent Test**: Crear una transacción "Pago Rappi restaurante" y verificar que se
sugiere una categoría de comida marcada como sugerencia con confianza; cambiarla manualmente
y confirmar que la corrección persiste y que futuras vistas muestran la categoría del usuario.

**Acceptance Scenarios**:

1. **Given** una nueva transacción con descripción reconocible, **When** se registra, **Then**
   la IA propone una categoría señalada explícitamente como sugerencia, con nivel de confianza
   visible.
2. **Given** una sugerencia de categoría, **When** el usuario la acepta, **Then** la transacción
   queda con esa categoría marcada como confirmada por el usuario.
3. **Given** una sugerencia de categoría, **When** el usuario elige otra categoría, **Then** se
   guarda la del usuario y se distingue de una categoría autogenerada.
4. **Given** una descripción ambigua o vacía, **When** la IA no alcanza confianza suficiente,
   **Then** la transacción queda como "Sin categorizar" en vez de asignar una categoría inventada.
5. **Given** el servicio de IA no está disponible, **When** se registra una transacción, **Then**
   esta se guarda igualmente como "Sin categorizar" y el usuario puede categorizarla a mano.

---

### User Story 3 - Dashboard con reportes claros (Priority: P2)

El usuario ve un dashboard con: gasto por categoría, evolución mensual de ingresos vs
gastos, y tendencias en el tiempo. Cada cifra es trazable: al inspeccionar un valor, el
usuario entiende qué transacciones y qué periodo lo componen.

**Why this priority**: Convierte los datos en comprensión y es el corazón visual de la demo.
Depende de US1 (datos) y se enriquece con US2 (categorías).

**Independent Test**: Con los datos de ejemplo, abrir el dashboard y verificar que la suma
del gasto por categoría coincide con el total de gastos del periodo, y que la serie mensual
muestra los 3 meses con ingresos y gastos correctos.

**Acceptance Scenarios**:

1. **Given** transacciones en varias categorías, **When** el usuario abre el reporte de gasto por
   categoría de un mes, **Then** ve el desglose y la suma de las categorías iguala el total de
   gastos de ese mes.
2. **Given** 3 meses de datos, **When** el usuario ve la evolución mensual, **Then** cada mes
   muestra ingresos y gastos totales correctos y el saldo neto del mes.
3. **Given** un valor del dashboard, **When** el usuario lo inspecciona (p. ej. lo selecciona o
   abre su detalle), **Then** puede ver el periodo y el conjunto de transacciones que lo componen.
4. **Given** un periodo sin transacciones, **When** el usuario abre el dashboard de ese periodo,
   **Then** se muestra un estado vacío explícito, no cifras en cero ambiguas ni errores.

---

### User Story 4 - Presupuestos y metas de ahorro con alertas (Priority: P3)

El usuario define presupuestos mensuales por categoría y metas de ahorro. La app muestra el
progreso contra cada presupuesto/meta y alerta visualmente cuando el gasto de una categoría
se acerca al límite o lo supera.

**Why this priority**: Aporta control activo del dinero; depende de US1 (gastos) y de las
categorías (US2), y se apoya en el dashboard (US3).

**Independent Test**: Definir un presupuesto de comida y registrar gastos hasta superar el
80% del límite (alerta de cercanía) y luego el 100% (alerta de exceso); crear una meta de
ahorro, registrar un aporte manual y ver el progreso actualizarse.

**Acceptance Scenarios**:

1. **Given** una categoría de gasto, **When** el usuario define un presupuesto mensual para ella,
   **Then** el sistema muestra gasto acumulado, límite y porcentaje consumido del mes en curso.
2. **Given** un presupuesto definido, **When** el gasto acumulado alcanza el umbral de cercanía,
   **Then** el sistema lo señala visualmente como "cerca del límite".
3. **Given** un presupuesto definido, **When** el gasto acumulado supera el límite, **Then** el
   sistema lo señala visualmente como "excedido" e indica en cuánto se pasó.
4. **Given** una meta de ahorro con monto objetivo y fecha, **When** el usuario registra un aporte
   manual a la meta, **Then** el progreso (suma de aportes vs objetivo y %) se actualiza; los aportes
   son independientes de las transacciones de ingreso/gasto.
5. **Given** un presupuesto sin gasto en el mes, **When** el usuario lo consulta, **Then** ve 0%
   consumido sin alertas.

---

### User Story 5 - Chat de IA anclado a mis datos reales (Priority: P3)

El usuario pregunta en lenguaje natural ("¿cuánto gasté en comida este mes?", "¿puedo
permitirme un gasto de X?") y recibe respuestas calculadas únicamente sobre sus datos
reales, citando de dónde sale cada número (categorías, periodo, transacciones o presupuestos
usados). El asistente nunca inventa cifras.

**Why this priority**: Es el mayor diferenciador de la demo, pero depende de que todo lo
anterior (datos, categorías, presupuestos) exista y sea correcto.

**Independent Test**: Preguntar "¿cuánto gasté en comida este mes?" y verificar que el monto
respondido coincide exactamente con la suma de gastos de esa categoría en el mes en el
dashboard, y que la respuesta cita el periodo y la categoría usados.

**Acceptance Scenarios**:

1. **Given** datos del usuario, **When** pregunta "¿cuánto gasté en [categoría] este mes?",
   **Then** la respuesta da un monto que coincide exactamente con el total real de esa categoría
   en ese mes y cita categoría y periodo.
2. **Given** una pregunta de asequibilidad ("¿puedo permitirme X?"), **When** el usuario la hace,
   **Then** la respuesta compara X contra el presupuesto restante del mes en curso (límites por
   categoría − gasto acumulado) y/o el neto disponible del mes (ingresos − gastos), y cita el
   presupuesto y periodo usados, sin afirmar certezas que no se derivan de los datos.
3. **Given** una pregunta cuya respuesta requiere un dato que no existe, **When** el usuario la hace,
   **Then** el asistente lo indica y pide el dato faltante en vez de inventar una cifra.
4. **Given** cualquier respuesta con números, **When** se muestra al usuario, **Then** incluye la
   procedencia de cada número (qué transacciones/categorías/periodo lo componen).
5. **Given** una pregunta fuera del alcance de sus finanzas, **When** el usuario la hace, **Then**
   el asistente aclara que solo responde sobre los datos financieros del usuario.

---

### User Story 6 - Importar movimientos desde CSV/Excel del banco (Priority: P4)

El usuario importa un archivo CSV o Excel exportado de su banco. La app interpreta las
columnas (fecha, descripción, monto), permite confirmar el mapeo si es ambiguo, categoriza
las filas con la IA y las incorpora como transacciones, informando de filas no importadas.

**Why this priority**: Acelera la carga de datos reales, pero es el flujo más complejo y
variable; el registro manual (US1) ya cubre la necesidad básica, por eso va al final.

**Independent Test**: Importar un CSV de ejemplo con varias filas y verificar que se crean
las transacciones correctas, que las filas inválidas se reportan y no se importan a medias,
y que los montos y fechas coinciden con el archivo.

**Acceptance Scenarios**:

1. **Given** un archivo CSV/Excel con columnas de fecha, descripción y monto, **When** el usuario
   lo importa, **Then** se crea una transacción por fila válida con esos valores.
2. **Given** columnas cuyo significado no es evidente, **When** el usuario importa, **Then** el
   sistema le permite confirmar/ajustar qué columna es fecha, descripción y monto antes de importar.
3. **Given** filas con datos inválidos (fecha o monto ilegibles), **When** se importa, **Then**
   esas filas se omiten y se reportan al usuario, y las válidas sí se importan.
4. **Given** un archivo con filas que coinciden exactamente en fecha, monto y descripción con
   transacciones existentes, **When** se importa, **Then** el sistema las marca como posibles
   duplicados y advierte antes de confirmarlas.
5. **Given** un archivo con formato no soportado o corrupto, **When** el usuario lo importa, **Then**
   el sistema lo rechaza con un mensaje claro sin crear transacciones parciales.

---

### Edge Cases

- **Monto y precisión**: montos con decimales, cero y valores grandes deben sumarse sin errores
  de redondeo; nunca se muestran cifras aproximadas de dinero.
- **Fechas**: transacciones a fin/inicio de mes deben contarse en el mes correcto; el "mes en
  curso" se calcula respecto a la fecha actual del sistema.
- **Categoría inexistente**: si una transacción referencia una categoría borrada, debe reasignarse
  a "Sin categorizar" en lugar de romper reportes.
- **IA no disponible / lenta**: la categorización y el chat degradan de forma controlada (guardar
  sin categoría, mensaje de error claro) sin bloquear el registro ni perder datos.
- **Reset durante uso**: "empezar de cero" pide confirmación y no deja datos huérfanos
  (presupuestos/metas sin transacciones).
- **Presupuesto de una categoría sin gastos** y **meta ya cumplida o vencida** deben mostrarse
  correctamente.
- **Chat ambiguo**: preguntas sin periodo ("¿cuánto gasté en comida?") deben asumir un periodo
  por defecto explícito (mes en curso) e indicarlo, o pedir aclaración.

## Requirements *(mandatory)*

### Functional Requirements

**Registro y gestión de transacciones**

- **FR-001**: El sistema MUST permitir registrar manualmente transacciones de tipo ingreso o gasto
  con monto, fecha, categoría y descripción.
- **FR-002**: El sistema MUST permitir listar, filtrar (al menos por mes/categoría/tipo), editar y
  eliminar transacciones.
- **FR-003**: El sistema MUST validar los datos de una transacción antes de guardar (monto numérico
  y con signo/tipo coherente, fecha válida) y rechazar los inválidos con un mensaje claro, sin
  guardar parcialmente.
- **FR-004**: El sistema MUST representar y operar los montos con precisión exacta (sin errores de
  coma flotante) y asociar a cada transacción su moneda.

**Categorización con IA**

- **FR-005**: El sistema MUST sugerir automáticamente una categoría para cada transacción a partir
  de su descripción/comercio, presentándola explícitamente como sugerencia con un nivel de confianza.
- **FR-006**: El usuario MUST poder aceptar o cambiar la categoría sugerida, y la elección del
  usuario MUST prevalecer y distinguirse de las categorías autogeneradas.
- **FR-007**: Cuando la confianza sea insuficiente o la IA no esté disponible, el sistema MUST dejar
  la transacción como "Sin categorizar" en lugar de asignar una categoría inventada.
- **FR-008**: El sistema MUST proveer categorías por defecto del sistema (no borrables ni
  renombrables) y MUST permitir al usuario crear categorías propias y borrar las propias. Al borrar
  una categoría propia, sus transacciones MUST reasignarse a "Sin categorizar". Las categorías se
  usan de forma consistente en registro, presupuestos y reportes.

**Presupuestos y metas**

- **FR-009**: El usuario MUST poder definir un presupuesto mensual por categoría.
- **FR-010**: El sistema MUST mostrar, por presupuesto, el gasto acumulado del mes en curso, el
  límite y el porcentaje consumido.
- **FR-011**: El sistema MUST alertar visualmente cuando el gasto de una categoría se acerca al
  límite (umbral de cercanía) y cuando lo supera, indicando el exceso.
- **FR-012**: El usuario MUST poder definir metas de ahorro (monto objetivo y, opcionalmente, fecha),
  registrar aportes manuales a cada meta, y ver el progreso (suma de aportes vs objetivo). Los aportes
  a metas son independientes de las transacciones de ingreso/gasto.

**Dashboard y reportes**

- **FR-013**: El sistema MUST mostrar un reporte de gasto por categoría para un periodo, cuya suma
  cuadre exactamente con el total de gastos del periodo.
- **FR-014**: El sistema MUST mostrar la evolución mensual de ingresos vs gastos y el saldo neto por
  mes.
- **FR-015**: El sistema MUST mostrar tendencias a lo largo del tiempo (p. ej. variación del gasto
  entre meses).
- **FR-016**: El sistema MUST permitir que cada cifra mostrada sea trazable a las transacciones y el
  periodo que la componen (transparencia del origen del número).
- **FR-017**: El sistema MUST mostrar estados vacíos explícitos cuando no haya datos para un periodo.

**Chat con IA**

- **FR-018**: El sistema MUST permitir preguntas en lenguaje natural sobre las finanzas del usuario
  y responder usando únicamente sus datos reales.
- **FR-019**: Toda cifra de una respuesta del chat MUST ser calculada de forma determinista sobre los
  datos reales (la IA no es la fuente de la aritmética) y MUST coincidir con lo que muestran los
  reportes para el mismo criterio.
- **FR-020**: Toda respuesta con números MUST citar su procedencia (categorías, periodo y/o
  transacciones o presupuestos usados).
- **FR-021**: Cuando falte un dato necesario para responder, el sistema MUST indicarlo y pedirlo en
  lugar de inventar una cifra; y MUST acotar sus respuestas al ámbito de las finanzas del usuario.
- **FR-021a**: Para preguntas de asequibilidad ("¿puedo permitirme X?"), el sistema MUST evaluar X
  contra el presupuesto restante del mes en curso y/o el neto disponible del mes (ingresos − gastos),
  citando el presupuesto y periodo usados. No se modela un saldo de cuenta bancaria.
- **FR-022**: Para preguntas sin periodo explícito, el sistema MUST asumir el mes en curso e
  indicarlo, o pedir aclaración.

**Importación CSV/Excel**

- **FR-023**: El sistema MUST permitir importar transacciones desde archivos CSV y Excel, creando una
  transacción por fila válida (fecha, descripción, monto).
- **FR-024**: El sistema MUST permitir al usuario confirmar/ajustar el mapeo de columnas cuando el
  formato no sea inequívoco.
- **FR-025**: El sistema MUST omitir y reportar las filas inválidas sin abortar la importación de las
  válidas, y MUST rechazar archivos corruptos/no soportados sin crear transacciones parciales.
- **FR-026**: El sistema MUST advertir de posibles transacciones duplicadas antes de confirmarlas,
  considerando duplicado a la coincidencia exacta de fecha + monto + descripción con una transacción
  existente.

**Datos de ejemplo y modo demo**

- **FR-027**: En una instalación nueva el sistema MUST arrancar con datos de ejemplo que cubran
  aproximadamente 3 meses de ingresos y gastos ficticios en varias categorías.
- **FR-028**: El usuario MUST poder borrar todos los datos ("empezar de cero", con confirmación) y
  poder recargar los datos de ejemplo.
- **FR-029**: El sistema MUST funcionar como una demo de un solo usuario, sin registro ni login.

**Privacidad y manejo de errores (transversal)**

- **FR-030**: El sistema MUST NOT registrar en logs montos, descripciones identificables ni otros
  datos financieros sensibles del usuario.
- **FR-031**: El sistema MUST manejar de forma explícita los fallos que afecten datos de dinero
  (parseo, IA, validación, importación), informando al usuario y sin continuar con valores por
  defecto no señalados.

### Key Entities *(include if feature involves data)*

- **Transacción**: un ingreso o gasto. Atributos: tipo (ingreso/gasto), monto (precisión exacta),
  moneda, fecha, descripción, categoría, origen (manual/importada), estado de categoría
  (sugerida por IA / confirmada por usuario / sin categorizar) y confianza de la sugerencia.
- **Categoría**: agrupador de transacciones (p. ej. comida, transporte, salario). Puede ser del
  sistema (por defecto, no borrable/renombrable) o propia del usuario (creable y borrable). Usada por
  transacciones, presupuestos y reportes.
- **Presupuesto**: límite mensual de gasto asociado a una categoría; base para el cálculo de
  progreso y alertas.
- **Meta de ahorro**: objetivo de monto a ahorrar, con fecha opcional. Tiene **aportes** (montos
  registrados manualmente por el usuario); el progreso es la suma de sus aportes. Independiente de
  las transacciones de ingreso/gasto.
- **Conjunto de datos de ejemplo**: transacciones (y presupuestos/metas) ficticios precargados que
  representan ~3 meses, borrables y recargables.
- **Consulta de chat**: pregunta del usuario en lenguaje natural y su respuesta, con las cifras
  calculadas y sus fuentes citadas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Al abrir la demo por primera vez, el usuario ve datos financieros reales funcionando
  (transacciones, dashboard poblado) en menos de 5 segundos y sin introducir ningún dato.
- **SC-002**: En el 100% de los casos, la suma del gasto por categoría de un periodo coincide
  exactamente con el total de gastos de ese periodo (sin discrepancias de redondeo).
- **SC-003**: En el 100% de las respuestas numéricas del chat, la cifra coincide exactamente con la
  del reporte correspondiente y se muestra la procedencia de cada número.
- **SC-004**: El usuario puede registrar manualmente una transacción completa en menos de 30 segundos.
- **SC-005**: El usuario puede corregir la categoría sugerida por la IA en 1 acción, y la corrección
  se refleja de inmediato en reportes y presupuestos.
- **SC-006**: Cuando un presupuesto se acerca (umbral) o supera el límite, la alerta visual aparece
  en el 100% de los casos correspondientes.
- **SC-007**: En la importación, el 100% de las filas inválidas se reportan y ninguna transacción se
  crea a medias; las filas válidas de un archivo bien formado se importan correctamente.
- **SC-008**: "Empezar de cero" deja el sistema sin datos residuales y "recargar datos de ejemplo"
  restaura los ~3 meses, ambos verificables en una sola acción.
- **SC-009**: Ninguna entrada de log contiene montos ni descripciones de transacciones (verificable
  inspeccionando los logs tras ejercitar los flujos principales).

## Assumptions

- **Un solo usuario, sin autenticación**: es una demo local; no hay cuentas, roles ni multiusuario.
  La privacidad se centra en no filtrar datos a logs ni a terceros más allá de lo mínimo para la IA.
- **Moneda única**: la demo opera en una sola moneda por defecto; se registra la moneda por
  transacción por consistencia, pero no se implementa conversión entre monedas en esta versión.
- **Umbral de "cerca del límite"**: por defecto 80% del presupuesto de la categoría (configurable a
  futuro; fijo en la demo).
- **Periodo por defecto del chat/reportes**: el mes calendario en curso respecto a la fecha del
  sistema, salvo que el usuario indique otro.
- **Formato de importación**: se asumen exportaciones bancarias tabulares con, al menos, columnas de
  fecha, descripción y monto; formatos muy exóticos pueden requerir el mapeo manual de columnas.
- **Datos de ejemplo**: son ficticios y no representan a ninguna persona real; incluyen variedad de
  categorías, ingresos recurrentes y gastos para que todos los reportes y alertas tengan contenido.
- **Categorías por defecto**: el sistema provee un conjunto inicial de categorías comunes (comida,
  transporte, vivienda, ocio, salario, etc.) que el usuario puede usar desde el inicio.
- **La IA sugiere y explica, pero no calcula**: la categorización y el lenguaje del chat usan IA; los
  totales, saldos y comparativas se calculan de forma determinista sobre los datos, conforme a los
  principios del proyecto.
- **Persistencia local**: los datos de la demo se guardan localmente entre sesiones (no se pierden al
  cerrar), salvo que el usuario elija "empezar de cero".
