"use client";

import { useEffect, useState } from "react";
import { getReviewQueue, ReviewItem } from "../../lib/api";
import ReviewCard from "./ReviewCard";

export default function ReviewPage() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [message, setMessage] = useState("");
  useEffect(() => { getReviewQueue().then(setItems).catch((error) => setMessage(error.message)); }, []);
  return <main style={{ padding: 24, fontFamily: "system-ui" }}><h1>Revisión ({items.length} pendientes)</h1><p role="status">{message}</p><div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 16, marginTop: 16 }}>{items.map((item) => <ReviewCard key={item.content_item_id} item={item} />)}</div>{items.length === 0 && !message && <p>No hay contenido esperando revisión.</p>}</main>;
}
