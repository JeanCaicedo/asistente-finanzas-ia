# Asistente de Finanzas IA

Agente de IA que responde preguntas en lenguaje natural sobre finanzas personales: gastos, categorías, comparativas entre meses, y (más adelante) lectura de recibos por foto.

## Por qué este proyecto

Proyecto de aprendizaje enfocado en ingeniería de agentes de IA (LLMs con function-calling/tool-use y RAG), construido paso a paso siguiendo un roadmap concreto en vez de un tutorial genérico de "chat con tu PDF".

## Estado actual

🟡 **Paso 1 del roadmap**: llamada básica a la API de Anthropic, sin tools ni base de datos todavía. Sirve para verificar que la integración funciona y entender la forma de la respuesta (`content`, `usage`) antes de construir el agente completo.

## Roadmap

- [x] 1. Llamada básica a la API (system prompt, mensajes, tokens)
- [ ] 2. Prompting estructurado (respuestas en JSON con formato fijo)
- [ ] 3. Function calling: el agente consulta una base de datos real de gastos
- [ ] 4. RAG con `pgvector` para preguntas sobre historial largo
- [ ] 5. Arquitectura de agente completa (loop de tool-use)
- [ ] 6. Seguridad y control de costos en producción

## Cómo correrlo

```bash
npm install
cp .env.example .env   # agrega tu ANTHROPIC_API_KEY (gratis en console.anthropic.com)
npm start                              # pregunta por defecto
npm start -- "¿cuánto gasté en enero?" # pregunta propia
```

## Stack

- Node.js + `@anthropic-ai/sdk`
- Próximamente: Express/NestJS para la API, PostgreSQL + `pgvector` para el historial de gastos
