# Voice chat MVP (spike)

## Scope

Opt-in **stemmemodus** on the chat page (`web/src/app/(app)/chat/page.tsx`). Default chat is unchanged when the toggle is off.

Pipeline (phase 1):

1. Browser **SpeechRecognition** (Web Speech API) for STT
2. Existing **`streamChat`** SSE flow (same as typed messages)
3. Browser **SpeechSynthesis** for TTS on the **final** assistant reply only

## UI states

`idle` → `listening` → `processing` → `speaking` → `idle`

Starting a new listening session **cancels** ongoing TTS (basic barge-in).

## Limitations

- Requires a browser with both STT and TTS (Chrome desktop is the primary target).
- **Safari / iOS**: limited or missing `SpeechRecognition`; users see a Norwegian fallback message.
- Language is set to `nb-NO`; recognition quality varies by browser.
- No OpenAI Realtime API, WebRTC, or phone integration in this spike.

## Files

- `web/src/lib/use-voice-chat.ts` — hook
- `web/src/components/VoiceChatControls.tsx` — opt-in panel UI
