import { Card, RiskBadge } from "../components/common";
import { percent } from "../format";
import type { ActionStatus, NextBestAction, RetentionAction } from "../types";

const STEPS: ActionStatus[] = ["Pending", "Contacted", "Completed"];
const NEXT: Record<ActionStatus, ActionStatus | null> = { Pending: "Contacted", Contacted: "Completed", Completed: null };

/** US14 Next Best Action + US09 follow-up tracking. */
export function NextBestActionCard(props: {
  nba: NextBestAction;
  followUp: RetentionAction | null;
  saving: boolean;
  onAdvance: (status: ActionStatus) => void;
}) {
  const { nba, followUp } = props;
  const top = nba.options[0];
  const next = followUp ? NEXT[followUp.status] : null;

  return (
    <Card title="🎯 Next Best Action" className="nba-card">
      <p className="action-text">{nba.best.action}</p>
      {top && (
        <div className="nba-impact">
          <span className="nba-from">{percent(nba.current_probability, 0)}</span>
          <span className="nba-arrow" aria-hidden>→</span>
          <span className="nba-to">{percent(top.new_probability, 0)}</span>
          <RiskBadge risk={top.new_risk} />
          <span className="muted small">estimated churn after this action</span>
        </div>
      )}
      <p className="muted small">{nba.best.reason}</p>
      <p className="small">
        <span className="tag">Rule: {nba.best.rule_id}</span>{" "}
        {top && <span className={`tag cost-${top.cost.toLowerCase()}`}>Cost: {top.cost}</span>}{" "}
        {nba.best.requires_human_review && <span className="tag tag-warn">👤 Needs human review</span>}
      </p>

      <h4>Follow-up status</h4>
      {followUp ? (
        <>
          <ol className="stepper">
            {STEPS.map((s) => (
              <li key={s} className={STEPS.indexOf(s) <= STEPS.indexOf(followUp.status) ? "done" : ""}>{s}</li>
            ))}
          </ol>
          {next ? (
            <button className="btn btn-primary full" disabled={props.saving} onClick={() => props.onAdvance(next)}>
              Mark as {next}
            </button>
          ) : (
            <p className="alert alert-success">✅ Follow-up completed</p>
          )}
        </>
      ) : (
        <p className="muted small">Low-risk customers have no tracked follow-up action.</p>
      )}
    </Card>
  );
}

/** US14: step-by-step retention plan and every option compared on its own. */
export function RetentionPlanCard({ nba }: { nba: NextBestAction }) {
  if (nba.current_risk === "Low") return null;
  const last = nba.plan[nba.plan.length - 1];
  const stays = last?.risk === "Low";

  return (
    <Card
      title="Retention plan: what keeps this customer?"
      subtitle="Each action is tried on a copy of the customer and the model re-scores it (what-if simulation)"
    >
      <div className="grid-2 plan-grid">
        <div>
          <h4>Step-by-step plan</h4>
          {nba.plan.length === 0 ? (
            <p className="muted">No simulated action lowers this customer's risk enough. Start with the Next Best Action above.</p>
          ) : (
            <ol className="timeline">
              <li className="timeline-now">
                <span className="timeline-label">Today</span>
                <strong>{percent(nba.current_probability, 0)}</strong>
                <RiskBadge risk={nba.current_risk} />
              </li>
              {nba.plan.map((step, i) => (
                <li key={step.rule_id}>
                  <span className="timeline-label">Step {i + 1}: {step.action}</span>
                  <strong>{percent(step.probability, 0)}</strong>
                  <RiskBadge risk={step.risk} />
                </li>
              ))}
            </ol>
          )}
          {last && (
            <div className={`alert ${stays ? "alert-success" : "alert-warn"}`}>
              {stays
                ? `✅ After ${nba.plan.length} action${nba.plan.length > 1 ? "s" : ""}, the customer is estimated to be Low risk (likely to stay).`
                : `⚠️ Even with every helpful action, risk stays ${last.risk}. Escalate to a personal call with an account manager.`}
            </div>
          )}
        </div>

        <div>
          <h4>All options, each on its own</h4>
          {nba.options.length === 0 ? (
            <p className="muted">No simulated option helps enough.</p>
          ) : (
            <div className="table-wrap">
              <table className="options">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Action &amp; simulated change</th>
                    <th className="num">Churn after</th>
                    <th>Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {nba.options.map((o, i) => (
                    <tr key={o.rule_id} className={i === 0 ? "best-row" : ""}>
                      <td>{i === 0 ? "⭐" : i + 1}</td>
                      <td>
                        <div>{o.action}</div>
                        <div className="muted small">{o.change_text.join("; ")}</div>
                      </td>
                      <td className="num">
                        <strong>{percent(o.new_probability, 0)}</strong>
                        <div className="small down">▼ {(o.reduction * 100).toFixed(1)} pts</div>
                      </td>
                      <td><span className={`tag cost-${o.cost.toLowerCase()}`}>{o.cost}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
      <p className="muted small">ℹ️ {nba.note}</p>
    </Card>
  );
}
