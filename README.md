# Production RAG

API-first RAG service: chunk → retrieve → generate with citations.
LangGraph routes search vs answer. FastAPI so a product can mount it on internal docs.

**Status:** repo created; implementation in progress.

## Stack
Python · FastAPI · LangGraph · vector DB · LangSmith

## Intended surface
`POST /query` — question in, cited answer out.
