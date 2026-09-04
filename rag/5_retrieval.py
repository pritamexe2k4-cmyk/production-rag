# ============================================================
#  COMPONENT 5 : RETRIEVAL
# ============================================================
#
#  WHAT IS IT?
#  -----------
#  Retrieval is the SEARCH step. Given a user's question,
#  it fetches the most relevant chunks from the Vector Store.
#  This is the heart of RAG — bad retrieval = bad answers, always.
#
#  WHAT DOES IT DO?
#  ----------------
#  - Takes the user's question (raw or transformed)
#  - Embeds the question into a vector
#  - Searches the Vector Store for the closest chunk vectors
#  - Returns the top-k chunks as context for the LLM
#
#  RETRIEVAL STRATEGIES:
#  ---------------------
#  NAIVE:
#    - Simple similarity search (top-k by cosine similarity)
#    - Fast, easy, but can miss relevant results if phrasing differs
#
#  ADVANCED:
#    - MMR (Maximal Marginal Relevance)
#        → balances relevance AND diversity of retrieved chunks
#        → avoids returning 3 identical chunks
#
#    - Hybrid Search (vector + BM25 keyword)
#        → vector search finds semantically similar chunks
#        → BM25 finds exact keyword matches
#        → both scores combined (e.g. via Reciprocal Rank Fusion)
#        → best of both worlds
#
#    - Re-Ranking (Cross-Encoder)
#        → first retrieve top-20 candidates cheaply
#        → then a Cross-Encoder model re-scores all 20 more accurately
#        → return only the top-3 after re-ranking
#        → much more accurate than vector search alone
#
#    - Multi-vector Retrieval
#        → store summaries of chunks as the searchable vector
#        → but return the full parent chunk to the LLM
#
#  KEY PARAMETER:
#  --------------
#  - k : how many chunks to retrieve
#    Too few → LLM might miss the answer
#    Too many → LLM gets confused by irrelevant context (lost-in-middle)
#    Typical value: 3 to 5
#
#  OUTPUT of this step:
#  --------------------
#  A list of relevant Document chunks  →  sent to 7_prompt.py
# ============================================================
