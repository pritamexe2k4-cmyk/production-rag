# Production RAG — Grounded Ops Q&A

Answer only from files in `corpus/`. If the files do not say it, refuse.
Same pipeline for company SOPs or personal notes (journals, quotes, logs).

**Repo:** https://github.com/pritamexe2k4-cmyk/production-rag  
**Status:** design locked; code not shipped yet.

## Problem
People ask questions against a pile of markdown. The system must cite a file or say `not_in_corpus`. No invented facts.

## Pipeline

```
.md / .pdf
  → ingest.py          load → split → embed
  → Chroma             persist ./chroma

POST /query {question}
  → LangGraph          retrieve → generate | refuse
  → JSON               {answer, sources[], refused}
  → SQLite             queries.db (question, refused, latency_ms)
```

## Slots (fill these; do not skip)
| Slot | Choice |
|---|---|
| Source | `corpus/ops/` (public samples) and `corpus/personal/` (local, gitignored) |
| Split | ~1000 tokens, ~200 overlap |
| Embed + LLM | one pair; set in `.env` |
| Store | Chroma persist |
| Graph | retrieve → (hits?) generate : refuse |
| API | FastAPI `POST /ingest`, `POST /query` |
| Eval | `eval.json` — in-corpus + must-refuse |
| Trace | LangSmith optional |

## Personal use
Notion stays the editor. From 31 Aug 2026, new durable notes also exist as `.md` so this service can ingest them.

- Drop personal files in `corpus/personal/` (not committed).
- Photos stay in Drive; only the **caption / note** is markdown.
- Daily journal, SQL notes, quotes, gym one-liners → `.md` with a date in the filename.

`corpus/personal/` is gitignored. Do not push journals to GitHub.

## Layout
```
app.py          FastAPI
graph.py        retrieve / generate / refuse
ingest.py       folder → Chroma
eval.py         run eval.json
eval.json       20 questions
corpus/ops/     sample SOPs (safe to public)
corpus/personal/  your notes (local only)
chroma/         gitignored
queries.db      gitignored
```

## Run (once code exists)
```bash
python ingest.py --path corpus/ops
uvicorn app:app --reload
# POST /query {"question": "What is the on-call rule?"}
python eval.py
```

## Showcase bar
A stranger can clone, ingest `corpus/ops`, hit `/query`, and see a refusal on a question the files do not answer.
