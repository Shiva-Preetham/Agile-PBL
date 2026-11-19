import { useEffect, useState } from "react";
import { api } from "./api";
import { percent } from "./format";
import type { ModelSchema } from "./types";

let cached: Promise<ModelSchema> | null = null;

/** Customer fields and risk thresholds, fetched once from the API (single source of truth). */
export function useSchema(): ModelSchema | null {
  const [schema, setSchema] = useState<ModelSchema | null>(null);
  useEffect(() => {
    cached ??= api.schema();
    cached.then(setSchema).catch(() => {
      cached = null; // retry on the next mount
    });
  }, []);
  return schema;
}

/** Human-readable threshold labels, e.g. { low: "below 40%", medium: "40% – 70%", high: "≥ 70%" }. */
export function thresholdLabels(schema: ModelSchema | null) {
  if (!schema) return { low: "", medium: "", high: "" };
  const m = percent(schema.risk_thresholds.medium, 0);
  const h = percent(schema.risk_thresholds.high, 0);
  return { low: `below ${m}`, medium: `${m} – ${h}`, high: `probability ≥ ${h}`, pair: `${m} / ${h}` };
}
