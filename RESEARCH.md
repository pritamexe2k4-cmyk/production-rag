# Grounded Ops Q&A — skills, papers, learn path

For anyone building this class of system: retrieve from files, cite, or refuse.

## Skills the project must prove

| Layer | You need |
|---|---|
| Language | Python, typing, errors |
| Serve | FastAPI, JSON in/out |
| Retrieve | chunking, embeddings, vector store (Chroma) |
| Control | LangGraph state: retrieve → generate \| refuse |
| Data | markdown corpus; optional SQLite query log |
| Proof | eval.json (in-corpus + must-refuse) |
| See | LangSmith or printed traces |
| Ship | Git, one run command, README diagram |

SQL is for logs and later filters. React is optional skin.

## Papers (read these, in this order)

1. Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, NeurIPS 2020. https://arxiv.org/abs/2005.11401 — why retrieve at all.
2. Karpukhin et al., *Dense Passage Retrieval for Open-Domain Question Answering* (DPR), 2020. https://arxiv.org/abs/2004.04906 — dense retrieval.
3. Asai et al., *Self-RAG: Learning to Retrieve, Generate, and Critique*, 2023. https://arxiv.org/abs/2310.11511 — retrieve only when needed; critique.
4. Yan et al., *Corrective Retrieval Augmented Generation* (CRAG), 2024. https://arxiv.org/abs/2401.15884 — what to do when retrieval is weak.
5. Gao et al., *Retrieval-Augmented Generation for Large Language Models: A Survey*, 2024. https://arxiv.org/abs/2312.10997 — map of patterns.
6. de Costa et al., *From Naive RAG to Deep Agentic Retrieval*, 2026. https://arxiv.org/abs/2607.24791 — naive → hybrid → agent in a real ops corpus.

## Similar systems (not to copy, to compare)

- LangChain docs RAG tutorial (load → split → retrieve → generate).
- LlamaIndex RAG stages: load, index, store, query, evaluate.
- Capstone / career RAG studios on GitHub: FastAPI + vector DB + refuse-or-cite.

## What to learn before writing `app.py`

1. Embeddings = nearest neighbour, not magic.
2. Chunk size changes what retrieve can see.
3. Always-retrieve vs retrieve-when-needed (LangGraph branch).
4. Faithfulness ≠ fluency. Eval on refuse questions.
5. Traces: one failed retrieve is worth more than a demo GIF.

## Research you actually do on *this* repo

- Write 4 short source files (`corpus/ops/`).
- Write 20 questions in `eval.json` (12 answerable, 8 refuse).
- After first `/query`, log miss rate. Change chunk size once. Measure again.
- Do not add agents until refuse questions pass.

## Personal corpus

Gym, SQL, daily journals → `corpus/personal/YYYY-MM-DD-topic.md` (gitignored).
Empty templates live in `corpus/templates/`.
