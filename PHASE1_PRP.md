# Brum Phase 1 — Product Requirements Prompt (PRP)

> **How to use:** Edit anything marked `[CUSTOMIZE]`. Keep or delete options in lists. Send the filled version back to Spider so build matches your intent.
> **Status:** Draft for customization — not locked until you return it.
> **Date:** 2026-09-05

---

## 0. One-liner

Brum Phase 1 is a **pure speech-to-speech** browser voice assistant over **my knowledge base**: talk in → grounded spoken answer out, with **cite or refuse** — deployed live for a small set of real users.

---

## 1. Problem

[CUSTOMIZE — why this exists]

People (starting with me) need to **talk** to their notes/docs and get answers that are **only** from that corpus — not generic LLM chatter. Typing RAG demos don’t feel like a product. Cascaded STT→LLM→TTS feels robotic; Phase 1 must feel like a **conversation**.

**Jobs to be done**
1. Ask by voice what’s in my uploaded knowledge.
2. Hear a natural spoken answer grounded in that knowledge.
3. Know when Brum **doesn’t know** (refuse) instead of hallucinating.
4. See which sources backed the answer (UI), even if speech doesn’t read every citation.

---

## 2. Non-goals (Phase 1)

Explicitly **out** unless you move them into goals:

- [ ] Cascaded STT → LLM → TTS as the primary path
- [ ] Fine-tuning / training on dumps
- [ ] Multi-tenant company Brum / role lenses
- [ ] Notion OAuth sync
- [ ] Mobile native app
- [ ] Phone/SIP telephony
- [ ] Multi-user shared company brain (Phase 2+)
- [ ] Avatar / digital human video

[CUSTOMIZE — add/remove]

---

## 3. Users

| Role | Who | What they do |
|------|-----|--------------|
| Primary | Preetam | Upload KB, talk to Brum daily, demo to employers |
| Secondary | [CUSTOMIZE: friends / teammates / N people] | Use live URL with shared or per-user KB |

**Success user count (Phase 1):** [CUSTOMIZE: e.g. 3–5 people for 1 week]

---

## 4. Experience (must feel like this)

### Voice mode — **pure speech-to-speech**

- Audio in → realtime multimodal / speech-to-speech model → audio out.
- **No** separate Whisper-then-TTS happy path (cascade is fallback only if S2S blocked).
- Natural turn-taking: [CUSTOMIZE: push-to-talk **or** always-listening with barge-in].
- Latency target: [CUSTOMIZE: e.g. first audio &lt; 800ms when possible].

### Knowledge behavior

- Answers **only** from retrieved KB for knowledge questions.
- If retrieval empty / below threshold → **spoken refuse** (short, clear).
- UI shows **citation chips** (doc title / chunk id) from tool results.
- Spoken cites: [CUSTOMIZE: optional light “from your notes on X” **or** silent cites UI-only].

### Text side-channel (optional)

- [CUSTOMIZE: yes/no] Show live transcript + text answer alongside audio.
- Useful for debugging grounding and for resume demos.

---

## 5. Functional requirements

### Must have (P0)

1. **Browser mic** over WebRTC (or equivalent realtime transport).
2. **Pure S2S** conversation loop with a realtime voice model.
3. **KB ingest:** upload markdown and/or PDF → chunk → embed → vector store.
4. **`search_kb` tool** (or equivalent) the voice model can call mid-turn.
5. **Cite-or-refuse:** grounded speak if hits; refuse if not.
6. **Live deploy** — one public URL (auth-lite OK).
7. **Small real users** can complete: upload → ask by voice → hear grounded or refused reply.

### Should have (P1)

- Upload UI + list of documents in workspace.
- Citation panel in UI tied to last turn.
- Simple auth (magic link / shared password / per-user API key).
- Basic logs: answered vs refused, latency, tool calls.

### Nice (P2)

- Prefetch / semantic cache for RAG latency (VoiceAgentRAG-style).
- Multiple workspaces.
- Chat-supervisor pattern (fast voice + smarter text tools).

---

## 6. Architecture (locked direction)

```
Browser mic
  → WebRTC (prefer LiveKit or OpenAI Realtime transport)
  → Speech-to-speech / Realtime model
       ↔ tool: search_kb(query) → vector store → chunks + source ids
  → Spoken reply (grounded or refuse)
UI: citations from tool I/O (+ optional transcript)
Separate: FastAPI (or Next) ingest + KB admin APIs
```

| Layer | Choice | Notes |
|-------|--------|-------|
| Voice runtime | [CUSTOMIZE: LiveKit Agents + Realtime plugin **or** OpenAI Realtime Agents **or** other] | Pure S2S primary |
| KB / RAG | FastAPI + embeddings + [CUSTOMIZE: Chroma / pgvector / Qdrant / LanceDB] | Tool-called from voice loop |
| Client | Thin web app | Mic + playback + upload + cites |
| Deploy | [CUSTOMIZE: Railway / Fly / Vercel+worker / Docker VPS] | One live URL |

**Reference repos to steal patterns from (not fork wholesale)**
1. https://github.com/openai/openai-realtime-agents
2. https://github.com/livekit/agents
3. https://github.com/pipecat-ai/pipecat (only if we need pipeline pieces)
4. https://github.com/Mintplex-Labs/anything-llm (cite UX / workspace model)
5. https://github.com/SalesforceAIResearch/VoiceAgentRAG (latency later)

---

## 7. Grounding policy (product law)

1. Knowledge questions → must call retrieval (or use fresh retrieval context).
2. If no adequate evidence → refuse; do **not** answer from world knowledge.
3. Chitchat (“hi”, “thanks”) → no KB required.
4. Citations in UI must match tool-returned chunks (no post-rationalized fake cites).
5. [CUSTOMIZE: threshold score / top-k / max context tokens]

**Refuse script (spoken):**  
[CUSTOMIZE default:] “I don’t have that in your knowledge base yet.”

---

## 8. Success metrics

| Metric | Target |
|--------|--------|
| Deployed live URL | Yes |
| End-to-end voice ask over own KB | Works for primary user |
| Refuse rate on out-of-KB questions | [CUSTOMIZE: e.g. correctly refuses ≥ 80% on a 20-Q test set] |
| Hallucinated KB answers on held-out “not in docs” | [CUSTOMIZE: e.g. ≤ 10%] |
| Real users | [CUSTOMIZE: N people used it ≥ M times] |
| Demo-ready for resume / interviews | Yes |

---

## 9. Constraints

- Budget: [CUSTOMIZE: max $/month on model + STT/TTS/hosting]
- Privacy: [CUSTOMIZE: docs stay private / which cloud OK]
- Timebox: [CUSTOMIZE: e.g. Phase 1 spine in 7–14 days]
- Stack comfort: Python/FastAPI preferred; JS/TS OK for client.
- Resume story: must be honest — “Phase 1 in build / live S2S over KB” only when true.

---

## 10. Milestones

1. **M0 — PRP locked** (this doc returned + customized).
2. **M1 — Text tool path:** ingest + `search_kb` + cite/refuse over HTTP (proves grounding).
3. **M2 — S2S loop:** realtime voice in browser, no KB yet (proves voice feel).
4. **M3 — Wire tool:** S2S model calls `search_kb`; speak grounded/refuse.
5. **M4 — Deploy + 3–5 users** + citation UI + basic logs.
6. **M5 — Harden:** test set, thresholds, latency fillers / prefetch if needed.

[CUSTOMIZE order if you want M2 before M1]

---

## 11. Open decisions (fill these)

Copy and answer:

```
Voice provider:     [ ] OpenAI Realtime  [ ] Gemini Live  [ ] other: ____
Transport:          [ ] LiveKit  [ ] OpenAI native WS  [ ] other: ____
Turn style:         [ ] push-to-talk  [ ] always-on + barge-in
KB start format:    [ ] markdown  [ ] PDF  [ ] both
Vector store:       [ ] Chroma  [ ] pgvector  [ ] Qdrant  [ ] LanceDB  [ ] other
Auth:               [ ] none (private URL)  [ ] password  [ ] per-user
Cites in speech:    [ ] UI only  [ ] light spoken  [ ] full spoken
Transcript UI:      [ ] yes  [ ] no
First milestone:    [ ] M1 text grounding  [ ] M2 pure voice feel
Deadline:           ____
Budget/mo:          ____
Must-demo for:      [ ] applications  [ ] interview  [ ] personal use only
Anything sacred:    ____
Anything banned:    ____
```

---

## 12. North star (post–Phase 1, do not build yet)

Multi-user company brain-dumps → shared company voice over the **same** S2S + KB spine. Notion later. Lenses later. Fine-tune only if RAG plateaus.

---

## 13. Return format

Paste back either:
- this whole file with your edits, **or**
- just **§11 Open decisions** + any changed sections.

Spider will treat your returned PRP as source of truth and scaffold from it.
