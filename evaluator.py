from groq import Groq
import re, config

client = Groq(api_key=config.GROQ_API_KEY)

MODEL = "qwen/qwen3.8-27b"
# /no_think suppresses the <think>...</think> reasoning block,
# keeping output within the OTPM budget and making responses direct.
_NO_THINK = "/no_think"

def get_answer(question, context, system="You are a helpful assistant."):
    if not context:
        return "No context available."
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": f"{system} {_NO_THINK}"},
            {"role": "user",   "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        max_tokens=200,
    )
    return resp.choices[0].message.content.strip()

def score_answer(question, answer, gold_answer):
    """Ask LLM to judge accuracy 0-10."""
    prompt = (
        f"Question: {question}\n"
        f"Expected answer: {gold_answer}\n"
        f"Given answer: {answer}\n\n"
        "Rate the accuracy of the given answer from 0 to 10. Reply with just a number."
    )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": f"You are an evaluator. Output only a single integer 0-10. {_NO_THINK}"},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=10,
    )
    raw = resp.choices[0].message.content
    match = re.search(r'\b(\d+)\b', raw)
    return min(int(match.group(1)), 10) if match else 0
