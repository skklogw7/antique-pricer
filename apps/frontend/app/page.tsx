"use client";
import { useState } from "react";

export default function Home() {
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState<string>("");

  const ping = async () => {
    setErr("");
    setResult(null);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);
      const data = await res.json();
      setResult(data);
    } catch (e: any) {
      setErr(String(e));
    }
  };

  return (
    <main style={{ maxWidth: 680, margin: "40px auto", padding: "0 16px" }}>
      <h1>Antique Pricer (MVP)</h1>
      <button onClick={ping}>Ping API</button>
      {result && (
        <pre style={{ marginTop: 16, background: "#f6f6f6", padding: 12 }}>
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
      {err && <p style={{ color: "crimson" }}>{err}</p>}
    </main>
  );
}

