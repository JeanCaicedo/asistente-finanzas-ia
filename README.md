# Asistente de Finanzas IA

Agente de IA que responde preguntas en lenguaje natural sobre finanzas personales: consulta de gastos, categorización automática y comparativas entre periodos, con soporte planificado para extracción de datos desde imágenes de recibos.

## Descripción

Proyecto orientado a la implementación de agentes de IA basados en LLMs, integrando técnicas de function-calling / tool-use y RAG (Retrieval-Augmented Generation) para conectar un modelo de lenguaje con datos financieros reales.

## Estado del proyecto

En desarrollo — Fase 2: categorización automática de transacciones con salida JSON estructurada y validada (`structured outputs`), reutilizable desde una futura API.

## Roadmap

- [x] Integración básica con la API (system prompt, mensajes, tokens)
- [x] Prompting estructurado con salida en formato JSON (categorización de transacciones)
- [ ] Function calling: consultas a una base de datos de gastos
- [ ] RAG con `pgvector` para consultas sobre historial extenso
- [ ] Arquitectura de agente con ciclo de tool-use
- [ ] Lectura de recibos por visión (imagen → JSON, sin OCR aparte)
- [ ] Consideraciones de seguridad y control de costos en producción

## Stack tecnológico

- Node.js
- Adaptador de proveedor LLM (`src/llm.js`): funciona con **Gemini** (gratis) o **Claude/Anthropic**, intercambiables vía `.env`
- SDKs: `@google/genai`, `@anthropic-ai/sdk`
- Planificado: Express/NestJS, PostgreSQL + `pgvector`

## Instalación

```bash
npm install
cp .env.example .env
```

Elige tu proveedor en `.env` con `LLM_PROVIDER`:

- **Gemini (gratis, sin tarjeta)** — `LLM_PROVIDER=gemini` y pon tu `GEMINI_API_KEY` de [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
- **Claude/Anthropic (pago por uso)** — `LLM_PROVIDER=claude` y pon tu `ANTHROPIC_API_KEY` de [console.anthropic.com](https://console.anthropic.com).

Cambiar de un proveedor a otro es solo cambiar esas variables; la lógica del proyecto no cambia.

## Uso

Llamada básica al modelo (Fase 1):

```bash
npm start
npm start -- "¿Cuánto gasté en enero?"
```

Categorización de una transacción a JSON estructurado (Fase 2):

```bash
npm run categorizar
npm run categorizar -- "Pago Rappi restaurante $45.000 el 3 de marzo con tarjeta"
```

Devuelve un objeto validado con `comercio`, `monto`, `moneda`, `tipo`,
`categoria`, `subcategoria`, `fecha`, `confianza` y `nota`. La función
`categorizarTransaccion()` en `src/categorizar.js` es reutilizable desde
código (será la base del function-calling de la Fase 3).
