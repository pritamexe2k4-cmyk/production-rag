# ============================================================
#  COMPONENT 7 : PROMPT
# ============================================================
#
#  WHAT IS IT?
#  -----------
#  The Prompt is the instruction sent to the LLM.
#  In RAG, it combines TWO things:
#    1. The CONTEXT  → retrieved chunks from the Vector Store
#    2. The QUESTION → the user's original question
#  Together they form a "grounded" prompt that tells the LLM:
#  "Answer this question using ONLY this information."
#
#  WHAT DOES IT DO?
#  ----------------
#  - Takes the retrieved chunks (formatted as readable text)
#  - Takes the user's question
#  - Assembles them into a structured prompt template
#  - Sends the final prompt to the LLM for generation
#
#  WHY IS PROMPT DESIGN IMPORTANT?
#  --------------------------------
#  A poorly written prompt can cause the LLM to:
#    - Ignore the context and hallucinate anyway
#    - Be too verbose or too terse
#    - Mix up the question and the context
#  A good prompt clearly separates context from question and
#  explicitly instructs the LLM to stay grounded.
#
#  NAIVE LEVEL PROMPT STRUCTURE:
#  ------------------------------
#  """
#  Use the following context to answer the question.
#  If the context doesn't contain the answer, say "I don't know."
#
#  Context:
#  {context}
#
#  Question: {question}
#
#  Answer:
#  """
#
#  ADVANCED LEVEL TECHNIQUES:
#  --------------------------
#  - System prompt + Human prompt separation (ChatPromptTemplate)
#  - Few-shot examples in the prompt (show the LLM example Q&A pairs)
#  - Chain-of-thought instructions ("think step by step")
#  - Citation instructions ("cite the source of each fact")
#  - Compression: summarize/filter chunks before injecting into prompt
#    to avoid exceeding context window
#  - Context window management: if too many chunks, pick the best ones
#
#  CONTEXT FORMATTING:
#  -------------------
#  Retrieved chunks should be formatted clearly, e.g.:
#    --- Document 1 ---
#    <text of chunk 1>
#    --- Document 2 ---
#    <text of chunk 2>
#
#  OUTPUT of this step:
#  --------------------
#  A fully assembled prompt string  →  sent to 8_generation.py
# ============================================================
