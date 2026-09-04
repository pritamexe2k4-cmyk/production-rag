# ============================================================
#  COMPONENT 3 : EMBEDDING
# ============================================================
#
#  WHAT IS IT?
#  -----------
#  Embedding converts text (chunks) into numerical vectors.
#  These vectors capture the MEANING of the text mathematically,
#  so that similar texts end up close together in vector space.
#
#  WHAT DOES IT DO?
#  ----------------
#  - Takes each text chunk from Chunking
#  - Passes it through an Embedding Model
#  - Gets back a list of numbers (the vector / embedding)
#  - These vectors are stored in the Vector Store
#
#  HOW IT WORKS (INTUITION):
#  -------------------------
#  "The cat sat on the mat"   →  [0.12, -0.45, 0.87, ...]
#  "A feline rested on a rug" →  [0.11, -0.43, 0.85, ...]
#  Both are different sentences but have SIMILAR vectors
#  because they mean roughly the same thing.
#
#  EMBEDDING MODEL OPTIONS:
#  ------------------------
#  LOCAL (via Ollama — no API key, free):
#    - nomic-embed-text   → fast, good quality, popular choice
#    - mxbai-embed-large  → higher quality, slightly slower
#    - all-minilm         → very lightweight
#
#  CLOUD (API-based):
#    - OpenAI text-embedding-3-small / large
#    - Google text-embedding-004
#    - Cohere embed-v3
#
#  NAIVE LEVEL:
#  ------------
#  Use a single embedding model for ALL documents and queries.
#  Same model embeds both chunks AND the user question.
#
#  ADVANCED LEVEL:
#  ---------------
#  - Fine-tune the embedding model on your domain data
#  - Use different models for documents vs queries (asymmetric embedding)
#  - Late chunking: embed the full document first, then chunk vectors
#
#  IMPORTANT RULE:
#  ---------------
#  The SAME embedding model must be used at BOTH indexing time
#  (when storing chunks) AND query time (when embedding the question).
#  Mixing models will produce garbage results.
#
#  OUTPUT of this step:
#  --------------------
#  Dense vectors for each chunk  →  stored in 4_vectorstore.py
# ============================================================
