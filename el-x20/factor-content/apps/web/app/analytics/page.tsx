"use client";

import { useEffect, useState } from "react";
import { DashboardKpis, getAnalyticsOverview } from "../../lib/api";

export default function AnalyticsPage() {
  const [kpis, setKpis] = useState<DashboardKpis | null>(null);
  const [message, setMessage] = useState("");
  useEffect(() => { getAnalyticsOverview().then(setKpis).catch((error) => setMessage(error.message)); }, []);
  return <main style={{ padding: 24, fontFamily: "system-ui" }}>
    <h1>Métricas</h1>
    {message && <p>{message}</p>}
    {kpis && <dl style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(180px, 1fr))", gap: 16 }}>
      <div><dt>Visualizaciones</dt><dd>{kpis.total_views}</dd></div>
      <div><dt>Media por publicación</dt><dd>{kpis.views_per_post.toFixed(0)}</dd></div>
      <div><dt>Mediana de visualizaciones</dt><dd>{kpis.median_views}</dd></div>
      <div><dt>Engagement</dt><dd>{(kpis.engagement_rate * 100).toFixed(2)}%</dd></div>
      <div><dt>Finalización media</dt><dd>{(kpis.avg_completion_rate * 100).toFixed(2)}%</dd></div>
      <div><dt>Seguidores ganados</dt><dd>{kpis.followers_gained}</dd></div>
    </dl>}
  </main>;
}
