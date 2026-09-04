"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [message, setMessage] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const token = String(new FormData(event.currentTarget).get("token") || "").trim();
    if (!token) return setMessage("Introduce el token de operador.");
    window.localStorage.setItem("factor_operator_token", token);
    router.push("/queue");
  }

  return <main style={{ padding: 24, fontFamily: "system-ui", maxWidth: 440 }}>
    <h1>Acceso de operador</h1>
    <p>Introduce el valor configurado como <code>AUTH_SECRET</code>. En producción activa <code>AUTH_REQUIRED=true</code>.</p>
    <form onSubmit={submit} style={{ display: "grid", gap: 12 }}>
      <input name="token" type="password" autoComplete="current-password" placeholder="Token de operador" />
      <button>Entrar</button>
    </form>
    <p role="status">{message}</p>
  </main>;
}
