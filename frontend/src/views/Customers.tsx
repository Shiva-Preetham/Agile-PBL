import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { Card, EmptyState, ErrorBox, ProbabilityBar, RiskBadge, Spinner } from "../components/common";
import { amount, CONTRACT_TYPES, RISKS } from "../format";
import type { CustomerPage } from "../types";
import { UploadPanel } from "./UploadPanel";

const PAGE_SIZE = 15;

/** US01 upload + US02 search & filter. */
export function Customers({ onOpenCustomer }: { onOpenCustomer: (id: string) => void }) {
  const [search, setSearch] = useState("");
  const [risk, setRisk] = useState("");
  const [contract, setContract] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<CustomerPage | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      api
        .listCustomers({ search, risk, contract_type: contract, page, page_size: PAGE_SIZE })
        .then((d) => {
          setData(d);
          setErrors([]);
        })
        .catch((e) => setErrors(e instanceof ApiError ? e.messages : ["Could not load customers."]));
    }, 200); // small debounce while typing
    return () => clearTimeout(timer);
  }, [search, risk, contract, page, reload]);

  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;
  const resetPage = <T,>(setter: (v: T) => void) => (v: T) => {
    setter(v);
    setPage(1);
  };

  return (
    <div className="stack">
      <UploadPanel onUploaded={() => setReload((n) => n + 1)} />

      <Card
        title="Customers"
        subtitle="Sorted by churn probability, highest risk first"
        actions={data && <span className="muted">{data.total} result{data.total === 1 ? "" : "s"}</span>}
      >
        <div className="filters">
          <input
            className="search"
            placeholder="Search by customer ID…"
            value={search}
            onChange={(e) => resetPage(setSearch)(e.target.value)}
          />
          <select value={risk} onChange={(e) => resetPage(setRisk)(e.target.value)}>
            <option value="">All risk levels</option>
            {RISKS.map((r) => <option key={r}>{r}</option>)}
          </select>
          <select value={contract} onChange={(e) => resetPage(setContract)(e.target.value)}>
            <option value="">All contracts</option>
            {CONTRACT_TYPES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </div>

        <ErrorBox messages={errors} />
        {!data && !errors.length && <Spinner />}
        {data && data.items.length === 0 && (
          <EmptyState title="No matching customers" text="Try a different search or clear the filters." />
        )}
        {data && data.items.length > 0 && (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Customer ID</th>
                    <th>Contract</th>
                    <th className="num">Tenure</th>
                    <th className="num">Monthly charges</th>
                    <th>Internet</th>
                    <th>Churn probability</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((c) => (
                    <tr key={c.customer_id} onClick={() => onOpenCustomer(c.customer_id)} className="clickable">
                      <td className="mono">{c.customer_id}</td>
                      <td>{c.contract_type}</td>
                      <td className="num">{c.tenure_months} mo</td>
                      <td className="num">{amount(c.monthly_charges)}</td>
                      <td>{c.internet_service}</td>
                      <td><ProbabilityBar value={c.churn_probability} risk={c.risk_category} /></td>
                      <td><RiskBadge risk={c.risk_category} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pager">
              <button className="btn btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Previous</button>
              <span className="muted">Page {page} of {pages}</span>
              <button className="btn btn-ghost" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next →</button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
