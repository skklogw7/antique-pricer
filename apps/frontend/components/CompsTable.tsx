// apps/frontend/components/CompsTable.tsx
import * as React from "react";

export type Comp = {
  title: string;
  price: number;
  currency?: string;
  url: string;
  thumbnail?: string | null;
  status: "active" | "sold";
  ended_at?: string | null;
  // legacy aliases (if your API still returns them)
  thumb?: string | null;
  sold_date?: string | null;
};

export default function CompsTable({ comps }: { comps: Comp[] }) {
  if (!comps?.length) return null;

  return (
    <div className="mt-6 overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="text-left border-b">
            <th className="py-2 pr-3">Thumb</th>
            <th className="py-2 pr-3">Title</th>
            <th className="py-2 pr-3">Price</th>
            <th className="py-2 pr-3">Status</th>
            <th className="py-2 pr-3">Date</th>
            <th className="py-2 pr-3">Link</th>
          </tr>
        </thead>
        <tbody>
          {comps.map((c, i) => {
            const thumb = c.thumbnail ?? c.thumb ?? null;
            const soldDate = c.ended_at ?? c.sold_date ?? "";
            return (
              <tr key={i} className="border-b align-top">
                <td className="py-2 pr-3">
                  {thumb ? (
                    // If you use next/image, add the domain to next.config.mjs
                    <img src={thumb} alt="" className="h-12 w-12 object-cover rounded" />
                  ) : null}
                </td>
                <td className="py-2 pr-3 min-w-[240px]">{c.title}</td>
                <td className="py-2 pr-3">
                  {c.currency ? `${c.currency} ` : "$"}
                  {typeof c.price === "number" ? c.price.toFixed(2) : c.price}
                </td>
                <td className="py-2 pr-3">{c.status === "sold" ? "Sold" : "Active"}</td>
                <td className="py-2 pr-3">{c.status === "sold" ? soldDate : ""}</td>
                <td className="py-2 pr-3">
                  <a href={c.url} target="_blank" rel="noreferrer" className="underline">
                    View
                  </a>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

