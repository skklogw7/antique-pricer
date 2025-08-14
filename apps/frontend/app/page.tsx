"use client";

import { useState, FormEvent } from "react";
import * as React from "react";
import CompsTable from "../components/CompsTable";

type ValueRange = { low: number; high: number; confidence: string };

// Expanded Comp type so it works with both your legacy fields (thumb/sold_date)
// and the new provider fields (thumbnail/status/ended_at/currency).
type Comp = {
  title: string;
  price: number;
  url: string;
  thumb?: string | null;
  sold_date?: string | null;
  // new/optional fields from providers
  thumbnail?: string | null;
  status?: "active" | "sold";
  ended_at?: string | null;
  currency?: string;
};

type EstimateResponse = {
  normalized_title: string;
  value_range: ValueRange;
  pricing_rationale: string[];
  top_comps_used: number[];
  notes: string[];
  suggested_keywords: string[];
  comps: Comp[];
  image_url: string | null;
  duration_ms: number;
};

function isEstimateResponse(x: unknown): x is EstimateResponse {
  if (!x || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  return (
    typeof o.normalized_title === "string" &&
    typeof o.value_range === "object" &&
    Array.isArray(o.pricing_rationale) &&
    Array.isArray(o.comps)
  );
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState("not_sure");
  const [notes, setNotes] = useState("");
  const [resJson, setResJson] = useState<EstimateResponse | null>(null);
  const [err, setErr] = useState<string>("");
  const [loading, setLoading] = useState(false);

  // Fallback to localhost if NEXT_PUBLIC_API_URL is not set
  const API_BASE =
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || "http://localhost:8000";

  const onSubmit = async (ev: FormEvent) => {
    ev.preventDefault();
    setErr("");
    setResJson(null);

    if (!file) {
      setErr("Please choose an image.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setErr("Image too large (max 10MB).");
      return;
    }

    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("image", file);
      fd.append("category", category);
      fd.append("notes", notes);

      const r = await fetch(`${API_BASE}/estimate`, {
        method: "POST",
        body: fd,
      });
      const data: unknown = await r.json();

      if (!r.ok) {
        const msg = (data as { error?: string } | null)?.error ?? `Request failed (${r.status})`;
        setErr(msg);
        return;
      }

      if (isEstimateResponse(data)) {
        setResJson(data);
      } else {
        setErr("Unexpected response format.");
      }
    } catch {
      setErr("Network error. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main
      style={{
        maxWidth: 820,
        margin: "40px auto",
        padding: "0 16px",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h1 style={{ marginBottom: 12 }}>Antique Pricer (MVP)</h1>

      <form
        onSubmit={onSubmit}
        style={{ display: "grid", gap: 12, padding: 16, border: "1px solid #eee", borderRadius: 8 }}
      >
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />

        <label>
          Category:&nbsp;
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="not_sure">Not sure</option>
            <option value="furniture">Furniture</option>
            <option value="art">Art</option>
            <option value="jewelry">Jewelry</option>
            <option value="collectible">Collectible</option>
          </select>
        </label>

        <textarea
          placeholder="Notes (e.g., dimensions, maker’s mark, condition)"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          style={{ resize: "vertical" }}
        />

        <button disabled={!file || loading} style={{ padding: "8px 12px" }}>
          {loading ? "Estimating..." : "Get value"}
        </button>

        {err && <div style={{ color: "crimson" }}>{err}</div>}
      </form>

      {resJson && (
        <section style={{ marginTop: 24, padding: 16, border: "1px solid #eee", borderRadius: 8 }}>
          <h3 style={{ marginTop: 0 }}>{resJson.normalized_title}</h3>

          {/* Estimated range + 1-line rationale */}
          <p>
            <strong>
              ${resJson.value_range.low}–${resJson.value_range.high}
            </strong>{" "}
            ({resJson.value_range.confidence})
            {resJson.pricing_rationale?.[0] ? ` · ${resJson.pricing_rationale[0]}` : ""}
          </p>

          {/* Uploaded image preview, if available */}
          {resJson.image_url && (
            <img
              src={resJson.image_url}
              alt="Uploaded item"
              style={{ maxWidth: 320, borderRadius: 6, border: "1px solid #ddd" }}
            />
          )}

          {/* Full rationale list (optional to keep) */}
          <h4>Why this range</h4>
          <ul>
            {resJson.pricing_rationale.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>

          {/* Comps table (replaces old simple <ul>) */}
          <h4>Comparable Listings</h4>
          <CompsTable comps={resJson.comps} />

          <button
            onClick={() => {
              setFile(null);
              setResJson(null);
              setNotes("");
            }}
            style={{ marginTop: 12 }}
          >
            Price another item
          </button>

          {/* Optional: timing */}
          {typeof resJson.duration_ms === "number" ? (
            <p style={{ marginTop: 8, color: "#666", fontSize: 12 }}>
              Took {resJson.duration_ms} ms
            </p>
          ) : null}
        </section>
      )}
    </main>
  );
}

