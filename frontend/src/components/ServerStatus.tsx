import { useEffect, useState } from "react";
import { api, ApiError } from "../api";

const SLOW_AFTER_MS = 2500;

/**
 * The free hosting plan puts the backend to sleep after 15 idle minutes, and the
 * first request then takes up to a minute. Explain that instead of looking broken.
 */
export function ServerStatus() {
  const [state, setState] = useState<"checking" | "waking" | "ready" | "down">("checking");
  const [message, setMessage] = useState("");

  useEffect(() => {
    let done = false;
    const timer = setTimeout(() => !done && setState("waking"), SLOW_AFTER_MS);
    api
      .health()
      .then(() => setState("ready"))
      .catch((e) => {
        setState("down");
        setMessage(e instanceof ApiError ? e.messages.join(" ") : "The API is not reachable.");
      })
      .finally(() => {
        done = true;
        clearTimeout(timer);
      });
    return () => clearTimeout(timer);
  }, []);

  if (state === "waking") {
    return (
      <div className="banner banner-info" role="status">
        <span className="spinner" aria-hidden /> Waking up the server (free hosting sleeps when idle). This can take up to a minute…
      </div>
    );
  }
  if (state === "down") {
    return <div className="banner banner-error" role="alert">⚠️ {message} Try refreshing in a moment.</div>;
  }
  return null;
}
