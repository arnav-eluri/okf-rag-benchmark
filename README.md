# OKF — Ontology Knowledge Framework

A benchmarking framework that compares three question-answering retrieval strategies — **RAG**, **OKF**, and **Hybrid** — against real newspaper content. Each strategy retrieves context independently; a shared LLM layer generates and scores answers against gold standards.

**Author:** Arnav Eluri  
**License:** MIT

---

## Architecture

```
                        User Question
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
      RAG Pipeline       OKF Pipeline       Hybrid Router
      documents/         okf_bundle/        (OKF → RAG fallback)
      Chroma + embeddings  YAML frontmatter  combined context
          │                   │                   │
          └───────────────────┴───────────────────┘
                              │
                     LLM Layer (Groq)
                     Answer generation + scoring
                              │
                     Results table + JSON
```

| Strategy | How it retrieves |
|----------|-----------------|
| **RAG** | Embeds source documents into Chroma; returns top-5 chunks by cosine similarity |
| **OKF** | Keyword-matches curated Markdown files via YAML frontmatter; returns the most relevant 300-char chunk via cosine similarity |
| **Hybrid** | Queries OKF and RAG independently; when OKF matches, concatenates both contexts (RAG first, OKF last) for the LLM |

---

## Benchmark Results

Evaluated on 10 questions from the **Times of India, Delhi edition — November 7, 2026**.  
Scores are averaged across all questions where the retriever returned context.

| System | LLM Score | Precision | F1 |
|--------|----------:|----------:|---:|
| **Hybrid** | **8.7 / 10** | **0.718** | **0.643** |
| RAG    | 8.0 / 10 | 0.712 | 0.581 |
| OKF    | 4.5 / 10 | 0.545 | 0.563 |

- **LLM Score** — Groq-judged factual accuracy, 0–10, with partial-credit rubric  
- **Precision / F1** — SQuAD-style token-overlap against gold answers

Hybrid outperforms RAG standalone by combining curated OKF facts with semantic RAG context. OKF standalone scores lower because it is intentionally narrow — it only fires on explicitly curated topics.

---

## Project Structure

```
okf/
├── main.py           # Entry point — runs eval, prints table, saves JSON
├── evaluator.py      # Answer generation + LLM scoring (Groq)
├── rag.py            # Chroma vector index; ingests .md, .docx, .pdf
├── okf.py            # Keyword + frontmatter matcher with mini-RAG reranking
├── hybrid.py         # Combines OKF and RAG contexts; falls back to RAG
├── config.py         # Env var loading
├── documents/        # Source files indexed by RAG
│   └── Times of India_TOIDelhiBS-Delhi_20261107.pdf
├── okf_bundle/       # Curated knowledge files
│   ├── grap_delhi_pollution.md
│   ├── gaffar_market_fire.md
│   ├── ed_foreign_funds.md
│   ├── chawri_bazar_collapse.md
│   └── ml_glossary.md
└── results_YYYY-MM-DD.json
```

---

## Setup

**Prerequisites:** Python 3.8+, a [Groq API key](https://console.groq.com)

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here

# Optional — enables Google text-embedding-004 (better retrieval quality)
# Get a key at https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=AIza...
```

Without `GOOGLE_API_KEY`, the system falls back to `all-MiniLM-L6-v2` via HuggingFace.

---

## Running

```bash
python main.py
```

Builds the RAG index on every run (wipes `.chroma/` first to avoid stale chunks), evaluates all 10 questions in parallel, prints a Rich table, and saves `results_YYYY-MM-DD.json`.

---

## Extending

### Adding documents to RAG

Drop any `.md`, `.docx`, or `.pdf` into `documents/`. The index rebuilds automatically on the next run.

### Adding knowledge to OKF

Create a Markdown file in `okf_bundle/` with YAML frontmatter:

```markdown
---
verified: true
stale_after: 2027-06-01
keywords: [keyword1, keyword2, "multi word phrase"]
---

Your knowledge content here.
```

The OKF matcher fires when any `keyword` (or the filename slug) appears in the question. If the file body is long, it is split into 300-char chunks and the most relevant chunk is returned via embedding similarity. Content past `stale_after` is silently skipped.

### Adding test questions

Add entries to `TEST_QUESTIONS` in `main.py`:

```python
{
    "question": "Your question here?",
    "gold_answer": "Expected factual answer."
}
```

---

## Model

Answer generation and scoring both use `qwen/qwen3.8-27b` via Groq with the `/no_think` directive to suppress chain-of-thought output and stay within token budgets.

The scorer uses a partial-credit rubric: 10 for exact facts, 7–9 for correct facts with minor phrasing differences, 4–6 for partial answers, 0–3 for wrong or missing answers.

---

## License

MIT — see `LICENSE`.
