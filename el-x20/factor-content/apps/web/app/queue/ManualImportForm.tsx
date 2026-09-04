"use client";

import { FormEvent, useRef, useState } from "react";
import { importManualContent } from "../../lib/api";

const RIGHTS_OPTIONS = [
  ["UNKNOWN", "Pendiente de confirmar"],
  ["AUTHORIZED", "Autorizado"],
  ["LICENSED", "Con licencia"],
  ["PUBLIC_DOMAIN", "Dominio público"],
  ["PLATFORM_SUPPORTED", "Permitido por la plataforma"],
] as const;

export default function ManualImportForm() {
  const formRef = useRef<HTMLFormElement>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const file = form.elements.namedItem("file") as HTMLInputElement | null;
    if (!file?.files?.[0]) {
      setStatus("error");
      setMessage("Selecciona una foto antes de continuar.");
      return;
    }

    setStatus("uploading");
    setMessage("");
    try {
      const imported = await importManualContent(new FormData(form));
      setStatus("success");
      setMessage(`Importada: ${imported.title || file.files[0].name}. Ya está en la cola.`);
      formRef.current?.reset();
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "No se pudo importar la foto.");
    }
  }

  return (
    <section style={{ border: "1px solid #d5d9e2", borderRadius: 12, padding: 20 }}>
      <h2 style={{ marginTop: 0 }}>Paso 2 · Importar una foto</h2>
      <p>Sube manualmente el contenido que quieres procesar. Se aceptan JPEG, PNG y WebP (máximo 20 MB).</p>
      <form ref={formRef} onSubmit={handleSubmit} style={{ display: "grid", gap: 12, maxWidth: 620 }}>
        <label>
          Foto
          <input name="file" type="file" accept="image/jpeg,image/png,image/webp" required />
        </label>
        <label>
          Título (opcional)
          <input name="title" type="text" style={{ display: "block", width: "100%" }} />
        </label>
        <label>
          Guion o texto original a reescribir
          <textarea name="original_script" rows={6} required style={{ display: "block", width: "100%" }} />
        </label>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <label>
            Categoría
            <input name="category" type="text" />
          </label>
          <label>
            Idioma
            <input name="language" type="text" placeholder="es" />
          </label>
          <label>
            Derechos
            <select name="rights_status" defaultValue="UNKNOWN">
              {RIGHTS_OPTIONS.map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </label>
        </div>
        <button type="submit" disabled={status === "uploading"} style={{ width: "fit-content" }}>
          {status === "uploading" ? "Importando…" : "Importar foto"}
        </button>
        {message && (
          <p role="status" style={{ color: status === "error" ? "#b42318" : "#027a48", margin: 0 }}>
            {message}
          </p>
        )}
      </form>
    </section>
  );
}
