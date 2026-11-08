import { useCallback, useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, ApiError } from "../api";
import { Card, ErrorBox, RiskBadge, Spinner } from "../components/common";
import { amount, percent, RISK_COLORS } from "../format";
import type { ActionStatus, CustomerProfile, Explanation, Recommendation } from "../types";

const STEPS: ActionStatus[] = ["Pending", "Contacted", "Completed"];
const NEXT: Record<ActionStatus, ActionStatus | null> = { Pending: "Contacted", Contacted: "Completed", Completed: null };

/** US03 profile · US04/05 probability & risk · US07 SHAP · US08 suggestion · US09 status. */
export function CustomerDetail({ customerId, onBack }: { customerId: string; onBack: () => void }) {
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    Promise.all([api.getCustomer(customerId), api.getExplanation(customerId), api.getRecommendation(customerId)])
      .then(([p, e, r]) => {
        setProfile(p);
        setExplanation(e);
        setRecommendation(r);
      })
      .catch((e) => setErrors(e instanceof ApiError ? e.messages : ["Could not load customer."]));
  }, [customerId]);

  useEffect(load, [load]);

  async function advance(status: ActionStatus) {
    setSaving(true);
    try {
      await api.updateStatus(customerId, status);
      load();
    } catch (e) {
      setErrors(e instanceof ApiError ? e.messages : ["Could not update status."]);
    } finally {
      setSaving(false);
    }
  }

  const back = <button className="btn btn-ghost" onClick={onBack}>← Back</button>;
  if (errors.length) return <div className="stack">{back}<ErrorBox messages={errors} /></div>;
  if (!profile || !explanation || !recommendation) return <Spinner />;

  const risk = profile.risk_category;
  // Strongest factor first, so it appears at the top of the chart.
  const chartData = explanation.factors.map((f) => ({
    name: `${f.label} = ${f.value}`,
    contribution: f.contribution,
  }));
  const topDriver = explanation.factors.find((f) => f.contribution > 0);
  const topProtector = explanation.factors.find((f) => f.contribution < 0);

  const attributes: Array<[string, string | number]> = [
    ["Contract type", profile.contract_type],
    ["Tenure", `${profile.tenure_months} months`],
    ["Monthly charges", amount(profile.monthly_charges)],
    ["Total charges", amount(profile.total_charges)],
    ["Internet service", profile.internet_service],
    ["Tech support", profile.tech_support],
    ["Payment method", profile.payment_method],
    ["Support tickets", profile.support_tickets],
    ["Monthly usage", `${profile.monthly_usage_gb} GB`],
    ["Last login", `${profile.days_since_last_login} days ago`],
  ];

  return (
    <div className="stack">
      <div className="detail-head">
        {back}
        <h2 className="mono">{profile.customer_id}</h2>
        <RiskBadge risk={risk} />
      </div>

      <div className="grid-3">
        <Card title="Churn probability" className="gauge-card">
          <div className="gauge" style={{ ["--p" as string]: `${(profile.churn_probability ?? 0) * 100}`, ["--c" as string]: risk ? RISK_COLORS[risk] : "#94a3b8" }}>
            <span>{percent(profile.churn_probability)}</span>
          </div>
          <p className="center muted">
            <strong>{risk}</strong> risk · thresholds 40% / 70%
          </p>
        </Card>

        <Card title="Profile & activity" className="span-2">
          <dl className="attrs">
            {attributes.map(([k, v]) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
        </Card>
      </div>

      <div className="grid-3">
        <Card title="Why this prediction?" subtitle="Top 5 factors (SHAP). Red bars push towards churn; green bars keep the customer." className="span-2">
          <div className="insight">
            {topDriver && <p>🔺 Biggest risk driver: <strong>{topDriver.label} = {topDriver.value}</strong></p>}
            {topProtector && <p>🛡️ Strongest protective factor: <strong>{topProtector.label} = {topProtector.value}</strong></p>}
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="name" width={230} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v: number) => [v.toFixed(3), "SHAP contribution (log-odds)"]} />
              <ReferenceLine x={0} stroke="#64748b" />
              <Bar dataKey="contribution" radius={4}>
                {chartData.map((d) => <Cell key={d.name} fill={d.contribution > 0 ? "#dc2626" : "#16a34a"} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="muted small">{explanation.note}</p>
        </Card>

        <Card title="Suggested next step">
          <p className="action-text">{recommendation.action}</p>
          <p className="muted small">{recommendation.reason}</p>
          <p className="small">
            <span className="tag">Rule: {recommendation.rule_id}</span>{" "}
            {recommendation.requires_human_review && <span className="tag tag-warn">👤 Needs human review</span>}
          </p>

          <h4>Follow-up status</h4>
          {profile.action ? (
            <>
              <ol className="stepper">
                {STEPS.map((s) => (
                  <li key={s} className={STEPS.indexOf(s) <= STEPS.indexOf(profile.action!.status) ? "done" : ""}>{s}</li>
                ))}
              </ol>
              {NEXT[profile.action.status] ? (
                <button className="btn btn-primary full" disabled={saving} onClick={() => advance(NEXT[profile.action!.status]!)}>
                  Mark as {NEXT[profile.action.status]}
                </button>
              ) : (
                <p className="alert alert-success">✅ Follow-up completed</p>
              )}
            </>
          ) : (
            <p className="muted small">Low-risk customers have no tracked follow-up action.</p>
          )}
        </Card>
      </div>
    </div>
  );
}
