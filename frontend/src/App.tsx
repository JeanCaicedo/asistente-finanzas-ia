import { useEffect, useState } from "react";
import { api } from "./api/client";
import { Icon, type IconName } from "./components/Icon";
import { ThemeToggle } from "./components/ui";
import Dashboard from "./pages/Dashboard";
import Transactions from "./pages/Transactions";
import Budgets from "./pages/Budgets";
import ImportPage from "./pages/ImportPage";
import Chat from "./pages/Chat";

type Tab = "dashboard" | "transactions" | "budgets" | "import" | "chat";

const TABS: { id: Tab; label: string; icon: IconName; title: string; subtitle: string }[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    icon: "dashboard",
    title: "Dashboard",
    subtitle: "Resumen de ingresos, gastos y tendencias del mes.",
  },
  {
    id: "transactions",
    label: "Transacciones",
    icon: "transactions",
    title: "Transacciones",
    subtitle: "Registra, categoriza y filtra tus movimientos.",
  },
  {
    id: "budgets",
    label: "Presupuestos y metas",
    icon: "budgets",
    title: "Presupuestos y metas",
    subtitle: "Controla límites mensuales y avanza hacia tus objetivos.",
  },
  {
    id: "import",
    label: "Importar",
    icon: "import",
    title: "Importar movimientos",
    subtitle: "Sube un CSV o Excel y revisa antes de guardar.",
  },
  {
    id: "chat",
    label: "Chat IA",
    icon: "chat",
    title: "Chat sobre tus finanzas",
    subtitle: "Pregunta en lenguaje natural; las cifras son exactas y trazables.",
  },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [aiAvailable, setAiAvailable] = useState<boolean | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    api
      .health()
      .then((h) => setAiAvailable(h.ai_available))
      .catch(() => setAiAvailable(false));
  }, []);

  const active = TABS.find((t) => t.id === tab)!;

  useEffect(() => {
    document.title = `${active.title} · Asistente de Finanzas IA`;
  }, [active.title]);

  function go(id: Tab) {
    setTab(id);
    setMenuOpen(false);
  }

  return (
    <div className="app">
      {menuOpen && <div className="scrim" onClick={() => setMenuOpen(false)} />}

      <aside className={`sidebar ${menuOpen ? "open" : ""}`}>
        <div className="brand">
          <span className="brand-logo">
            <Icon name="wallet" size={22} />
          </span>
          <div>
            <div className="brand-name">Finanzas IA</div>
            <div className="brand-sub">Asistente personal</div>
          </div>
        </div>

        <nav className="nav">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`nav-item ${tab === t.id ? "active" : ""}`}
              onClick={() => go(t.id)}
            >
              <Icon name={t.icon} size={19} />
              {t.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className={`pill ${aiAvailable ? "on" : "off"}`}>
            <span className="dot" />
            {aiAvailable == null
              ? "Comprobando IA…"
              : aiAvailable
                ? "IA disponible"
                : "IA no disponible"}
          </span>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <button
            className="icon-btn menu-btn"
            onClick={() => setMenuOpen(true)}
            aria-label="Abrir menú"
          >
            <Icon name="menu" size={18} />
          </button>
          <div className="page-heading">
            <h1>{active.title}</h1>
            <p>{active.subtitle}</p>
          </div>
          <div className="topbar-right">
            <ThemeToggle />
          </div>
        </header>

        <main className="content" key={tab}>
          {tab === "dashboard" && <Dashboard />}
          {tab === "transactions" && <Transactions />}
          {tab === "budgets" && <Budgets />}
          {tab === "import" && <ImportPage />}
          {tab === "chat" && <Chat aiAvailable={aiAvailable ?? false} />}
        </main>
      </div>
    </div>
  );
}
