# System Architecture

## Overview

This project benchmarks three question-answering strategies against a fixed set of test questions drawn from real news articles. Each strategy retrieves a context passage and passes it to an LLM to generate an answer; a second LLM call then scores that answer against a gold standard on a 0–10 scale.

```
                    ┌─────────────────┐
                    │   main.py       │
                    │  (test runner)  │
                    └────────┬────────┘
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
      rag.query_rag    okf.query_okf    hybrid.query_hybrid
           │                 │                 │
           ▼                 ▼                 ▼
    Chroma vector      YAML-frontmatter    OKF first,
    store over         .md files in        RAG fallback
    documents/         okf_bundle/
           │                 │                 │
           └─────────────────┴─────────────────┘
                             │
                    evaluator.get_answer
                    (Groq llama-3.3-70b-versatile)
                             │
                    evaluator.score_answer
                    (Groq llama-3.3-70b-versatile)
```

## Strategy Details

### RAG (`rag.py`)

- Embeds every `.md` file under `documents/` using `all-MiniLM-L6-v2` (HuggingFace sentence-transformers).
- Splits documents into 400-token chunks with 50-token overlap via `RecursiveCharacterTextSplitter`.
- Stores vectors in a local Chroma database (`.chroma/`).
- At query time retrieves the top-3 most similar chunks by cosine similarity.
- **Source of truth**: raw source documents in `documents/`.

### OKF (`okf.py`)

- Reads every `.md` file in `okf_bundle/`, parsing YAML frontmatter (`---` delimiters).
- Skips a file if today's date exceeds `stale_after`.
- Matches a question by checking:
  1. Whether the filename (underscores → spaces) appears in the lowercased question.
  2. Whether any entry in the `keywords` list (frontmatter) appears in the lowercased question.
- Returns the markdown body and the `verified` flag.
- **Source of truth**: curated, human-verified bundle files in `okf_bundle/`.

### Hybrid (`hybrid.py`)

- Calls OKF first. If OKF returns a match, uses that context (no RAG call made).
- Falls back to RAG when OKF has no match.
- `main.py` detects reuse (same context, same answer) and skips redundant LLM calls.

## LLM Configuration

All LLM calls go through the Groq API (`evaluator.py`):

| Use | Model | Purpose |
|-----|-------|---------|
| Answer generation | `qwen/qwen3.8-27b` | Generates answer from retrieved context |
| Scoring | `qwen/qwen3.8-27b` | Rates answer 0–10 vs gold standard |

## Data Flow

```
1. rag.build_index(documents/)      ← indexes raw source docs into Chroma
2. For each TEST_QUESTION:
   a. rag.query_rag(q)              ← top-3 semantic chunks
   b. okf.query_okf(q, okf_bundle/) ← keyword/filename match
   c. hybrid.query_hybrid(q, ...)   ← OKF-first, RAG fallback
3. evaluator.get_answer(q, ctx)     ← LLM answer per strategy
4. evaluator.score_answer(q, ans, gold) ← LLM 0-10 score
5. Print Rich table + save JSON
```
