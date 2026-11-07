import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, ApiError } from "../api";
import { Card, ErrorBox, RiskBadge, Spinner, StatCard } from "../components/common";
import { CONTRACT_TYPES, INTERNET_SERVICES, percent, RISK_COLORS } from "../format";
import type { ModelMetrics, Prediction, ScoreSet } from "../types";

const METRIC_INFO: Array<[keyof ScoreSet, string, string]> = [
  ["roc_auc", "ROC-AUC", "How well the model ranks churners above stayers (0.5 = guessing, 1 = perfect)"],
  ["accuracy", "Accuracy", "Share of all predictions that were correct"],
  ["precision", "Precision", "Of customers flagged as churners, how many really churned"],
  ["recall", "Recall", "Of real churners, how many the model caught"],
  ["f1", "F1 score", "Balance of precision and recall"],
];

type Form = Record<string, string | number>;
const FIELDS: Array<{ name: string; label: string; options?: string[]; min?: number; max?: number; step?: number }> = [
  { name: "contract_type", label: "Contract type", options: CONTRACT_TYPES },
  { name: "tenure_months", label: "Tenure (months)", min: 0, max: 120 },
  { name: "monthly_charges", label: "Monthly charges", min: 0, max: 1000, step: 0.5 },
  { name: "total_charges", label: "Total charges", min: 0, max: 200000, step: 1 },
  { name: "internet_service", label: "Internet service", options: INTERNET_SERVICES },
  { name: "tech_support", label: "Tech support", options: ["Yes", "No"] },
  { name: "payment_method", label: "Payment method", options: ["Electronic check", "Mailed check", "Bank transfer", "Credit card"] },
  { name: "support_tickets", label: "Support tickets", min: 0, max: 100 },
  { name: "monthly_usage_gb", label: "Monthly usage (GB)", min: 0, max: 10000, step: 0.1 },
  { name: "days_since_last_login", label: "Days since last login", min: 0, max: 3650 },
];
const START: Form = {
  contract_type: "Month-to-month", tenure_months: 3, monthly_charges: 95.5, total_charges: 286.5,
  internet_service: "Fiber optic", tech_support: "No", payment_method: "Electronic check",
  support_tickets: 4, monthly_usage_gb: 20, days_since_last_login: 21,
};

/** US06: model evaluation metrics + a what-if predictor (US04/US05). */
export function ModelView() {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    api.metrics().then(setMetrics).catch((e) => setErrors(e instanceof ApiError ? e.messages : ["Could not load metrics."]));
  }, []);

  if (errors.length) return <ErrorBox messages={errors} />;
  if (!metrics) return <Spinner />;

  const cm = metrics.holdout_confusion_matrix;

  return (
    <div className="stack">
      <Card title="Model quality on unseen data" subtitle={`${metrics.model} · ${metrics.split.evaluated_on}`}>
        <div className="stats">
          {METRIC_INFO.map(([key, label, hint]) => (
            <StatCard key={key} label={label} value={metrics.holdout_metrics[key].toFixed(3)} hint={hint} />
          ))}
        </div>
        <p className="muted small">
          Trained on {metrics.split.n_train} customers, tested on {metrics.split.n_test} held-out customers ({metrics.split.method.toLowerCase()}).
          Dataset: {metrics.dataset.name}, churn rate {percent(metrics.dataset.churn_rate)}.
        </p>
      </Card>

      <div className="grid-2">
        <Card title="Confusion matrix (holdout)" subtitle={`Decision threshold ${metrics.decision_threshold}`}>
          <table className="cm">
            <thead>
              <tr><th></th><th>Predicted: stays</th><th>Predicted: churns</th></tr>
            </thead>
            <tbody>
              <tr><th>Actually stayed</th><td className="ok">{cm.tn}<small>correct</small></td><td className="bad">{cm.fp}<small>false alarm</small></td></tr>
              <tr><th>Actually churned</th><td className="bad">{cm.fn}<small>missed</small></td><td className="ok">{cm.tp}<small>caught</small></td></tr>
            </tbody>
          </table>
          <details className="small">
            <summary>Training-set scores (overfitting check only)</summary>
            <p className="muted">{metrics.training_metrics_note}</p>
            <p className="mono">
              {METRIC_INFO.map(([k, label]) => `${label} ${metrics.training_metrics[k].toFixed(3)}`).join(" · ")}
            </p>
          </details>
        </Card>
        <Card title="What drives churn overall?" subtitle="Average impact of each field (mean |SHAP|) on holdout customers">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={metrics.global_importance} layout="vertical" margin={{ left: 10, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="label" width={160} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v: number) => [v.toFixed(3), "mean |SHAP|"]} />
              <Bar dataKey="mean_abs_shap" fill="#4f46e5" radius={4} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <WhatIf thresholds={metrics.risk_thresholds} />
    </div>
  );
}

function WhatIf({ thresholds }: { thresholds: ModelMetrics["risk_thresholds"] }) {
  const [form, setForm] = useState<Form>(START);
  const [result, setResult] = useState<Prediction | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    const timer = setTimeout(() => {
      api
        .predict(form)
        .then((r) => {
          setResult(r);
          setErrors([]);
        })
        .catch((e) => setErrors(e instanceof ApiError ? e.messages : ["Prediction failed."]));
    }, 250);
    return () => clearTimeout(timer);
  }, [form]);

  return (
    <Card title="What-if predictor" subtitle="Change a customer's details and watch the churn probability update live">
      <div className="whatif">
        <div className="form-grid">
          {FIELDS.map((f) => (
            <label key={f.name}>
              {f.label}
              {f.options ? (
                <select value={form[f.name]} onChange={(e) => setForm({ ...form, [f.name]: e.target.value })}>
                  {f.options.map((o) => <option key={o}>{o}</option>)}
                </select>
              ) : (
                <input
                  type="number" min={f.min} max={f.max} step={f.step ?? 1} value={form[f.name]}
                  onChange={(e) => setForm({ ...form, [f.name]: e.target.value })}
                />
              )}
            </label>
          ))}
        </div>
        <div className="whatif-result">
          {result && (
            <>
              <div className="gauge" style={{ ["--p" as string]: `${result.churn_probability * 100}`, ["--c" as string]: RISK_COLORS[result.risk_category] }}>
                <span>{percent(result.churn_probability)}</span>
              </div>
              <RiskBadge risk={result.risk_category} />
            </>
          )}
          <ErrorBox messages={errors} />
          <table className="thresholds small">
            <tbody>
              {(["Low", "Medium", "High"] as const).map((r) => (
                <tr key={r}><td><RiskBadge risk={r} /></td><td className="mono">{thresholds[r]}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Card>
  );
}
