from groq import Groq
import re, config

client = Groq(api_key=config.GROQ_API_KEY)

def _clean(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def get_answer(question, context, system="You are a helpful assistant."):
    if not context:
        return "No context available."
    resp = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]
    )
    return _clean(resp.choices[0].message.content)

def score_answer(question, answer, gold_answer):
    """Ask GPT to judge accuracy 0-10."""
    prompt = f"""
Question: {question}
Expected answer: {gold_answer}
Given answer: {answer}

Rate the accuracy of the given answer from 0 to 10.
Reply with just a number.
"""
    resp = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{"role": "user", "content": prompt}]
    )
    try:
        return int(_clean(resp.choices[0].message.content))
    except:
        return 0