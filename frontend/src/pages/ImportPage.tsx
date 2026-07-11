import { useRef, useState } from "react";
import { api, ApiRequestError } from "../api/client";
import { Icon } from "../components/Icon";
import { useToast } from "../components/ui";
import { formatMoney } from "../lib/format";
import type { ImportPreview, ImportResult } from "../types";

export default function ImportPage() {
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [fileName, setFileName] = useState("");
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    setResult(null);
    setFileName(file.name);
    setBusy(true);
    try {
      setPreview(await api.importPreview(file));
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "No se pudo leer el archivo.");
      setPreview(null);
    } finally {
      setBusy(false);
    }
  }

  async function commit() {
    if (!preview) return;
    setBusy(true);
    setError("");
    try {
      const res = await api.importCommit(preview.valid_rows, skipDuplicates);
      setResult(res);
      setPreview(null);
      setFileName("");
      if (inputRef.current) inputRef.current.value = "";
      toast(`Importación completada: ${res.created_count} creada(s).`, "success");
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "No se pudo importar.");
    } finally {
      setBusy(false);
    }
  }

  const dupIndexes = new Set((preview?.possible_duplicates ?? []).map((d) => d.row_index));

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-icon">
          <Icon name="import" size={17} />
        </span>
        <h2>Importar movimientos (CSV / Excel)</h2>
      </div>
      <p className="hint" style={{ marginBottom: 16 }}>
        Sube un archivo con columnas de fecha, descripción y monto. Se propondrá un mapeo, se marcarán
        filas inválidas y posibles duplicados. Nada se guarda hasta confirmar.
      </p>

      {/* Dropzone */}
      <label
        className="dropzone"
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 8,
          padding: "28px 20px",
          border: "1.5px dashed var(--border)",
          borderRadius: 14,
          background: "var(--surface-2)",
          cursor: busy ? "wait" : "pointer",
          textAlign: "center",
        }}
      >
        <span className="card-icon" style={{ width: 44, height: 44 }}>
          <Icon name="import" size={22} />
        </span>
        <strong>{fileName || "Selecciona o arrastra un archivo"}</strong>
        <span className="hint">Formatos: .csv, .xlsx, .xls</span>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={onFile}
          disabled={busy}
          style={{ display: "none" }}
        />
      </label>

      {error && (
        <div className="error-msg">
          <Icon name="alert" size={15} /> {error}
        </div>
      )}

      {result && (
        <div className="tile" style={{ marginTop: 16, borderLeft: "3px solid var(--income)" }}>
          <div className="row-between">
            <strong style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
              <Icon name="check" size={17} /> Importación completada
            </strong>
          </div>
          <div className="hint" style={{ marginTop: 6 }}>
            Creadas: {result.created_count} · Omitidas: {result.skipped_count}
          </div>
          {result.skipped.length > 0 && (
            <ul className="hint" style={{ marginTop: 8, paddingLeft: 18 }}>
              {result.skipped.map((s, i) => (
                <li key={i}>
                  Fila {s.row_index}: {s.reason}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {preview && (
        <div style={{ marginTop: 20 }}>
          <div className="tile" style={{ marginBottom: 16 }}>
            <strong>Mapeo propuesto</strong>
            <div className="hint" style={{ marginTop: 6 }}>
              Fecha <code>{preview.proposed_mapping.date ?? "—"}</code> · Descripción{" "}
              <code>{preview.proposed_mapping.description ?? "—"}</code> · Monto{" "}
              <code>{preview.proposed_mapping.amount ?? "—"}</code>
            </div>
            <div className="hint" style={{ marginTop: 4 }}>
              Columnas detectadas: {preview.columns.join(", ")}
            </div>
          </div>

          <div className="grid grid-3">
            <div className="tile">
              <div className="tile-label">Filas válidas</div>
              <div className="tile-value" style={{ color: "var(--income)" }}>{preview.valid_rows.length}</div>
            </div>
            <div className="tile">
              <div className="tile-label">Filas inválidas</div>
              <div className="tile-value" style={{ color: "var(--expense)" }}>{preview.invalid_rows.length}</div>
            </div>
            <div className="tile">
              <div className="tile-label">Posibles duplicados</div>
              <div className="tile-value" style={{ color: "var(--warn)" }}>{preview.possible_duplicates.length}</div>
            </div>
          </div>

          {preview.invalid_rows.length > 0 && (
            <div className="tile" style={{ marginTop: 16, borderLeft: "3px solid var(--expense)" }}>
              <strong>Filas omitidas</strong>
              <ul className="hint" style={{ marginTop: 8, paddingLeft: 18 }}>
                {preview.invalid_rows.map((r, i) => (
                  <li key={i}>
                    Fila {r.row_index}: {r.reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="table-wrap" style={{ marginTop: 16 }}>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Fecha</th>
                  <th>Descripción</th>
                  <th className="num">Monto</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {preview.valid_rows.map((r, i) => (
                  <tr key={i}>
                    <td className="faint">{i}</td>
                    <td>{r.date}</td>
                    <td>{r.description || <span className="faint">—</span>}</td>
                    <td className="num">{formatMoney(r.amount_minor, r.currency)}</td>
                    <td>
                      {dupIndexes.has(i) ? (
                        <span className="badge near">Duplicado</span>
                      ) : (
                        <span className="badge ok">Nueva</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <label style={{ display: "flex", gap: 8, alignItems: "center", margin: "16px 0", fontSize: 14, color: "var(--text)" }}>
            <input
              type="checkbox"
              checked={skipDuplicates}
              onChange={(e) => setSkipDuplicates(e.target.checked)}
            />
            Omitir duplicados al importar
          </label>
          <button className="btn primary" onClick={commit} disabled={busy || preview.valid_rows.length === 0}>
            <Icon name="check" size={16} /> Confirmar importación ({preview.valid_rows.length} filas)
          </button>
        </div>
      )}
    </div>
  );
}
