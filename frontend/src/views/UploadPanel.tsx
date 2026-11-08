import { useRef, useState } from "react";
import { api, ApiError } from "../api";
import { Card, ErrorBox } from "../components/common";
import type { UploadResult } from "../types";

/** US01: upload and validate a customer CSV. */
export function UploadPanel({ onUploaded }: { onUploaded: () => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [result, setResult] = useState<UploadResult | null>(null);

  function choose(selected: File | null | undefined) {
    setFile(selected ?? null);
    setErrors([]);
    setResult(null);
  }

  async function upload() {
    if (!file) return;
    setBusy(true);
    setErrors([]);
    try {
      setResult(await api.uploadCsv(file));
      onUploaded();
    } catch (error) {
      setErrors(error instanceof ApiError ? error.messages : ["Upload failed."]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Upload customer data" subtitle="CSV with the 11 required columns. Every row is validated before anything is saved.">
      <div
        className={`dropzone ${dragging ? "dropzone-active" : ""}`}
        onClick={() => input.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          choose(e.dataTransfer.files[0]);
        }}
      >
        <input ref={input} type="file" accept=".csv" hidden onChange={(e) => choose(e.target.files?.[0])} />
        <span className="dropzone-icon" aria-hidden>⬆</span>
        {file ? <strong>{file.name}</strong> : <span>Drop a CSV here or <u>browse</u></span>}
        <span className="muted small">Try backend/data/sample_customers.csv, or sample_invalid_rows.csv to see validation</span>
      </div>
      <div className="row-end">
        <button className="btn btn-primary" disabled={!file || busy} onClick={upload}>
          {busy ? "Validating & scoring…" : "Upload & predict"}
        </button>
      </div>
      {result && (
        <div className="alert alert-success">
          ✅ Upload complete: <strong>{result.inserted}</strong> new, <strong>{result.updated}</strong> updated.{" "}
          {result.total_customers} customers in total, all scored.
        </div>
      )}
      <ErrorBox messages={errors} title="Please fix the following:" />
    </Card>
  );
}
