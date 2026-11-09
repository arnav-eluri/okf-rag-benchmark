# Evaluation Methodology

## How Answers Are Scored

Each test question has a `gold_answer` — a short reference answer written by the author. After each strategy generates an answer from its retrieved context, `evaluator.score_answer` asks the LLM:

```
Question: <question>
Expected answer: <gold_answer>
Given answer: <generated_answer>

Rate the accuracy of the given answer from 0 to 10.
Reply with just a number.
```

The LLM returns an integer 0–10. The evaluator parses it; if parsing fails it returns 0.

## Test Questions

Defined in `main.py` as `TEST_QUESTIONS`. Each entry:

```python
{
    "question": "Who was stabbed on the flydubai flight from Dubai to Tel Aviv?",
    "gold_answer": "The co-pilot was stabbed by the captain in an apparent attempt to crash the aircraft."
}
```

The gold answers are grounded in the OKF bundle files and source documents in `documents/`.

## Parallel Execution

`main.py` uses `ThreadPoolExecutor` to run answer generation and scoring in parallel across the three strategies. If Hybrid reuses OKF's context (same content, same answer), the redundant LLM call is skipped.

## Output

A Rich table is printed to stdout:

| Column | Description |
|--------|-------------|
| Question | Truncated question text |
| RAG Score | 0–10, pure vector-search retrieval |
| OKF Score | 0–10, structured bundle lookup |
| Hybrid Score | 0–10, OKF-first with RAG fallback |
| Hybrid Used | Which backend Hybrid selected (`OKF` or `RAG`) |

Averages are printed below the table. All results are saved to `results_YYYY-MM-DD.json`.

## Interpreting Results

- **OKF score higher than RAG**: The curated bundle provided a more precise context than vector search over the raw article.
- **RAG score higher than OKF**: The question fell outside OKF's keyword coverage — a signal to add keywords or a new bundle file.
- **Hybrid ≈ OKF**: Most questions matched OKF (expected when bundle coverage is good).
- **Hybrid ≈ RAG**: OKF had low coverage; consider expanding `keywords` in bundle frontmatter.
