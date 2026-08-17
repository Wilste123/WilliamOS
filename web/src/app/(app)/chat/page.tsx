"use client";

import { FormEvent, useEffect, useState } from "react";

import { fetchMe, sendChat } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [assistantName, setAssistantName] = useState("WilliamOS");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchMe().then((me) => setAssistantName(me.assistant_name ?? "WilliamOS"));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    const nextMessages: Message[] = [...messages, { role: "user", content: userMessage }];
    setMessages(nextMessages);
    setLoading(true);

    try {
      const response = await sendChat(
        userMessage,
        nextMessages.map((m) => ({ role: m.role, content: m.content }))
      );
      setMessages([...nextMessages, { role: "assistant", content: response.answer }]);
    } catch {
      setMessages([
        ...nextMessages,
        { role: "assistant", content: "Beklager, noe gikk galt. Sjekk at API-et kjører." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-[calc(100dvh-9rem)] flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Chat med {assistantName}</h1>
        <p className="text-sm text-muted">Spør om oppgaver, eiendeler, prosjekter og mer.</p>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto rounded-2xl border border-border p-4">
        {messages.length === 0 && (
          <p className="text-sm text-muted">Start en samtale med assistenten din.</p>
        )}
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm ${
              message.role === "user" ? "ml-auto bg-accent text-white" : "bg-zinc-900"
            }`}
          >
            {message.content}
          </div>
        ))}
        {loading && <p className="text-sm text-muted">{assistantName} tenker…</p>}
      </div>

      <form onSubmit={onSubmit} className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Skriv en melding…"
          className="flex-1 rounded-xl border border-border bg-transparent px-4 py-3"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-xl bg-accent px-4 py-3 font-medium text-white disabled:opacity-60"
        >
          Send
        </button>
      </form>
    </div>
  );
}
