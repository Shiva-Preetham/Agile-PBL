/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend address for the hosted build, e.g. https://churnsense-api.onrender.com (empty = same origin / dev proxy). */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
