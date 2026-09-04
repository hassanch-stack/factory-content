"use client";

import { FormEvent, useEffect, useState } from "react";
import { Account, ContentItem, createSchedule, getAccounts, getContentQueue, getPosts, Post } from "../../lib/api";

export default function CalendarPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [message, setMessage] = useState("");
  useEffect(() => {
    Promise.all([getPosts(), getAccounts(), getContentQueue("APPROVED")])
      .then(([loadedPosts, loadedAccounts, loadedContent]) => { setPosts(loadedPosts); setAccounts(loadedAccounts); setContent(loadedContent); })
      .catch((error) => setMessage(error.message));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const account = accounts.find((item) => item.id === data.get("account_id"));
    if (!account) return;
    try {
      const post = await createSchedule({
        content_item_id: String(data.get("content_item_id")), account_id: account.id,
        platform: account.platform, scheduled_at: new Date(String(data.get("scheduled_at"))).toISOString(),
      });
      setPosts((current) => [...current, post]);
      setMessage("Publicación programada.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "No se pudo programar."); }
  }

  return <main style={{ padding: 24, fontFamily: "system-ui" }}>
    <h1>Calendario</h1>
    <form onSubmit={submit} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      <select name="content_item_id" required><option value="">Contenido aprobado</option>{content.map((item) => <option key={item.id} value={item.id}>{item.title || item.id}</option>)}</select>
      <select name="account_id" required><option value="">Cuenta</option>{accounts.map((account) => <option key={account.id} value={account.id}>{account.name} · {account.platform}</option>)}</select>
      <input name="scheduled_at" type="datetime-local" required />
      <button>Programar</button>
    </form>
    <p role="status">{message}</p>
    <ul>{posts.map((post) => <li key={post.id}>{new Date(post.scheduled_at).toLocaleString()} · {post.platform} · {post.status}</li>)}</ul>
  </main>;
}
