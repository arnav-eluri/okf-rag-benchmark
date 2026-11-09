---
verified: true
stale_after: 2030-01-01
keywords: [precision, recall, "f1 score", f1, "token overlap", "squad metric", "evaluation metric", accuracy, "true positive", "false positive", "false negative", "confusion matrix"]
---

# ML Evaluation Glossary

## Precision
Precision measures how many of the predicted tokens (or items) are actually correct.

**Formula:** Precision = True Positives / (True Positives + False Positives)

In token-overlap evaluation (SQuAD-style): Precision = common_tokens / len(predicted_tokens)

A high precision means the model rarely includes incorrect information — but it may still miss relevant content.

## Recall
Recall measures how many of the correct tokens (or items) the model actually retrieved.

**Formula:** Recall = True Positives / (True Positives + False Negatives)

In token-overlap evaluation: Recall = common_tokens / len(gold_tokens)

A high recall means the model covers most of the gold answer — but it may also include noise.

## F1 Score
F1 is the harmonic mean of Precision and Recall. It balances both concerns into a single number.

**Formula:** F1 = 2 × (Precision × Recall) / (Precision + Recall)

Range: 0 (worst) to 1 (perfect match).

F1 is preferred over accuracy when classes are imbalanced or when both false positives and false negatives matter. The SQuAD benchmark uses token-overlap F1 as its primary metric for open-domain QA.

## Why harmonic mean?
The harmonic mean penalises extreme imbalances. A model with Precision=1.0 and Recall=0.01 gets F1=0.02 — not 0.5 — correctly flagging that it is nearly useless despite perfect precision.

## Confusion Matrix
|               | Predicted Positive | Predicted Negative |
|---------------|--------------------|--------------------|
| **Actual Positive** | True Positive (TP)  | False Negative (FN) |
| **Actual Negative** | False Positive (FP) | True Negative (TN) |

- Precision = TP / (TP + FP)
- Recall    = TP / (TP + FN)
- F1        = 2·TP / (2·TP + FP + FN)
