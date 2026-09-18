"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type VoiceChatState = "idle" | "listening" | "processing" | "speaking" | "unsupported";

type SpeechRecognitionCtor = new () => SpeechRecognitionInstance;

type SpeechRecognitionInstance = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: SpeechRecognitionResultEvent) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
};

type SpeechRecognitionResultEvent = {
  resultIndex: number;
  results: {
    length: number;
    [index: number]: {
      isFinal: boolean;
      [index: number]: { transcript: string };
    };
  };
};

function getSpeechRecognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as Window & {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

function hasSpeechSynthesis(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

export function useVoiceChat(onTranscript: (text: string) => Promise<string | null>) {
  const [state, setState] = useState<VoiceChatState>("idle");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const pendingTranscriptRef = useRef<string | null>(null);
  const onTranscriptRef = useRef(onTranscript);
  onTranscriptRef.current = onTranscript;

  const sttSupported = typeof window !== "undefined" && getSpeechRecognitionCtor() !== null;
  const ttsSupported = hasSpeechSynthesis();
  const supported = sttSupported && ttsSupported;

  useEffect(() => {
    if (!supported) {
      setState("unsupported");
    }
  }, [supported]);

  const stopSpeaking = useCallback(() => {
    if (!hasSpeechSynthesis()) return;
    window.speechSynthesis.cancel();
  }, []);

  const speak = useCallback(async (text: string) => {
    if (!hasSpeechSynthesis() || !text.trim()) {
      setState("idle");
      return;
    }
    stopSpeaking();
    setState("speaking");
    const utterance = new SpeechSynthesisUtterance(text.trim());
    utterance.lang = "nb-NO";
    await new Promise<void>((resolve) => {
      utterance.onend = () => resolve();
      utterance.onerror = () => resolve();
      window.speechSynthesis.speak(utterance);
    });
    setState("idle");
  }, [stopSpeaking]);

  const processTranscript = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) {
        setState("idle");
        return;
      }
      setInterimTranscript("");
      setState("processing");
      setVoiceError(null);
      try {
        const reply = await onTranscriptRef.current(trimmed);
        if (reply?.trim()) {
          await speak(reply);
        } else {
          setState("idle");
        }
      } catch {
        setVoiceError("Kunne ikke sende stemmemeldingen.");
        setState("idle");
      }
    },
    [speak]
  );

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
  }, []);

  const startListening = useCallback(() => {
    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) {
      setState("unsupported");
      return;
    }

    stopSpeaking();
    setVoiceError(null);
    setInterimTranscript("");

    const recognition = new Ctor();
    recognition.lang = "nb-NO";
    recognition.continuous = false;
    recognition.interimResults = true;
    recognitionRef.current = recognition;

    recognition.onresult = (event) => {
      let interim = "";
      let finalText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0]?.transcript ?? "";
        if (result.isFinal) {
          finalText += transcript;
        } else {
          interim += transcript;
        }
      }
      if (interim) setInterimTranscript(interim);
      if (finalText) {
        pendingTranscriptRef.current = finalText;
      }
    };

    recognition.onerror = (event) => {
      if (event.error === "aborted" || event.error === "no-speech") {
        setState("idle");
        return;
      }
      setVoiceError("Stemmegjenkjenning feilet. Prøv igjen.");
      setState("idle");
    };

    recognition.onend = () => {
      recognitionRef.current = null;
      const pending = pendingTranscriptRef.current;
      pendingTranscriptRef.current = null;
      if (pending) {
        void processTranscript(pending);
      } else {
        setState("idle");
      }
    };

    try {
      setState("listening");
      recognition.start();
    } catch {
      setVoiceError("Kunne ikke starte mikrofonen.");
      setState("idle");
    }
  }, [processTranscript, stopSpeaking]);

  const toggleListening = useCallback(() => {
    if (state === "listening") {
      stopListening();
      return;
    }
    if (state === "processing" || state === "speaking") {
      return;
    }
    startListening();
  }, [state, startListening, stopListening]);

  const cancelVoice = useCallback(() => {
    recognitionRef.current?.abort();
    recognitionRef.current = null;
    pendingTranscriptRef.current = null;
    stopSpeaking();
    setInterimTranscript("");
    setState(supported ? "idle" : "unsupported");
  }, [stopSpeaking, supported]);

  return {
    state,
    interimTranscript,
    voiceError,
    supported,
    sttSupported,
    ttsSupported,
    startListening,
    stopListening,
    toggleListening,
    cancelVoice,
    stopSpeaking,
  };
}
