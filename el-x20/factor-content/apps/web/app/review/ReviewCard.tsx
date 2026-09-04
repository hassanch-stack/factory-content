"use client";

import { useState } from "react";
import type { ReviewItem } from "../../lib/api";
import { approveReviewItem, rejectReviewItem, sendBackReviewItem } from "../../lib/api";

export default function ReviewCard({ item }: { item: ReviewItem }) {
  const [busy, setBusy] = useState(false);
  const [hidden, setHidden] = useState(false);

  async function handle(action: () => Promise<Response>) {
    setBusy(true);
    const res = await action();
    setBusy(false);
    if (res.ok) setHidden(true); // el item sale de la cola visualmente al resolverse
  }

  if (hidden) return null;

  const rightsOk = ["AUTHORIZED", "LICENSED", "PUBLIC_DOMAIN", "PLATFORM_SUPPORTED"].includes(
    item.rights_status
  );

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
      {item.preview && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={item.preview.preview_url}
          alt={item.title ?? "preview"}
          style={{ width: "100%", borderRadius: 6, aspectRatio: "9/16", objectFit: "cover" }}
        />
      )}

      <h3 style={{ marginTop: 8 }}>{item.ai_output?.title ?? item.title ?? "(sin título)"}</h3>

      {!rightsOk && (
        <p style={{ color: "#b00", fontSize: 13 }}>
          ⚠ rights_status={item.rights_status} — no se puede aprobar hasta resolverlo
        </p>
      )}

      {item.ai_output && (
        <div style={{ fontSize: 13, color: "#444" }}>
          <p><strong>Hook:</strong> {item.ai_output.hook}</p>
          <p><strong>CTA:</strong> {item.ai_output.cta}</p>
          <p><strong>Hashtags:</strong> {(item.ai_output.hashtags ?? []).join(" ")}</p>
        </div>
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <button disabled={busy || !rightsOk} onClick={() => handle(() => approveReviewItem(item.content_item_id))}>
          Aprobar
        </button>
        <button disabled={busy} onClick={() => handle(() => rejectReviewItem(item.content_item_id))}>
          Rechazar
        </button>
        <button disabled={busy} onClick={() => handle(() => sendBackReviewItem(item.content_item_id))}>
          Reprocesar
        </button>
      </div>
    </div>
  );
}
