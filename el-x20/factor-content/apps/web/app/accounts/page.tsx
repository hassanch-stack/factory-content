"use client";

import { FormEvent, useEffect, useState } from "react";
import { Account, createAccount, getAccounts } from "../../lib/api";

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => { getAccounts().then(setAccounts).catch((error) => setMessage(error.message)); }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    try {
      const account = await createAccount({
        name: String(data.get("name")), platform: String(data.get("platform")),
        username: String(data.get("username")) || null, timezone: String(data.get("timezone")),
        publishing_enabled: false,
      });
      setAccounts((current) => [...current, account]);
      event.currentTarget.reset();
      setMessage("Cuenta añadida. La publicación queda desactivada hasta conectar sus credenciales oficiales.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo crear la cuenta."); }
  }

  return <main style={{ padding: 24, fontFamily: "system-ui" }}>
    <h1>Cuentas</h1>
    <p>Las credenciales no se introducen aquí: se conectan exclusivamente mediante el flujo oficial de cada plataforma.</p>
    <form onSubmit={submit} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      <input name="name" required placeholder="Nombre" />
      <select name="platform" defaultValue="INSTAGRAM"><option>INSTAGRAM</option><option>FACEBOOK</option><option>TIKTOK</option></select>
      <input name="username" placeholder="Usuario (opcional)" />
      <input name="timezone" defaultValue="Europe/Madrid" required />
      <button>Añadir cuenta</button>
    </form>
    <p role="status">{message}</p>
    <ul>{accounts.map((account) => <li key={account.id}>{account.name} · {account.platform} · publicación {account.publishing_enabled ? "activa" : "desactivada"}</li>)}</ul>
  </main>;
}
