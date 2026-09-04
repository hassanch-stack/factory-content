"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AIGeneration,
  enqueueRenders,
  rewriteScript,
  getContentAssets,
  getScriptTemplates,
  getVisualTemplates,
  MediaAsset,
  ScriptTemplate,
  updateGeneration,
  VisualTemplate,
} from "../../../lib/api";

export default function ContentEditor({ contentId }: { contentId: string }) {
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [scriptTemplates, setScriptTemplates] = useState<ScriptTemplate[]>([]);
  const [visualTemplates, setVisualTemplates] = useState<VisualTemplate[]>([]);
  const [scriptTemplateId, setScriptTemplateId] = useState("");
  const [templateIds, setTemplateIds] = useState<string[]>([]);
  const [generation, setGeneration] = useState<AIGeneration | null>(null);
  const [scriptJson, setScriptJson] = useState("");
  const [message, setMessage] = useState("Cargando opciones…");
  const [busy, setBusy] = useState(false);

  const original = useMemo(
    () => assets.find((asset) => asset.asset_type === "original"),
    [assets]
  );

  useEffect(() => {
    Promise.all([getContentAssets(contentId), getScriptTemplates(), getVisualTemplates()])
      .then(([loadedAssets, loadedScriptTemplates, loadedVisualTemplates]) => {
        setAssets(loadedAssets);
        setScriptTemplates(loadedScriptTemplates);
        setVisualTemplates(loadedVisualTemplates);
        setScriptTemplateId(loadedScriptTemplates[0]?.id ?? "");
        setMessage("");
      })
      .catch((error) => setMessage(error instanceof Error ? error.message : "No se pudo cargar el editor."));
  }, [contentId]);

  async function createScript() {
    if (!scriptTemplateId) return setMessage("Crea o selecciona una plantilla de guion primero.");
    setBusy(true);
    try {
      const created = await rewriteScript(contentId, scriptTemplateId);
      setGeneration(created);
      setScriptJson(JSON.stringify(created.output_json, null, 2));
      setMessage("Guion reescrito. Revísalo y edítalo antes de renderizar.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo reescribir el guion.");
    } finally {
      setBusy(false);
    }
  }

  async function saveScript() {
    if (!generation) return;
    try {
      const saved = await updateGeneration(generation.id, JSON.parse(scriptJson));
      setGeneration(saved);
      setMessage("Guion guardado.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "El JSON del guion no es válido.");
    }
  }

  async function render() {
    if (!original) return setMessage("Falta la foto original.");
    if (!generation) return setMessage("Reescribe y revisa el guion antes de renderizar.");
    if (!templateIds.length) return setMessage("Selecciona al menos una plantilla visual.");
    setBusy(true);
    try {
      await enqueueRenders(
        templateIds.map((templateId, slideIndex) => ({
          content_item_id: contentId,
          template_id: templateId,
          input_asset_id: original.id,
          slide_index: slideIndex,
        }))
      );
      setMessage("Render enviado. Cuando terminen todas las diapositivas, pasará a revisión.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo iniciar el render.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: "system-ui", maxWidth: 960 }}>
      <h1>Editor de contenido</h1>
      <p>Flujo: aporta un guion original, reescríbelo, revísalo y elige las diapositivas visuales.</p>

      <section style={{ display: "grid", gap: 10, border: "1px solid #ddd", borderRadius: 10, padding: 16 }}>
        <h2 style={{ margin: 0 }}>1. Guion</h2>
        <label>
          Plantilla de guion
          <select value={scriptTemplateId} onChange={(event) => setScriptTemplateId(event.target.value)}>
            <option value="">Selecciona una plantilla</option>
            {scriptTemplates.map((template) => <option key={template.id} value={template.id}>{template.name}</option>)}
          </select>
        </label>
        <button disabled={busy || !scriptTemplateId} onClick={createScript}>Reescribir guion con IA</button>
        {generation && (
          <>
            <textarea value={scriptJson} onChange={(event) => setScriptJson(event.target.value)} rows={18} spellCheck={false} />
            <button disabled={busy} onClick={saveScript}>Guardar edición</button>
          </>
        )}
      </section>

      <section style={{ display: "grid", gap: 10, border: "1px solid #ddd", borderRadius: 10, padding: 16, marginTop: 18 }}>
        <h2 style={{ margin: 0 }}>2. Render</h2>
        <p>Selecciona las plantillas en el orden del carrusel.</p>
        {visualTemplates.map((template) => (
          <label key={template.id}>
            <input
              type="checkbox"
              checked={templateIds.includes(template.id)}
              onChange={(event) => setTemplateIds((current) => event.target.checked
                ? [...current, template.id]
                : current.filter((id) => id !== template.id))}
            /> {template.name} (v{template.version})
          </label>
        ))}
        <button disabled={busy || !generation || !original || !templateIds.length} onClick={render}>
          Crear render
        </button>
      </section>

      {message && <p role="status" style={{ marginTop: 16 }}>{message}</p>}
    </main>
  );
}
