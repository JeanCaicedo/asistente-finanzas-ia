// Primitivas de UI compartidas: tema (claro/oscuro), toasts y diálogos
// (confirmación / prompt) que reemplazan a los nativos alert/confirm/prompt.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Icon, type IconName } from "./Icon";

/* ---------------------------------- Tema ---------------------------------- */

export type Theme = "light" | "dark";

interface ThemeCtx {
  theme: Theme;
  toggle: () => void;
}
const ThemeContext = createContext<ThemeCtx>({ theme: "dark", toggle: () => {} });
export const useTheme = () => useContext(ThemeContext);

function readInitialTheme(): Theme {
  const attr = document.documentElement.getAttribute("data-theme");
  return attr === "light" ? "light" : "dark";
}

/* --------------------------------- Toasts --------------------------------- */

type ToastKind = "success" | "error" | "info";
interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}
const ToastContext = createContext<(message: string, kind?: ToastKind) => void>(() => {});
export const useToast = () => useContext(ToastContext);

/* ------------------------------- Confirmación ----------------------------- */

interface ConfirmOptions {
  title: string;
  message?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
}
interface PromptOptions {
  title: string;
  message?: string;
  label?: string;
  placeholder?: string;
  confirmLabel?: string;
  defaultValue?: string;
}
interface DialogCtx {
  confirm: (opts: ConfirmOptions) => Promise<boolean>;
  prompt: (opts: PromptOptions) => Promise<string | null>;
}
const DialogContext = createContext<DialogCtx>({
  confirm: async () => false,
  prompt: async () => null,
});
export const useConfirm = () => useContext(DialogContext).confirm;
export const usePrompt = () => useContext(DialogContext).prompt;

/* ----------------------------- Proveedor único ---------------------------- */

type DialogState =
  | { kind: "confirm"; opts: ConfirmOptions; resolve: (v: boolean) => void }
  | { kind: "prompt"; opts: PromptOptions; resolve: (v: string | null) => void }
  | null;

export function UiProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(readInitialTheme);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [dialog, setDialog] = useState<DialogState>(null);
  const [promptValue, setPromptValue] = useState("");
  const nextId = useRef(1);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("theme", theme);
    } catch {
      /* almacenamiento no disponible */
    }
  }, [theme]);

  const toggle = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);

  const pushToast = useCallback((message: string, kind: ToastKind = "info") => {
    const id = nextId.current++;
    setToasts((list) => [...list, { id, kind, message }]);
    setTimeout(() => setToasts((list) => list.filter((t) => t.id !== id)), 4200);
  }, []);

  const confirm = useCallback(
    (opts: ConfirmOptions) =>
      new Promise<boolean>((resolve) => setDialog({ kind: "confirm", opts, resolve })),
    [],
  );
  const prompt = useCallback(
    (opts: PromptOptions) =>
      new Promise<string | null>((resolve) => {
        setPromptValue(opts.defaultValue ?? "");
        setDialog({ kind: "prompt", opts, resolve });
      }),
    [],
  );

  const closeDialog = useCallback(
    (result: boolean | string | null) => {
      if (!dialog) return;
      if (dialog.kind === "confirm") dialog.resolve(result as boolean);
      else dialog.resolve(result as string | null);
      setDialog(null);
    },
    [dialog],
  );

  // Enfocar el input del prompt y cerrar con Escape.
  useEffect(() => {
    if (dialog?.kind === "prompt") setTimeout(() => inputRef.current?.focus(), 30);
    if (!dialog) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeDialog(dialog.kind === "confirm" ? false : null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [dialog, closeDialog]);

  const dialogApi = useMemo(() => ({ confirm, prompt }), [confirm, prompt]);
  const themeApi = useMemo(() => ({ theme, toggle }), [theme, toggle]);

  const toastIcon: Record<ToastKind, IconName> = {
    success: "check",
    error: "alert",
    info: "info",
  };

  return (
    <ThemeContext.Provider value={themeApi}>
      <ToastContext.Provider value={pushToast}>
        <DialogContext.Provider value={dialogApi}>
          {children}

          {/* Toasts */}
          <div className="toast-stack" role="status" aria-live="polite">
            {toasts.map((t) => (
              <div key={t.id} className={`toast ${t.kind}`}>
                <Icon name={toastIcon[t.kind]} size={18} />
                <span>{t.message}</span>
              </div>
            ))}
          </div>

          {/* Diálogo modal */}
          {dialog && (
            <div
              className="modal-overlay"
              onMouseDown={(e) => {
                if (e.target === e.currentTarget)
                  closeDialog(dialog.kind === "confirm" ? false : null);
              }}
            >
              <div className="modal" role="dialog" aria-modal="true">
                <h3 className="modal-title">{dialog.opts.title}</h3>
                {dialog.opts.message && <p className="modal-message">{dialog.opts.message}</p>}

                {dialog.kind === "prompt" && (
                  <div className="field" style={{ marginTop: 4 }}>
                    {dialog.opts.label && <label>{dialog.opts.label}</label>}
                    <input
                      ref={inputRef}
                      value={promptValue}
                      placeholder={dialog.opts.placeholder}
                      onChange={(e) => setPromptValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") closeDialog(promptValue);
                      }}
                    />
                  </div>
                )}

                <div className="modal-actions">
                  <button
                    className="btn ghost"
                    onClick={() => closeDialog(dialog.kind === "confirm" ? false : null)}
                  >
                    {dialog.kind === "confirm"
                      ? (dialog.opts as ConfirmOptions).cancelLabel ?? "Cancelar"
                      : "Cancelar"}
                  </button>
                  <button
                    className={`btn ${
                      dialog.kind === "confirm" && (dialog.opts as ConfirmOptions).danger
                        ? "danger-solid"
                        : "primary"
                    }`}
                    onClick={() => closeDialog(dialog.kind === "confirm" ? true : promptValue)}
                  >
                    {dialog.opts.confirmLabel ??
                      (dialog.kind === "confirm" ? "Confirmar" : "Aceptar")}
                  </button>
                </div>
              </div>
            </div>
          )}
        </DialogContext.Provider>
      </ToastContext.Provider>
    </ThemeContext.Provider>
  );
}

/* --------------------------- Componentes de apoyo ------------------------- */

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      className="icon-btn"
      onClick={toggle}
      title={theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
      aria-label="Cambiar tema"
    >
      <Icon name={theme === "dark" ? "sun" : "moon"} size={18} />
    </button>
  );
}

export function Skeleton({
  height = 16,
  width = "100%",
  radius = 8,
  style,
}: {
  height?: number | string;
  width?: number | string;
  radius?: number;
  style?: React.CSSProperties;
}) {
  return (
    <span className="skeleton" style={{ height, width, borderRadius: radius, ...style }} />
  );
}

export function EmptyState({
  icon = "info",
  title,
  hint,
}: {
  icon?: IconName;
  title: string;
  hint?: string;
}) {
  return (
    <div className="empty-state">
      <span className="empty-icon">
        <Icon name={icon} size={26} />
      </span>
      <p className="empty-title">{title}</p>
      {hint && <p className="empty-hint">{hint}</p>}
    </div>
  );
}
