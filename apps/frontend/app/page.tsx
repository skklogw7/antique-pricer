"use client";
import { useState, FormEvent } from "react";

type ValueRange = { low: number; high: number; confidence: string };
type Comp = { title: string; price: number; sold_date: string; url: string; thumb: string };

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

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState("not_sure");
  const [notes, setNotes] = useState("");
  const [resJson, setResJson] = useState<EstimateResponse | null>(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
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

      const r = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/estimate`, {
        method: "POST",
        body: fd,
      });
      const data: EstimateResponse | { error: string } = await r.json();
      if (!r.ok || (data as any).error) {
        setErr((data as any).error || `Request failed (${r.status})`);
      } else {
        setResJson(data as EstimateResponse);
      }
    } catch (e) {
      setErr("Network error. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ maxWidth: 820, margin: "40px auto", padding: "0 16px", fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ marginBottom: 12 }}>Antique Pricer (MVP)</h1>
      <form onSubmit={onSubmit} style={{ display: "grid", gap: 12, padding: 16, border: "1px solid #eee", borderRadius: 8 }}>
        <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] || null)} />
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
          <p>
            <strong>${resJson.value_range.low}–${resJson.value_range.high}</strong> ({resJson.value_range.confidence})
          </p>
          {resJson.image_url && (
            <img src={resJson.image_url} alt="Uploaded item" style={{ maxWidth: 320, borderRadius: 6, border: "1px solid #ddd" }} />
          )}
          <h4>Why this range</h4>
          <ul>
            {resJson.pricing_rationale.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
          <h4>Comps</h4>
          <ul>
            {resJson.comps.map((c, i) => (
              <li key={i}>
                ${c.price} · {c.sold_date} ·{" "}
                <a href={c.url} target="_blank" rel="noreferrer">
                  link
                </a>
              </li>
            ))}
          </ul>
          <button onClick={() => { setFile(null); setResJson(null); setNotes(""); }} style={{ marginTop: 12 }}>
            Price another item
          </button>
        </section>
      )}
    </main>
  );
}

