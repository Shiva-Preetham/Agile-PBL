export type Risk = "Low" | "Medium" | "High";
export type ActionStatus = "Pending" | "Contacted" | "Completed";

export interface RetentionAction {
  rule_id: string;
  action: string;
  status: ActionStatus;
  updated_at?: string | null;
}

export interface CustomerSummary {
  customer_id: string;
  tenure_months: number;
  contract_type: string;
  monthly_charges: number;
  internet_service: string;
  churn_probability: number | null;
  risk_category: Risk | null;
}

export interface CustomerProfile extends CustomerSummary {
  total_charges: number;
  tech_support: string;
  payment_method: string;
  support_tickets: number;
  monthly_usage_gb: number;
  days_since_last_login: number;
  action: RetentionAction | null;
}

export interface CustomerPage {
  items: CustomerSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface Factor {
  feature: string;
  label: string;
  value: string | number;
  contribution: number;
  effect: string;
}

export interface Explanation {
  customer_id: string;
  churn_probability: number;
  risk_category: Risk;
  base_value: number;
  factors: Factor[];
  note: string;
}

export interface Recommendation {
  customer_id: string;
  risk_category: Risk;
  rule_id: string;
  action: string;
  reason: string;
  requires_human_review: boolean;
}

export interface DashboardSummary {
  total_customers: number;
  risk_counts: Record<Risk, number>;
  average_churn_probability: number | null;
  action_status_counts: Record<ActionStatus, number>;
  risk_by_contract: Array<{ contract_type: string } & Record<Risk, number>>;
  top_risk_customers: Array<{
    customer_id: string;
    churn_probability: number;
    risk_category: Risk;
    contract_type: string;
  }>;
}

export interface ScoreSet {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
}

export interface ModelMetrics {
  model: string;
  dataset: { name: string; rows: number; churn_rate: number };
  split: { method: string; test_size: number; n_train: number; n_test: number; evaluated_on: string };
  decision_threshold: number;
  holdout_metrics: ScoreSet;
  holdout_confusion_matrix: { tn: number; fp: number; fn: number; tp: number };
  training_metrics: ScoreSet;
  training_metrics_note: string;
  global_importance: Array<{ feature: string; label: string; mean_abs_shap: number }>;
  risk_thresholds: Record<Risk, string>;
  trained_at: string;
}

export interface UploadResult {
  inserted: number;
  updated: number;
  total_customers: number;
}

export interface Prediction {
  churn_probability: number;
  risk_category: Risk;
}
