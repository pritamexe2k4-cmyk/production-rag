# ============================================================
#  COMPONENT 6 : QUERY TRANSFORMATION
# ============================================================
#
#  WHAT IS IT?
#  -----------
#  Query Transformation improves retrieval by REWRITING or EXPANDING
#  the user's raw question before it hits the Vector Store.
#  Users often phrase questions poorly or vaguely — this step fixes that.
#
#  WHY IS IT NEEDED?
#  -----------------
#  The user types:  "what about the sun?"
#  This is vague. The embedding of this question may not closely match
#  chunks that say "The Sun's diameter is 1.39 million km."
#  A rewritten query like "What is the size and diameter of the Sun?"
#  will match much better.
#
#  THIS IS AN ADVANCED COMPONENT — not needed in Naive RAG.
#
#  TRANSFORMATION TECHNIQUES:
#  --------------------------
#
#  1. QUERY REWRITING
#     - Use an LLM to rephrase the question more clearly
#     - Removes ambiguity, fixes grammar, adds specificity
#     - Example: "tell me about python" → "What are the key features
#       and history of the Python programming language?"
#
#  2. MULTI-QUERY
#     - LLM generates 3-5 different versions of the same question
#     - Each version is used to retrieve chunks independently
#     - All retrieved chunks are merged and deduplicated
#     - Captures more relevant results from different angles
#
#  3. HyDE (Hypothetical Document Embeddings)
#     - LLM generates a HYPOTHETICAL answer to the question
#     - That hypothetical answer is embedded (not the question itself)
#     - The hypothesis vector often matches real document vectors better
#     - Very powerful for technical or factual queries
#
#  4. STEP-BACK PROMPTING
#     - LLM generates a more general / abstract version of the question
#     - Used to retrieve broader context first
#     - Then the specific question is answered using that broad context
#
#  5. QUERY DECOMPOSITION
#     - Complex multi-part question is broken into simpler sub-questions
#     - Each sub-question is answered separately
#     - Final answer synthesizes all sub-answers
#     - Used in Agentic RAG
#
#  NAIVE LEVEL:
#  ------------
#  Skip this step entirely. Raw user question goes directly to retrieval.
#
#  OUTPUT of this step:
#  --------------------
#  One or more improved queries  →  fed into 5_retrieval.py
# ============================================================
