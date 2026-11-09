# Adding Content

## Adding a RAG Document

Drop any `.md` file into `documents/`. RAG indexes every `.md` file under that directory recursively at startup (`rag.build_index`). No other changes needed.

The file is split into 400-token chunks with 50-token overlap. Keep source documents factual; the LLM generates answers from retrieved chunks verbatim.

## Adding an OKF Bundle File

1. Create `okf_bundle/<slug>.md` where `<slug>` uses underscores for spaces (e.g. `flydubai_flight.md`).
2. Write frontmatter:

   ```yaml
   ---
   verified: true
   stale_after: 2027-12-31
   keywords: [term1, term2, ...]
   ---
   ```

3. Write the knowledge body after the closing `---`.
4. Add a test question + gold answer to `TEST_QUESTIONS` in `main.py`.

**Keyword guidelines**: list terms a user would naturally include in a question about this topic. The concept name (filename slug) is already matched automatically, so do not repeat it in `keywords`. Focus on synonyms, specific entities, and sub-topics.

## Adding a Test Question

```python
TEST_QUESTIONS = [
    ...
    {
        "question": "Your question here?",
        "gold_answer": "The precise expected answer, sourced from the bundle or document."
    },
]
```

Gold answers should be grounded in what the OKF bundle or source document actually says — not paraphrased from memory. This keeps the evaluation honest.
