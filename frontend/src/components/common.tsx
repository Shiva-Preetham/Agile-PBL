import type { ReactNode } from "react";
import { percent, RISK_COLORS } from "../format";
import type { Risk } from "../types";

export function RiskBadge({ risk }: { risk: Risk | null }) {
  if (!risk) return <span className="badge badge-muted">Not scored</span>;
  return <span className={`badge badge-${risk.toLowerCase()}`}>{risk}</span>;
}

export function ProbabilityBar({ value, risk }: { value: number | null; risk: Risk | null }) {
  const width = value === null ? 0 : Math.round(value * 100);
  return (
    <div className="prob">
      <div className="prob-track">
        <div className="prob-fill" style={{ width: `${width}%`, background: risk ? RISK_COLORS[risk] : "#94a3b8" }} />
      </div>
      <span className="prob-label">{percent(value)}</span>
    </div>
  );
}

export function StatCard(props: { label: string; value: ReactNode; hint?: string; tone?: Risk | "primary" }) {
  return (
    <div className={`stat stat-${(props.tone ?? "primary").toLowerCase()}`}>
      <span className="stat-label">{props.label}</span>
      <span className="stat-value">{props.value}</span>
      {props.hint && <span className="stat-hint">{props.hint}</span>}
    </div>
  );
}

export function Card(props: { title?: string; subtitle?: string; actions?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`card ${props.className ?? ""}`}>
      {(props.title || props.actions) && (
        <header className="card-head">
          <div>
            {props.title && <h3>{props.title}</h3>}
            {props.subtitle && <p className="muted">{props.subtitle}</p>}
          </div>
          {props.actions}
        </header>
      )}
      {props.children}
    </section>
  );
}

export function ErrorBox({ messages }: { messages: string[] }) {
  if (!messages.length) return null;
  return (
    <div className="alert alert-error" role="alert">
      <strong>Please fix the following:</strong>
      <ul>
        {messages.map((m) => (
          <li key={m}>{m}</li>
        ))}
      </ul>
    </div>
  );
}

export function EmptyState(props: { title: string; text: string; action?: ReactNode }) {
  return (
    <div className="empty">
      <div className="empty-icon" aria-hidden>📂</div>
      <h3>{props.title}</h3>
      <p className="muted">{props.text}</p>
      {props.action}
    </div>
  );
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="spinner-wrap">
      <span className="spinner" aria-hidden /> {label}
    </div>
  );
}
