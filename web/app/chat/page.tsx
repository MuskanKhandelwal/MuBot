"use client";

import { useEffect, useRef, useState } from "react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const SUGGESTIONS = [
  "How many follow-ups are overdue?",
  "What's my reply rate this week?",
  "Show me today's sent emails",
  "What companies are in my pipeline?",
];

function TypingDots() {
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 8 }}>
      {/* Bot avatar */}
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: "50%",
          backgroundColor: "var(--accent-light)",
          border: "1.5px solid var(--border-strong)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 13,
          flexShrink: 0,
        }}
      >
        M
      </div>
      <div
        style={{
          backgroundColor: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "18px 18px 18px 4px",
          padding: "10px 16px",
          display: "flex",
          gap: 4,
          alignItems: "center",
          boxShadow: "0 1px 4px rgba(37,99,235,0.07)",
        }}
      >
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              backgroundColor: "var(--border-strong)",
              display: "inline-block",
              animation: "bounce 1.2s infinite",
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-end",
        gap: 8,
        flexDirection: isUser ? "row-reverse" : "row",
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: "50%",
          backgroundColor: isUser ? "var(--accent)" : "var(--accent-light)",
          border: isUser ? "none" : "1.5px solid var(--border-strong)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 12,
          fontWeight: 700,
          color: isUser ? "#fff" : "var(--accent)",
          flexShrink: 0,
        }}
      >
        {isUser ? "Y" : "M"}
      </div>

      {/* Bubble */}
      <div
        style={{
          maxWidth: "72%",
          padding: "10px 16px",
          borderRadius: isUser
            ? "18px 18px 4px 18px"
            : "18px 18px 18px 4px",
          fontSize: 14,
          lineHeight: 1.55,
          backgroundColor: isUser ? "var(--accent)" : "var(--surface)",
          color: isUser ? "#fff" : "var(--text)",
          border: isUser ? "none" : "1px solid var(--border)",
          boxShadow: "0 1px 4px rgba(37,99,235,0.08)",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {message.content}
      </div>
    </div>
  );
}

function EmptyState({ onSuggest }: { onSuggest: (text: string) => void }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        gap: 20,
        textAlign: "center",
        padding: "0 24px",
      }}
    >
      {/* Icon */}
      <div
        style={{
          width: 64,
          height: 64,
          borderRadius: "50%",
          backgroundColor: "var(--surface)",
          border: "1.5px solid var(--border-strong)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 28,
          boxShadow: "0 4px 16px rgba(37,99,235,0.1)",
        }}
      >
        🤖
      </div>

      <div>
        <h2
          style={{
            margin: "0 0 6px",
            fontSize: 20,
            fontWeight: 700,
            letterSpacing: "-0.3px",
            color: "var(--text)",
          }}
        >
          Ask MuBot
        </h2>
        <p style={{ margin: 0, fontSize: 14, color: "var(--text-muted)", maxWidth: 320 }}>
          Ask about your job search — follow-ups, reply rates, pipeline status, and more.
        </p>
      </div>

      {/* Suggestion chips */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", maxWidth: 420 }}>
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onSuggest(s)}
            style={{
              padding: "7px 14px",
              borderRadius: 99,
              fontSize: 13,
              fontWeight: 500,
              backgroundColor: "var(--surface)",
              color: "var(--accent)",
              border: "1.5px solid var(--border-strong)",
              cursor: "pointer",
              transition: "background 0.15s, border-color 0.15s",
              fontFamily: "inherit",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.backgroundColor = "var(--accent-light)";
              (e.currentTarget as HTMLElement).style.borderColor = "var(--accent)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface)";
              (e.currentTarget as HTMLElement).style.borderColor = "var(--border-strong)";
            }}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    const botId = crypto.randomUUID();
    const botMsg: Message = { id: botId, role: "assistant", content: "" };

    setMessages((prev) => [...prev, userMsg, botMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          history: messages.map((m) => ({ role: m.role, content: m.content })),
        }),
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No response body");

      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6).trim();
          if (payload === "[DONE]") break;
          try {
            const parsed = JSON.parse(payload);
            if (parsed.error) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === botId ? { ...m, content: `Error: ${parsed.error}` } : m
                )
              );
            } else if (parsed.delta) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === botId ? { ...m, content: m.content + parsed.delta } : m
                )
              );
            }
          } catch {
            // skip malformed SSE line
          }
        }
      }
    } catch (e) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === botId
            ? { ...m, content: `Something went wrong: ${e instanceof Error ? e.message : "Unknown error"}` }
            : m
        )
      );
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    sendMessage(input);
  }

  return (
    <>
      {/* bounce animation */}
      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-5px); }
        }
      `}</style>

      <div
        style={{
          height: "calc(100vh - 120px)",
          display: "flex",
          flexDirection: "column",
          backgroundColor: "var(--surface)",
          borderRadius: 18,
          border: "1px solid var(--border)",
          boxShadow: "0 4px 24px rgba(37,99,235,0.08)",
          overflow: "hidden",
        }}
      >
        {/* Chat header */}
        <div
          style={{
            padding: "14px 20px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            gap: 10,
            backgroundColor: "var(--surface-2)",
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: "50%",
              backgroundColor: "var(--accent)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#fff",
              fontWeight: 700,
              fontSize: 14,
            }}
          >
            M
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>
              MuBot
            </div>
            <div style={{ fontSize: 11, color: "var(--good)", fontWeight: 500 }}>
              ● online
            </div>
          </div>
        </div>

        {/* Messages */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "20px 20px 8px",
          }}
        >
          {messages.length === 0 ? (
            <EmptyState onSuggest={(s) => sendMessage(s)} />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {messages.map((msg) =>
                msg.role === "assistant" && msg.content === "" ? (
                  <TypingDots key={msg.id} />
                ) : (
                  <MessageBubble key={msg.id} message={msg} />
                )
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input bar */}
        <form
          onSubmit={handleSubmit}
          style={{
            padding: "12px 16px",
            borderTop: "1px solid var(--border)",
            display: "flex",
            gap: 10,
            alignItems: "center",
            backgroundColor: "var(--surface)",
          }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask MuBot anything…"
            disabled={loading}
            autoFocus
            style={{
              flex: 1,
              height: 40,
              padding: "0 14px",
              borderRadius: 99,
              border: "1.5px solid var(--border-strong)",
              backgroundColor: "var(--surface-2)",
              color: "var(--text)",
              fontSize: 14,
              fontFamily: "inherit",
              outline: "none",
              transition: "border-color 0.15s",
            }}
            onFocus={(e) => {
              (e.currentTarget as HTMLElement).style.borderColor = "var(--accent)";
            }}
            onBlur={(e) => {
              (e.currentTarget as HTMLElement).style.borderColor = "var(--border-strong)";
            }}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            style={{
              width: 40,
              height: 40,
              borderRadius: "50%",
              backgroundColor:
                loading || !input.trim() ? "var(--border)" : "var(--accent)",
              color: "#fff",
              border: "none",
              cursor: loading || !input.trim() ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 18,
              flexShrink: 0,
              transition: "background 0.15s",
            }}
          >
            ↑
          </button>
        </form>
      </div>
    </>
  );
}
