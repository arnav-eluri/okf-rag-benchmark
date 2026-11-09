from groq import Groq
import re, time, string, config

client = Groq(api_key=config.GROQ_API_KEY)

MODEL = "qwen/qwen3.8-27b"
# /no_think suppresses the <think>...</think> reasoning block,
# keeping output within the OTPM budget and making responses direct.
_NO_THINK = "/no_think"

def _call(messages, max_tokens):
    # ponytail: simple retry for OTPM rate limits; upgrade to tenacity if limits tighten further
    for attempt in range(5):
        try:
            return client.chat.completions.create(
                model=MODEL, messages=messages, max_tokens=max_tokens
            )
        except Exception as e:
            if "rate_limit" not in str(e) and "429" not in str(e):
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("Groq rate limit: exhausted retries")

_ANSWER_SYSTEM = (
    "You are a factual QA assistant. "
    "Answer the question in one or two concise sentences using only the provided context. "
    "Quote numbers and names exactly as they appear in the context. "
    "Do not add commentary or hedging."
)

def get_answer(question, context, system=None):
    if not context:
        return "No context available."
    resp = _call([
        {"role": "system", "content": f"{system or _ANSWER_SYSTEM} {_NO_THINK}"},
        {"role": "user",   "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ], max_tokens=200)
    return resp.choices[0].message.content.strip()

def _tokenize(text):
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    return text.split()

def token_metrics(answer, gold_answer):
    """SQuAD-style token-overlap precision, recall, and F1 (0–1)."""
    pred = _tokenize(answer)
    gold = _tokenize(gold_answer)
    if not pred or not gold:
        return 0.0, 0.0, 0.0
    pred_counts = {}
    for t in pred:
        pred_counts[t] = pred_counts.get(t, 0) + 1
    gold_counts = {}
    for t in gold:
        gold_counts[t] = gold_counts.get(t, 0) + 1
    common = sum(min(pred_counts.get(t, 0), gold_counts[t]) for t in gold_counts)
    if common == 0:
        return 0.0, 0.0, 0.0
    precision = common / len(pred)
    recall    = common / len(gold)
    f1        = 2 * precision * recall / (precision + recall)
    return round(precision, 3), round(recall, 3), round(f1, 3)

def score_answer(question, answer, gold_answer):
    prompt = (
        f"Question: {question}\n"
        f"Expected answer: {gold_answer}\n"
        f"Given answer: {answer}\n\n"
        "Score the given answer 0-10 for factual accuracy.\n"
        "10 = all key facts correct (names, numbers, dates match).\n"
        "7-9 = correct fact, minor phrasing difference.\n"
        "4-6 = partially correct or missing one key detail.\n"
        "1-3 = mostly wrong but contains a relevant fragment.\n"
        "0 = completely wrong or no answer.\n"
        "Reply with just a single integer."
    )
    resp = _call([
        {"role": "system", "content": f"You are an evaluator. Output only a single integer 0-10. {_NO_THINK}"},
        {"role": "user",   "content": prompt},
    ], max_tokens=10)
    raw = resp.choices[0].message.content
    match = re.search(r'\b(\d+)\b', raw)
    return min(int(match.group(1)), 10) if match else 0
