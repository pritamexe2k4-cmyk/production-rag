# ============================================================
#  COMPONENT 4 : VECTOR STORE
# ============================================================
#
#  WHAT IS IT?
#  -----------
#  A Vector Store is a specialized database that stores text chunks
#  alongside their embedding vectors and allows fast similarity search.
#  Think of it as a search engine — but instead of keyword matching,
#  it matches by MEANING.
#
#  WHAT DOES IT DO?
#  ----------------
#  - Receives (chunk text + vector) pairs from the Embedding step
#  - Stores them persistently or in-memory
#  - At query time: takes the query vector and finds the most
#    similar chunk vectors using distance metrics (cosine, dot product)
#  - Returns the top-k most relevant chunks
#
#  HOW SIMILARITY WORKS:
#  ---------------------
#  Each chunk is a point in high-dimensional space (e.g. 768 dimensions).
#  The query is also a point in that same space.
#  Vector Store finds the closest points (chunks) to the query point.
#  "Closeness" is measured by cosine similarity or L2 distance.
#
#  VECTOR STORE OPTIONS:
#  ---------------------
#  IN-MEMORY (no setup, good for demos):
#    - FAISS           → Facebook's fast similarity search library
#    - Chroma          → lightweight, easy to use, can persist to disk
#
#  SELF-HOSTED (for production):
#    - Qdrant          → fast, feature-rich, runs as a Docker container
#    - Weaviate        → supports hybrid search out of the box
#    - Milvus          → high scalability
#
#  CLOUD / MANAGED:
#    - Pinecone        → fully managed, very popular
#    - Weaviate Cloud  → managed Weaviate
#    - MongoDB Atlas   → vector search inside MongoDB
#
#  NAIVE LEVEL:
#  ------------
#  Use FAISS in-memory. No persistence — index is rebuilt every run.
#  Fast to set up, no external dependencies.
#
#  ADVANCED LEVEL:
#  ---------------
#  - Persist the index to disk so you don't re-embed on every run
#  - Add metadata filtering (e.g. only search docs from 2024)
#  - Use hybrid search: combine vector search + keyword (BM25) search
#  - Partition indexes by namespace / collection for multi-tenant use
#
#  OUTPUT of this step:
#  --------------------
#  A "retriever" object that can be queried  →  used in 5_retrieval.py
# ============================================================
