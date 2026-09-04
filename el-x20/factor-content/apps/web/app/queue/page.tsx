"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ContentItem, getContentQueue } from "../../lib/api";
import ManualImportForm from "./ManualImportForm";

export default function QueuePage() {
  const [queue, setQueue] = useState<ContentItem[]>([]);
  const [message, setMessage] = useState("");
  useEffect(() => { getContentQueue().then(setQueue).catch((error) => setMessage(error.message)); }, []);
  return <main style={{ padding: 24, fontFamily: "system-ui", maxWidth: 1080 }}>
    <h1>Cola de contenido</h1><ManualImportForm />{message && <p role="status">{message}</p>}
    <section style={{ marginTop: 28 }}><h2>Contenido importado ({queue.length})</h2>
      {queue.length === 0 ? <p>Aún no hay fotos en la cola.</p> : <table cellPadding={8} style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead><tr style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}><th>Título</th><th>Estado</th><th>Derechos</th><th>Factor Score</th></tr></thead>
        <tbody>{queue.map((item) => <tr key={item.id} style={{ borderBottom: "1px solid #eee" }}><td><Link href={`/editor/${item.id}`}>{item.title || "Sin título"}</Link></td><td>{item.status}</td><td>{item.rights_status}</td><td>{item.factor_score}</td></tr>)}</tbody>
      </table>}
    </section>
  </main>;
}
