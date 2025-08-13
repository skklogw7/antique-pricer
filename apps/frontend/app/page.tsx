"use client";
import { useEffect, useState } from "react";

type Health = { ok: boolean } | { error: string };

export default function Home() {
  const [data, setData] = useState<Health | null>(null);

  useEffect(() => {
    const run = async () => {
      try {
        const res = await fetch("https://antique-pricer.onrender.com/health", {
          method: "GET",
          credentials: "include",
        });
        const json = (await res.json()) as Health;
        setData(json);
      } catch (e) {
        setData({ error: "Failed to fetch" });
      }
    };
    run();
  }, []);

  return (
    <main style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>Backend Connection Test</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </main>
  );
}

