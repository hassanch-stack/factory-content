"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  createScriptTemplate,
  createVisualTemplate,
  getScriptTemplates,
  getVisualTemplates,
  ScriptTemplate,
  VisualTemplate,
} from "../../lib/api";

const VISUAL_EXAMPLE = `{
  "canvas": { "width": 1080, "height": 1920, "background_fit": "cover" },
  "zones": [{ "role": "hook", "x": 40, "y": 620, "max_width": 1000, "font_size": 64 }],
  "output": { "format": "jpg", "quality": 90 }
}`;

const SCRIPT_EXAMPLE = `{
  "sections": [{ "role": "hook", "max_words": 20 }, { "role": "body_beats", "repeat": true, "count": 3, "max_words": 25 }, { "role": "cta", "max_words": 15 }],
  "hashtag_count": 5,
  "keyword_count": 5,
  "title_max_words": 14,
  "tone": "urgente"
}`;

export default function TemplatesPage() {
  const [visual, setVisual] = useState<VisualTemplate[]>([]);
  const [scripts, setScripts] = useState<ScriptTemplate[]>([]);
  const [message, setMessage] = useState("");
  useEffect(() => {
    Promise.all([getVisualTemplates(), getScriptTemplates()])
      .then(([loadedVisual, loadedScripts]) => { setVisual(loadedVisual); setScripts(loadedScripts); })
      .catch((error) => setMessage(error.message));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>, type: "visual" | "script") {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      const name = String(data.get("name"));
      const config = JSON.parse(String(data.get("configuration")));
      if (type === "visual") setVisual((current) => [...current, await createVisualTemplate(name, config)]);
      else setScripts((current) => [...current, await createScriptTemplate(name, config)]);
      form.reset();
      setMessage("Plantilla creada.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Configuración no válida."); }
  }

  function form(type: "visual" | "script", title: string, example: string) {
    return <section style={{ border: "1px solid #ddd", borderRadius: 10, padding: 16 }}>
      <h2>{title}</h2>
      <form onSubmit={(event) => submit(event, type)} style={{ display: "grid", gap: 8 }}>
        <input name="name" required placeholder="Nombre" />
        <textarea name="configuration" required defaultValue={example} rows={14} spellCheck={false} />
        <button>Guardar plantilla</button>
      </form>
    </section>;
  }

  return <main style={{ padding: 24, fontFamily: "system-ui", maxWidth: 1100 }}>
    <h1>Plantillas</h1><p>Las versiones ya usadas nunca se modifican: crea una nueva versión para cambiar un diseño o un guion.</p>
    <p role="status">{message}</p>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))", gap: 18 }}>
      {form("visual", "Plantilla visual", VISUAL_EXAMPLE)}
      {form("script", "Plantilla de guion", SCRIPT_EXAMPLE)}
    </div>
    <section><h2>Activas</h2><p>Visuales: {visual.map((item) => item.name).join(", ") || "ninguna"}</p><p>Guion: {scripts.map((item) => item.name).join(", ") || "ninguna"}</p></section>
  </main>;
}
