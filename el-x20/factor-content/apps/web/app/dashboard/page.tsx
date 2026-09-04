"use client";

import { useEffect, useState } from "react";
import { ContentItem, getContentQueue, getSources, Source } from "../../lib/api";

export default function DashboardPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [queue, setQueue] = useState<ContentItem[]>([]);
  const [message, setMessage] = useState("");
  useEffect(() => { Promise.all([getSources(), getContentQueue()]).then(([s, q]) => { setSources(s); setQueue(q); }).catch((error) => setMessage(error.message)); }, []);
  const counts = queue.reduce<Record<string, number>>((acc, item) => { acc[item.status] = (acc[item.status] ?? 0) + 1; return acc; }, {});
  return <main style={{ padding: 24, fontFamily: "system-ui" }}><h1>Factor Content</h1><p>Entrada manual de fotos y flujo de revisión.</p><p role="status">{message}</p><h2>Fuentes ({sources.length})</h2><ul>{sources.map((source) => <li key={source.id}>{source.name} · {source.permission_status}</li>)}</ul><h2>Cola por estado</h2><ul>{Object.entries(counts).map(([status, count]) => <li key={status}>{status}: {count}</li>)}</ul></main>;
}
