# ============================================================
#  COMPONENT 8 : GENERATION
# ============================================================
#
#  WHAT IS IT?
#  -----------
#  Generation is the final step where the LLM reads the prompt
#  (context + question) and produces the final answer.
#  This is the "G" in RAG — Retrieval-Augmented GENERATION.
#
#  WHAT DOES IT DO?
#  ----------------
#  - Receives the fully assembled prompt from the Prompt step
#  - Passes it to the LLM (local or cloud)
#  - LLM generates a response grounded in the provided context
#  - The response is parsed and returned to the user
#
#  LLM OPTIONS:
#  ------------
#  LOCAL (via Ollama — free, private, no internet needed):
#    - qwen3:4b        → fast, good for demos (used in this project)
#    - llama3.2        → very capable open-source model
#    - mistral         → strong reasoning
#    - gemma3          → Google's open model
#
#  CLOUD (API-based):
#    - ChatOpenAI      → GPT-4o, GPT-4-turbo
#    - ChatGoogleGenerativeAI → Gemini 1.5 Pro / Flash
#    - ChatAnthropic   → Claude 3.5 Sonnet
#    - ChatCohere      → Command R+
#
#  NAIVE LEVEL:
#  ------------
#  Single LLM call. Feed the prompt, get the answer. Done.
#  No validation, no retry, no citation checking.
#
#  ADVANCED LEVEL:
#  ---------------
#  - Streaming output: stream tokens as they are generated
#    (better UX for chat interfaces)
#
#  - Faithfulness checking: after generation, verify that
#    the answer is actually supported by the retrieved context
#    (using another LLM call or a scoring model like RAGAS)
#
#  - Self-correction / reflection: if the answer seems uncertain
#    or contradicts context, the LLM re-generates with a refined prompt
#
#  - Citation generation: LLM is instructed to cite which document
#    each fact came from (e.g. [Source: doc_3, page 12])
#
#  - Answer compression: if answer is too long, summarize it
#
#  OUTPUT PARSING:
#  ---------------
#  LangChain's StrOutputParser → extracts plain text from LLM response
#  For structured output (JSON) → use JsonOutputParser or Pydantic models
#
#  OUTPUT of this step:
#  --------------------
#  A final text answer string  →  returned to the user / pipeline
# ============================================================
