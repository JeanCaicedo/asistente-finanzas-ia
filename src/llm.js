import "dotenv/config";

// Adaptador de proveedor LLM.
//
// El resto del proyecto (categorizar.js, y luego el agente) NO sabe qué modelo
// hay detrás. Solo llama a generarJSON() con un JSON Schema estándar y recibe
// datos validados. Cambiar de Gemini a Claude es cambiar LLM_PROVIDER en .env,
// sin tocar la lógica de negocio.
//
// Formato común de salida: { datos, usage: { input_tokens, output_tokens }, modelo }
// Formato común de entrada: un JSON Schema estándar (el que ya usa Claude).

const PROVEEDOR = (process.env.LLM_PROVIDER || "gemini").toLowerCase();

/**
 * Genera una respuesta JSON validada contra un esquema, con el proveedor activo.
 * @param {object} opts
 * @param {string} opts.system   - instrucciones de sistema
 * @param {string} opts.prompt   - mensaje del usuario
 * @param {object} opts.schema   - JSON Schema estándar de la salida esperada
 * @param {number} [opts.maxTokens=500]
 * @returns {Promise<{datos: object, usage: object, modelo: string}>}
 */
export async function generarJSON(opts) {
  if (PROVEEDOR === "gemini") return generarJSONGemini(opts);
  if (PROVEEDOR === "claude") return generarJSONClaude(opts);
  throw new Error(`LLM_PROVIDER desconocido: "${PROVEEDOR}". Usa "gemini" o "claude" en tu .env.`);
}

// --- Gemini (gratis, https://aistudio.google.com/apikey) ---
async function generarJSONGemini({ system, prompt, schema, maxTokens = 500 }) {
  if (!process.env.GEMINI_API_KEY) {
    throw new Error("Falta GEMINI_API_KEY. Consíguela gratis en https://aistudio.google.com/apikey");
  }
  // Importación diferida: solo se carga el SDK del proveedor que realmente usas.
  const { GoogleGenAI } = await import("@google/genai");
  const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
  const modelo = process.env.GEMINI_MODEL || "gemini-2.5-flash";

  const res = await ai.models.generateContent({
    model: modelo,
    contents: prompt,
    config: {
      systemInstruction: system,
      responseMimeType: "application/json",
      responseSchema: jsonSchemaAGemini(schema),
      maxOutputTokens: maxTokens,
      // gemini-2.5-flash razona ("thinking") por defecto y esos tokens se
      // comen el presupuesto de salida. Para extracción estructurada no hace
      // falta, así que lo desactivamos: más rápido, más barato y sin truncar.
      thinkingConfig: { thinkingBudget: 0 },
    },
  });

  return {
    datos: JSON.parse(res.text),
    usage: {
      input_tokens: res.usageMetadata?.promptTokenCount,
      output_tokens: res.usageMetadata?.candidatesTokenCount,
    },
    modelo,
  };
}

// --- Claude (cuando tengas saldo en https://console.anthropic.com) ---
async function generarJSONClaude({ system, prompt, schema, maxTokens = 500 }) {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error("Falta ANTHROPIC_API_KEY. Copia .env.example a .env y agrega tu clave.");
  }
  const { default: Anthropic } = await import("@anthropic-ai/sdk");
  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
  const modelo = process.env.CLAUDE_MODEL || "claude-sonnet-5";

  const res = await client.messages.create({
    model: modelo,
    max_tokens: maxTokens,
    system,
    // Claude consume el JSON Schema estándar tal cual, sin traducción.
    output_config: { format: { type: "json_schema", schema } },
    messages: [{ role: "user", content: prompt }],
  });

  const bloque = res.content.find((b) => b.type === "text");
  if (!bloque) throw new Error("La respuesta de Claude no contenía texto JSON.");

  return {
    datos: JSON.parse(bloque.text),
    usage: {
      input_tokens: res.usage.input_tokens,
      output_tokens: res.usage.output_tokens,
    },
    modelo: res.model,
  };
}

// Traduce un JSON Schema estándar al dialecto que espera Gemini (responseSchema).
// Diferencias que resolvemos aquí:
//   - Tipos en MAYÚSCULA: "string" -> "STRING"
//   - Nullable: type ["string","null"] -> type "STRING" + nullable: true
//   - Gemini ignora additionalProperties (lo omitimos)
//   - propertyOrdering ayuda a que respete el orden de los campos
function jsonSchemaAGemini(schema) {
  const TIPOS = {
    string: "STRING",
    number: "NUMBER",
    integer: "INTEGER",
    boolean: "BOOLEAN",
    object: "OBJECT",
    array: "ARRAY",
  };

  function convertir(nodo) {
    const out = {};
    let tipo = nodo.type;

    if (Array.isArray(tipo)) {
      out.nullable = tipo.includes("null");
      tipo = tipo.find((t) => t !== "null");
    }
    if (tipo) out.type = TIPOS[tipo] || String(tipo).toUpperCase();
    if (nodo.description) out.description = nodo.description;
    if (nodo.enum) out.enum = nodo.enum;

    if (nodo.properties) {
      out.properties = {};
      for (const [clave, valor] of Object.entries(nodo.properties)) {
        out.properties[clave] = convertir(valor);
      }
      if (nodo.required) {
        out.required = nodo.required;
        out.propertyOrdering = nodo.required;
      }
    }
    if (nodo.items) out.items = convertir(nodo.items);
    return out;
  }

  return convertir(schema);
}
