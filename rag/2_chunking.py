# ============================================================
#  COMPONENT 2 : CHUNKING
# ============================================================
#
#  WHAT IS IT?
#  -----------
#  Chunking splits large documents into smaller, manageable pieces.
#  This is critical because:
#    1. LLMs have a context window limit
#    2. Embedding models work best on focused, short text
#    3. Smaller chunks = more precise retrieval
#
#  WHAT DOES IT DO?
#  ----------------
#  - Takes the list of Documents from Ingestion
#  - Splits each Document into smaller "chunks"
#  - Each chunk is still a Document object (preserves metadata)
#  - Outputs a larger list of smaller Documents
#
#  CHUNKING STRATEGIES:
#  --------------------
#  NAIVE:
#    - Fixed-size character splitting
#    - e.g. every 500 characters, with 50 character overlap
#    - Simple but can split sentences mid-way
#
#  ADVANCED:
#    - RecursiveCharacterTextSplitter  → tries to split on paragraphs,
#      then sentences, then words (smarter than fixed-size)
#    - Semantic Chunking               → uses embeddings to split at
#      natural topic boundaries (most accurate, slowest)
#    - Parent-Child Chunking           → stores large "parent" chunks
#      for context but retrieves small "child" chunks for precision
#    - Markdown / Code aware splitters → split on headers or functions
#
#  KEY PARAMETERS:
#  ---------------
#  - chunk_size    : max characters (or tokens) per chunk
#  - chunk_overlap : how many characters overlap between adjacent chunks
#                    (prevents losing context at chunk boundaries)
#
#  WHY OVERLAP?
#  ------------
#  If a sentence is split between chunk 1 and chunk 2,
#  overlap ensures that information isn't completely lost —
#  both chunks will contain that boundary text.
#
#  OUTPUT of this step:
#  --------------------
#  A list of smaller Document chunks  →  sent to 3_embedding.py
# ============================================================
