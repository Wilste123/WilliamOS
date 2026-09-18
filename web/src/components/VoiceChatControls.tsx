"use client";

import { useVoiceChat, type VoiceChatState } from "@/lib/use-voice-chat";

const STATE_LABELS: Record<VoiceChatState, string> = {
  idle: "Klar",
  listening: "Lytter…",
  processing: "Behandler…",
  speaking: "Snakker…",
  unsupported: "Ikke støttet",
};

type VoiceChatControlsProps = {
  active: boolean;
  disabled?: boolean;
  onTranscript: (text: string) => Promise<string | null>;
};

export function VoiceChatControls({ active, disabled, onTranscript }: VoiceChatControlsProps) {
  const {
    state,
    interimTranscript,
    voiceError,
    supported,
    sttSupported,
    ttsSupported,
    toggleListening,
    cancelVoice,
  } = useVoiceChat(onTranscript);

  if (!active) return null;

  if (!supported) {
    return (
      <div
        className="rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100"
        role="status"
      >
        Stemmemodus er ikke tilgjengelig i denne nettleseren.
        {!sttSupported && " Talegjenkjenning (STT) mangler."}
        {!ttsSupported && " Tale-syntese (TTS) mangler."}
        Safari på iOS har begrenset støtte — bruk Chrome på desktop for best resultat.
      </div>
    );
  }

  const busy = state === "processing" || state === "speaking";
  const listening = state === "listening";

  return (
    <div className="rounded-xl border border-border bg-zinc-950/50 px-4 py-3">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={disabled || busy}
          onClick={() => toggleListening()}
          className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-lg transition ${
            listening
              ? "bg-red-500 text-white animate-pulse"
              : "bg-accent text-white hover:opacity-90 disabled:opacity-50"
          }`}
          aria-label={listening ? "Stopp lytting" : "Start stemmemelding"}
          title={listening ? "Stopp lytting" : "Snakk"}
        >
          {listening ? "■" : "🎤"}
        </button>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-foreground">{STATE_LABELS[state]}</p>
          {interimTranscript && listening && (
            <p className="truncate text-xs text-muted">&ldquo;{interimTranscript}&rdquo;</p>
          )}
          {voiceError && <p className="text-xs text-red-400">{voiceError}</p>}
        </div>
        {(listening || busy) && (
          <button
            type="button"
            onClick={() => cancelVoice()}
            className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted hover:text-foreground"
          >
            Avbryt
          </button>
        )}
      </div>
      <p className="mt-2 text-[11px] text-muted">
        Stemmemodus er valgfritt. Tekstchat fungerer som før. Trykk mikrofon, snakk, og vent på svar.
      </p>
    </div>
  );
}
