"use client";

import { Bot, RotateCcw, User } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type ChatTurn = { role: "user" | "assistant"; content: string };

const MAX_HISTORY = 10;

// The model has no legitimate reason to emit image markdown, but if it ever
// does (hallucination or prompt injection via tool output), never render it.
const MARKDOWN_COMPONENTS = { img: () => null };

function Avatar({ role }: { role: "user" | "assistant" }) {
  return (
    <div
      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
        role === "user"
          ? "bg-[var(--series-google)] text-white"
          : "bg-[var(--surface-2)] text-[var(--text-secondary)]"
      }`}
    >
      {role === "user" ? <User size={16} /> : <Bot size={16} />}
    </div>
  );
}

export default function ChatBox() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "streaming">("idle");
  const [error, setError] = useState("");
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [turns, status]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const message = input.trim();
    if (!message || status !== "idle") return;

    const history = turns.slice(-MAX_HISTORY);
    setTurns((prev) => [...prev, { role: "user", content: message }]);
    setInput("");
    setStatus("loading");
    setError("");

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history }),
        signal: controller.signal,
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? "Something went wrong.");
      }

      await consumeStream(res.body!, controller.signal);
      setStatus("idle");
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setStatus("idle");
        return;
      }
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setStatus("idle");
    } finally {
      abortRef.current = null;
    }
  }

  async function consumeStream(body: ReadableStream<Uint8Array>, signal: AbortSignal) {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let started = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (signal.aborted) {
        await reader.cancel();
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const event = JSON.parse(line.slice("data: ".length));

        if (event.type === "token") {
          if (!started) {
            started = true;
            setStatus("streaming");
            setTurns((prev) => [...prev, { role: "assistant", content: "" }]);
          }
          setTurns((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              role: "assistant",
              content: next[next.length - 1].content + event.text,
            };
            return next;
          });
        } else if (event.type === "error") {
          setError(event.message);
        }
      }
    }
  }

  function handleStop() {
    abortRef.current?.abort();
  }

  function handleReset() {
    abortRef.current?.abort();
    setTurns([]);
    setInput("");
    setError("");
    setStatus("idle");
  }

  const isBusy = status !== "idle";

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-6">
      {turns.length > 0 ? (
        <div className="mb-3 flex justify-end">
          <button
            type="button"
            onClick={handleReset}
            className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium text-[var(--text-secondary)] transition hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)]"
          >
            <RotateCcw size={13} />
            Clear chat
          </button>
        </div>
      ) : null}
      <div ref={scrollRef} className="flex max-h-96 flex-col gap-3 overflow-y-auto">
        {turns.length === 0 ? (
          <p className="text-sm text-[var(--text-secondary)]">
            Ask a question about ads and ads performance, e.g. &ldquo;Which ad had the highest CTR last
            month?&rdquo;
          </p>
        ) : (
          turns.map((turn, i) => (
            <div
              key={i}
              className={`flex items-end gap-2 ${turn.role === "user" ? "flex-row-reverse self-end" : "self-start"}`}
            >
              <Avatar role={turn.role} />
              <div
                className={`max-w-[80%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
                  turn.role === "user"
                    ? "bg-[var(--chat-user-bg)] text-[var(--chat-user-text)]"
                    : "bg-[var(--surface-2)]"
                }`}
              >
                {turn.role === "assistant" ? (
                  <div className="prose-chat">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={MARKDOWN_COMPONENTS}>
                      {turn.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  turn.content
                )}
              </div>
            </div>
          ))
        )}
        {status === "loading" ? (
          <div className="flex items-end gap-2 self-start">
            <Avatar role="assistant" />
            <div className="rounded-lg bg-[var(--surface-2)] px-3 py-2 text-sm text-[var(--text-secondary)]">
              Thinking…
            </div>
          </div>
        ) : null}
      </div>

      {error ? <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p> : null}

      <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Dig deeper into the data…"
          maxLength={1000}
          disabled={isBusy}
          className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface-2)] px-3 py-2.5 text-sm outline-none transition focus:border-[var(--border-strong)] disabled:opacity-50"
        />
        {isBusy ? (
          <button
            type="button"
            onClick={handleStop}
            className="rounded-lg border border-[var(--border)] px-4 py-2.5 text-sm font-medium transition hover:bg-[var(--surface-2)]"
          >
            Stop
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            className="rounded-lg bg-[var(--text-primary)] px-4 py-2.5 text-sm font-medium text-[var(--surface-page)] transition hover:opacity-90 disabled:opacity-50"
          >
            Ask
          </button>
        )}
      </form>
    </div>
  );
}
