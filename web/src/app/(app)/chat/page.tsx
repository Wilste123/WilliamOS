"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useRef, useState } from "react";

import { fetchMe, streamChat, type ChatStreamEvent } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: unknown[];
};

const CHAT_STORAGE_KEY = "mini_jarv_chat_history";
const QUICK_ACTIONS = [
  "Hva bør jeg gjøre i dag?",
  "Oppsummer eiendelene mine",
  "Hva bør jeg gjøre denne uka?",
];

function statusLabel(assistantName: string, phase: string | null): string {
  if (phase === "tools") return `${assistantName} bruker verktøy…`;
  return `${assistantName} tenker…`;
}

function loadStoredMessages(): Message[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = sessionStorage.getItem(CHAT_STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as Message[];
  } catch {
    return [];
  }
}

function ChatPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [assistantName, setAssistantName] = useState("Mini-jarv");
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const bootstrapped = useRef(false);

  useEffect(() => {
    setMessages(loadStoredMessages());
    fetchMe().then((me) => setAssistantName(me.assistant_name ?? "Mini-jarv"));
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages.slice(-40)));
  }, [messages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, phase]);

  useEffect(() => {
    const prompt = searchParams.get("prompt");
    if (!prompt || bootstrapped.current) return;
    bootstrapped.current = true;
    setInput(prompt);
  }, [searchParams]);

  async function sendMessage(userMessage: string) {
    if (!userMessage.trim() || loading) return;

    const nextMessages: Message[] = [...messages, { role: "user", content: userMessage.trim() }];
    setMessages(nextMessages);
    setLoading(true);
    setPhase("thinking");
    setStreaming(false);

    let assistant = "";
    let sources: unknown[] = [];
    let sawToken = false;

    try {
      await streamChat(
        userMessage.trim(),
        nextMessages.map((m) => ({ role: m.role, content: m.content })),
        (event: ChatStreamEvent) => {
          if (event.type === "status") {
            setPhase(event.phase);
            return;
          }
          if (event.type === "token") {
            sawToken = true;
            setStreaming(true);
            assistant += event.text;
            setPhase(null);
            setMessages([...nextMessages, { role: "assistant", content: assistant, sources }]);
            return;
          }
          if (event.type === "done") {
            sources = event.sources ?? [];
            if (assistant) {
              setMessages([...nextMessages, { role: "assistant", content: assistant, sources }]);
            }
            return;
          }
          if (event.type === "error") {
            setMessages([
              ...nextMessages,
              {
                role: "assistant",
                content: event.message || "Beklager, noe gikk galt. Sjekk at API-et kjører.",
              },
            ]);
          }
        }
      );
      if (!sawToken && !assistant) {
        setMessages([
          ...nextMessages,
          { role: "assistant", content: "Ingen respons fra assistenten." },
        ]);
      }
    } catch {
      setMessages([
        ...nextMessages,
        { role: "assistant", content: "Beklager, noe gikk galt. Sjekk at API-et kjører." },
      ]);
    } finally {
      setLoading(false);
      setPhase(null);
      setStreaming(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const userMessage = input.trim();
    if (!userMessage) return;
    setInput("");
    if (searchParams.get("prompt")) {
      router.replace("/chat");
    }
    await sendMessage(userMessage);
  }

  const showThinking = loading && phase !== null && !streaming;

  return (
    <div className="flex h-[calc(100dvh-9rem)] flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Chat med {assistantName}</h1>
        <p className="text-sm text-muted">Spør om oppgaver, eiendeler, prosjekter og mer.</p>
      </div>

      {messages.length === 0 && (
        <div className="flex flex-wrap gap-2">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action}
              type="button"
              onClick={() => sendMessage(action)}
              className="rounded-full border border-border px-3 py-1.5 text-xs text-muted hover:border-accent hover:text-accent"
            >
              {action}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 space-y-3 overflow-y-auto rounded-2xl border border-border p-4">
        {messages.length === 0 && (
          <p className="text-sm text-muted">Start en samtale med assistenten din.</p>
        )}
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`max-w-[90%] ${message.role === "user" ? "ml-auto" : ""}`}>
            <div
              className={`rounded-2xl px-4 py-3 text-sm ${
                message.role === "user" ? "bg-accent text-white" : "bg-zinc-900"
              }`}
            >
              {message.content}
              {message.role === "assistant" &&
                loading &&
                index === messages.length - 1 &&
                streaming && (
                  <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-accent align-middle" />
                )}
            </div>
            {message.role === "assistant" && message.sources && message.sources.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {message.sources.slice(0, 3).map((source, sourceIndex) => (
                  <span
                    key={sourceIndex}
                    className="rounded-full bg-zinc-800 px-2 py-0.5 text-[10px] text-muted"
                  >
                    {typeof source === "object" && source && "filename" in source
                      ? String((source as { filename?: string }).filename)
                      : "Dokument"}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {showThinking && (
          <p className="text-sm text-muted">{statusLabel(assistantName, phase)}</p>
        )}
        <div ref={bottomRef} />
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

export default function ChatPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted">Laster chat…</p>}>
      <ChatPageInner />
    </Suspense>
  );
}
