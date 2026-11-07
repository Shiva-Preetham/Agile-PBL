import { useState } from "react";
import { CustomerDetail } from "./views/CustomerDetail";
import { Customers } from "./views/Customers";
import { Dashboard } from "./views/Dashboard";
import { ModelView } from "./views/ModelView";

type Tab = "dashboard" | "customers" | "model";

const TABS: Array<[Tab, string]> = [
  ["dashboard", "Dashboard"],
  ["customers", "Customers"],
  ["model", "Model"],
];

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [customerId, setCustomerId] = useState<string | null>(null);

  const go = (next: Tab) => {
    setCustomerId(null);
    setTab(next);
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo" aria-hidden>
            <svg viewBox="0 0 32 32" width="28" height="28">
              <rect width="32" height="32" rx="8" fill="#4f46e5" />
              <path d="M8 20l5-6 4 4 7-9" stroke="white" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <div>
            <strong>ChurnSense</strong>
            <span className="tagline">Predict · Explain · Act</span>
          </div>
        </div>
        <nav className="tabs">
          {TABS.map(([key, label]) => (
            <button key={key} className={tab === key && !customerId ? "tab active" : "tab"} onClick={() => go(key)}>
              {label}
            </button>
          ))}
        </nav>
        <span className="version">Prototype v0.1</span>
      </header>

      <main className="content">
        {customerId ? (
          <CustomerDetail customerId={customerId} onBack={() => setCustomerId(null)} />
        ) : tab === "dashboard" ? (
          <Dashboard onOpenCustomer={setCustomerId} onGoToUpload={() => go("customers")} />
        ) : tab === "customers" ? (
          <Customers onOpenCustomer={setCustomerId} />
        ) : (
          <ModelView />
        )}
      </main>

      <footer className="footer">
        ChurnSense · Agile PBL, Fundamentals of Agile Software Development Lab (26B16CS314), JIIT Noida
      </footer>
    </div>
  );
}
