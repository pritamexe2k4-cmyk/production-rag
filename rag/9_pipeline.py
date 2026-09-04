# ============================================================
#  COMPONENT 9 : PIPELINE (The Full RAG Chain)
# ============================================================
#
#  WHAT IS IT?
#  -----------
#  The Pipeline wires ALL components together into one executable chain.
#  It is the entry point — you call the pipeline with a question
#  and it handles everything internally, end to end.
#
#  WHAT DOES IT DO?
#  ----------------
#  Connects all components in sequence:
#
#  User Question
#       ↓
#  [6] Query Transformation  (optional, Advanced RAG)
#       ↓
#  [5] Retrieval             → searches Vector Store
#       ↓
#  [7] Prompt Assembly       → context + question combined
#       ↓
#  [8] Generation            → LLM produces the answer
#       ↓
#  Final Answer → returned to user
#
#  HOW IT'S BUILT IN LANGCHAIN:
#  -----------------------------
#  LangChain uses LCEL (LangChain Expression Language) to compose
#  chains using the pipe operator  |
#
#  NAIVE PIPELINE looks like:
#  --------------------------
#  chain = (
#    {"context": retriever | format_docs, "question": passthrough}
#    | prompt_template
#    | llm
#    | output_parser
#  )
#  answer = chain.invoke("your question here")
#
#  ADVANCED PIPELINE adds:
#  -----------------------
#  - Query rewriting before retrieval
#  - Re-ranking after retrieval
#  - Multiple parallel retrievals (multi-query)
#  - Conditional logic (if no good context found → fall back)
#  - Memory / chat history for multi-turn conversations
#
#  AGENTIC PIPELINE adds:
#  ----------------------
#  - LLM decides WHEN to retrieve (not always)
#  - LLM decides WHAT query to retrieve with
#  - LLM loops until it has enough information
#  - LLM can call external tools (web search, calculator, APIs)
#  - Examples: CRAG, Self-RAG, Graph-RAG, LangGraph agents
#
#  THIS FILE'S ROLE:
#  -----------------
#  Imports from all other component files and assembles them.
#  Is the ONLY file you run to use the RAG system.
#  Acts like the "main.py" of the RAG project.
#
#  USAGE (once code is added):
#  ---------------------------
#  python 9_pipeline.py
# ============================================================
