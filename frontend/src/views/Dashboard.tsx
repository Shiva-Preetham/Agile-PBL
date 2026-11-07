import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, ApiError } from "../api";
import { Card, EmptyState, ErrorBox, RiskBadge, Spinner, StatCard } from "../components/common";
import { CONTRACT_TYPES, INTERNET_SERVICES, percent, RISK_COLORS, RISKS } from "../format";
import type { DashboardSummary } from "../types";

/** US10: portfolio-level churn risk summary. */
export function Dashboard(props: { onOpenCustomer: (id: string) => void; onGoToUpload: () => void }) {
  const [contract, setContract] = useState("");
  const [internet, setInternet] = useState("");
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    api
      .dashboard({ contract_type: contract, internet_service: internet })
      .then((s) => {
        setSummary(s);
        setErrors([]);
      })
      .catch((e) => setErrors(e instanceof ApiError ? e.messages : ["Could not load dashboard."]));
  }, [contract, internet]);

  if (errors.length) return <ErrorBox messages={errors} />;
  if (!summary) return <Spinner />;

  const filtersActive = contract || internet;
  if (summary.total_customers === 0 && !filtersActive) {
    return (
      <Card>
        <EmptyState
          title="No customers yet"
          text="Upload a customer CSV to see churn risk across your portfolio."
          action={<button className="btn btn-primary" onClick={props.onGoToUpload}>Upload customers</button>}
        />
      </Card>
    );
  }

  const pieData = RISKS.map((r) => ({ name: r, value: summary.risk_counts[r] }));
  const actions = summary.action_status_counts;
  const totalActions = actions.Pending + actions.Contacted + actions.Completed;

  return (
    <div className="stack">
      <div className="filters">
        <label>
          Contract
          <select value={contract} onChange={(e) => setContract(e.target.value)}>
            <option value="">All contracts</option>
            {CONTRACT_TYPES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        <label>
          Internet
          <select value={internet} onChange={(e) => setInternet(e.target.value)}>
            <option value="">All services</option>
            {INTERNET_SERVICES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        {filtersActive && (
          <button className="btn btn-ghost" onClick={() => { setContract(""); setInternet(""); }}>
            Clear filters
          </button>
        )}
      </div>

      <div className="stats">
        <StatCard label="Customers" value={summary.total_customers} hint={filtersActive ? "matching filters" : "in portfolio"} />
        <StatCard label="High risk" value={summary.risk_counts.High} tone="High" hint="probability ≥ 70%" />
        <StatCard label="Medium risk" value={summary.risk_counts.Medium} tone="Medium" hint="40% – 70%" />
        <StatCard label="Low risk" value={summary.risk_counts.Low} tone="Low" hint="below 40%" />
        <StatCard label="Avg. churn probability" value={percent(summary.average_churn_probability)} />
      </div>

      <div className="grid-2">
        <Card title="Risk distribution" subtitle="Share of customers in each risk category">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={62} outerRadius={100} paddingAngle={2}>
                {pieData.map((d) => <Cell key={d.name} fill={RISK_COLORS[d.name]} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Risk by contract type" subtitle="Month-to-month customers carry most of the risk">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={summary.risk_by_contract}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="contract_type" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              {[...RISKS].reverse().map((r) => <Bar key={r} dataKey={r} stackId="risk" fill={RISK_COLORS[r]} />)}
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <div className="grid-2">
        <Card title="Retention follow-up" subtitle="Actions created for Medium and High risk customers">
          {totalActions === 0 ? (
            <p className="muted">No retention actions yet.</p>
          ) : (
            <div className="pipeline">
              {(["Pending", "Contacted", "Completed"] as const).map((s) => (
                <div key={s} className="pipeline-row">
                  <span className={`status status-${s.toLowerCase()}`}>{s}</span>
                  <div className="pipeline-track">
                    <div className={`pipeline-fill fill-${s.toLowerCase()}`} style={{ width: `${(actions[s] / totalActions) * 100}%` }} />
                  </div>
                  <strong>{actions[s]}</strong>
                </div>
              ))}
            </div>
          )}
        </Card>
        <Card title="Highest-risk customers" subtitle="Click a customer to see why and what to do">
          {summary.top_risk_customers.length === 0 ? (
            <p className="muted">No customers match these filters.</p>
          ) : (
            <ul className="toplist">
              {summary.top_risk_customers.map((c) => (
                <li key={c.customer_id} onClick={() => props.onOpenCustomer(c.customer_id)}>
                  <span className="mono">{c.customer_id}</span>
                  <span className="muted small">{c.contract_type}</span>
                  <strong>{percent(c.churn_probability)}</strong>
                  <RiskBadge risk={c.risk_category} />
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
