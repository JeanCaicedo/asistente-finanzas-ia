import "dotenv/config";
import Anthropic from "@anthropic-ai/sdk";

if (!process.env.ANTHROPIC_API_KEY) {
  throw new Error("Falta ANTHROPIC_API_KEY. Copia .env.example a .env y agrega tu clave de https://console.anthropic.com");
}

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// Paso 1 del roadmap: una llamada basica al modelo, sin tools ni RAG todavia.
// Sirve para verificar que la API key funciona y para ver la forma real
// de la respuesta (content, usage) antes de construir algo mas complejo.
async function main() {
  const pregunta = process.argv[2] || "¿Cuánto es el 15% de propina sobre $48.500?";

  const response = await client.messages.create({
    model: "claude-sonnet-5",
    max_tokens: 200,
    system: "Eres un asistente financiero conciso. Responde en español, en pocas líneas.",
    messages: [{ role: "user", content: pregunta }],
  });

  console.log("--- Respuesta ---");
  console.log(response.content[0].text);
  console.log("\n--- Uso de tokens (asi se cobra) ---");
  console.log(response.usage);
}

main().catch((err) => {
  console.error("Error llamando a la API:", err.message);
  process.exit(1);
});
