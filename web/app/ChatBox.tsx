"use client";

import { useState, type FormEvent } from "react";

type ChatTurn = { role: "user" | "assistant"; content: string };

const MAX_HISTORY = 10;

export default function ChatBox() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"idle" | "loading">("idle");
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const message = input.trim();
    if (!message || status === "loading") return;

    const history = turns.slice(-MAX_HISTORY);
    setTurns((prev) => [...prev, { role: "user", content: message }]);
    setInput("");
    setStatus("loading");
    setError("");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Something went wrong.");
      setTurns((prev) => [...prev, { role: "assistant", content: data.message }]);
      setStatus("idle");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setStatus("idle");
    }
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-6">
      <div className="flex max-h-96 flex-col gap-3 overflow-y-auto">
        {turns.length === 0 ? (
          <p className="text-sm text-[var(--text-secondary)]">
            Ask a question about ad performance, e.g. &ldquo;Which ad had the highest CTR last
            month?&rdquo;
          </p>
        ) : (
          turns.map((turn, i) => (
            <div
              key={i}
              className={`max-w-[80%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
                turn.role === "user"
                  ? "self-end bg-[var(--text-primary)] text-[var(--surface-page)]"
                  : "self-start bg-[var(--surface-2)]"
              }`}
            >
              {turn.content}
            </div>
          ))
        )}
        {status === "loading" ? (
          <div className="self-start rounded-lg bg-[var(--surface-2)] px-3 py-2 text-sm text-[var(--text-secondary)]">
            Thinking…
          </div>
        ) : null}
      </div>

      {error ? <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p> : null}

      <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about ad performance…"
          maxLength={1000}
          disabled={status === "loading"}
          className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2.5 text-sm outline-none transition focus:border-[var(--border-strong)] disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={status === "loading" || !input.trim()}
          className="rounded-lg bg-[var(--text-primary)] px-4 py-2.5 text-sm font-medium text-[var(--surface-page)] transition hover:opacity-90 disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
