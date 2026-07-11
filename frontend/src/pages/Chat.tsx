import { useEffect, useRef, useState } from "react";
import { api, ApiRequestError } from "../api/client";
import { Icon } from "../components/Icon";
import { formatMoney } from "../lib/format";
import type { ChatAnswer } from "../types";

interface Msg {
  role: "user" | "bot";
  text: string;
  answer?: ChatAnswer;
}

const SUGGESTIONS = [
  "¿cuánto gasté en comida este mes?",
  "¿cuál es mi neto este mes?",
  "¿puedo permitirme un gasto de 300000 este mes?",
];

export default function Chat({ aiAvailable }: { aiAvailable: boolean }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function send(question: string) {
    if (!question.trim() || busy) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setBusy(true);
    try {
      const answer = await api.chat(question);
      setMessages((m) => [...m, { role: "bot", text: answer.answer, answer }]);
    } catch (err) {
      const text = err instanceof ApiRequestError ? err.message : "No se pudo responder.";
      setMessages((m) => [...m, { role: "bot", text }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card chat-card">
      <div className="card-header">
        <span className="card-icon">
          <Icon name="sparkles" size={17} />
        </span>
        <h2>Chat sobre tus finanzas</h2>
        {!aiAvailable && (
          <span className="pill off" style={{ marginLeft: "auto" }}>
            <span className="dot" /> modo degradado
          </span>
        )}
      </div>

      {!aiAvailable && (
        <p className="hint" style={{ marginBottom: 12 }}>
          IA no disponible: las cifras se calculan igual (deterministas) y la respuesta se muestra en
          modo degradado.
        </p>
      )}

      <div className="chat-log" ref={logRef}>
        {messages.length === 0 && (
          <div className="hint">
            Pregunta cosas como:
            <div className="suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} className="suggestion" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            {m.text}
            {m.answer?.degraded && (
              <div className="degraded-note">Respuesta degradada, sin IA.</div>
            )}
            {m.answer?.citations?.map((c, j) => (
              <div key={j} className="citation">
                {c.label}
                {c.amount_minor != null && <>: {formatMoney(c.amount_minor)}</>}
                {c.transaction_ids.length > 0 && <> · {c.transaction_ids.length} transacción(es)</>}
              </div>
            ))}
          </div>
        ))}
        {busy && (
          <div className="bubble bot typing">
            <TypingDots />
          </div>
        )}
      </div>

      <form
        className="chat-form"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escribe tu pregunta…"
          disabled={busy}
        />
        <button className="btn primary" type="submit" disabled={busy || !input.trim()}>
          <Icon name="send" size={16} /> Enviar
        </button>
      </form>
    </div>
  );
}

function TypingDots() {
  return (
    <span style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
      Pensando
      <span className="typing-dots">…</span>
    </span>
  );
}
