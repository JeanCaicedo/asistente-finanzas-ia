import { generarJSON } from "./llm.js";

// Paso 2 del roadmap: categorización automática con salida JSON estructurada.
//
// La idea: recibimos texto libre (una línea de extracto bancario, una nota de
// gasto, lo que sea) y devolvemos SIEMPRE el mismo objeto JSON validado. Eso es
// lo que hace utilizable esto desde una API: la respuesta nunca es prosa, es
// un dato con forma fija que podrías guardar directo en Postgres.
//
// La llamada al modelo vive en ./llm.js (el adaptador), así que este archivo no
// sabe si detrás hay Gemini o Claude. Solo define QUÉ queremos: el esquema.

// Taxonomía de categorías. Es un enum cerrado a propósito: así el modelo no
// inventa categorías nuevas cada vez y tus reportes agregados quedan consistentes.
// Cuando conectes la base de datos, esta lista debería vivir en una tabla.
export const CATEGORIAS = [
  "Alimentación",
  "Transporte",
  "Vivienda",
  "Servicios", // luz, agua, internet, teléfono
  "Salud",
  "Entretenimiento",
  "Compras",
  "Educación",
  "Finanzas", // comisiones, intereses, transferencias
  "Ingresos",
  "Otros",
];

// El esquema de salida, en JSON Schema estándar. El adaptador lo traduce al
// formato de cada proveedor. Reglas que respetamos para máxima compatibilidad:
//   - additionalProperties: false (Claude lo exige; Gemini lo ignora)
//   - todos los campos en "required"
//   - "opcionales" se modelan como nullable (type: ["string", "null"])
export const ESQUEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    comercio: {
      type: "string",
      description: "Nombre del comercio o contraparte. Si no se identifica, 'Desconocido'.",
    },
    monto: {
      type: "number",
      description: "Valor de la transacción, siempre positivo.",
    },
    moneda: {
      type: "string",
      enum: ["COP", "USD", "EUR", "MXN", "ARS", "CLP", "PEN", "OTRA"],
      description: "Código de moneda. Usa 'OTRA' si no se puede determinar.",
    },
    tipo: {
      type: "string",
      enum: ["gasto", "ingreso"],
    },
    categoria: {
      type: "string",
      enum: CATEGORIAS,
    },
    subcategoria: {
      type: "string",
      description: "Etiqueta más específica y libre, p.ej. 'restaurante', 'gasolina', 'nómina'.",
    },
    fecha: {
      // nullable: si el texto no trae fecha, devuelve null en vez de inventarla.
      type: ["string", "null"],
      description: "Fecha en formato AAAA-MM-DD si aparece en el texto; si no, null.",
    },
    confianza: {
      type: "string",
      enum: ["alta", "media", "baja"],
      description: "Qué tan seguro está el modelo de la categorización.",
    },
    nota: {
      type: "string",
      description: "Explicación breve (una frase) de por qué se eligió esa categoría.",
    },
  },
  required: [
    "comercio",
    "monto",
    "moneda",
    "tipo",
    "categoria",
    "subcategoria",
    "fecha",
    "confianza",
    "nota",
  ],
};

const SYSTEM = `Eres un motor de categorización de transacciones financieras personales.
Recibes una descripción en lenguaje natural y devuelves los datos estructurados.
Reglas:
- 'monto' siempre positivo; el signo lo indica 'tipo' (gasto o ingreso).
- Elige la 'categoria' del enum que mejor represente el gasto/ingreso.
- Si el texto es ambiguo, usa 'confianza': "baja" y explícalo en 'nota'.
- No inventes fechas ni comercios: si no están, usa null / 'Desconocido'.`;

/**
 * Categoriza una transacción descrita en texto libre.
 * @param {string} descripcion - p.ej. "Rappi restaurante 45.000 el 3 de marzo"
 * @returns {Promise<{datos: object, usage: object, modelo: string}>}
 */
export async function categorizarTransaccion(descripcion) {
  return generarJSON({
    system: SYSTEM,
    prompt: descripcion,
    schema: ESQUEMA,
    maxTokens: 400,
  });
}

// --- Modo CLI: node src/categorizar.js "tu transacción aquí" ---
// Se ejecuta solo cuando llamas el archivo directamente, no cuando lo importas.
const esEjecucionDirecta = process.argv[1] && import.meta.url.endsWith(process.argv[1].replace(/\\/g, "/"));
if (esEjecucionDirecta) {
  const descripcion =
    process.argv[2] || "Pago Rappi restaurante $45.000 el 3 de marzo con tarjeta";

  categorizarTransaccion(descripcion)
    .then(({ datos, usage, modelo }) => {
      console.log("--- Transacción de entrada ---");
      console.log(descripcion);
      console.log(`\n--- Categorización (JSON estructurado · ${modelo}) ---`);
      console.log(JSON.stringify(datos, null, 2));
      console.log("\n--- Uso de tokens ---");
      console.log(usage);
    })
    .catch((err) => {
      console.error("Error categorizando:", err.message);
      process.exit(1);
    });
}
