import type { Risk } from "./types";

export const percent = (value: number | null | undefined, digits = 1) =>
  value === null || value === undefined ? "—" : `${(value * 100).toFixed(digits)}%`;

export const amount = (value: number) => value.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export const RISK_COLORS: Record<Risk, string> = {
  Low: "#16a34a",
  Medium: "#d97706",
  High: "#dc2626",
};

export const RISKS: Risk[] = ["High", "Medium", "Low"];
export const CONTRACT_TYPES = ["Month-to-month", "One year", "Two year"];
export const INTERNET_SERVICES = ["DSL", "Fiber optic", "No"];
