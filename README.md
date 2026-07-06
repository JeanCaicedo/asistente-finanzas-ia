# Asistente de Finanzas IA

Agente de IA que responde preguntas en lenguaje natural sobre finanzas personales: consulta de gastos, categorización automática y comparativas entre periodos, con soporte planificado para extracción de datos desde imágenes de recibos.

## Descripción

Proyecto orientado a la implementación de agentes de IA basados en LLMs, integrando técnicas de function-calling / tool-use y RAG (Retrieval-Augmented Generation) para conectar un modelo de lenguaje con datos financieros reales.

## Estado del proyecto

🟡 En desarrollo — Fase 1: integración básica con la API de Anthropic (envío de prompts, configuración de `system prompt` y verificación del formato de respuesta y consumo de tokens).

## Roadmap

- [x] Integración básica con la API (system prompt, mensajes, tokens)
- [ ] Prompting estructurado con salida en formato JSON
- [ ] Function calling: consultas a una base de datos de gastos
- [ ] RAG con `pgvector` para consultas sobre historial extenso
- [ ] Arquitectura de agente con ciclo de tool-use
- [ ] Consideraciones de seguridad y control de costos en producción

## Stack tecnológico

- Node.js
- Anthropic SDK (`@anthropic-ai/sdk`)
- Planificado: Express/NestJS, PostgreSQL + `pgvector`

## Instalación

```bash
npm install
cp .env.example .env
```

Configurar la variable `ANTHROPIC_API_KEY` en `.env` (clave disponible en [console.anthropic.com](https://console.anthropic.com)).

## Uso

```bash
npm start
npm start -- "¿Cuánto gasté en enero?"
```
