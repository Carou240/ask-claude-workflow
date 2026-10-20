import json
import os
import sys

import httpx

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


def main() -> None:
    with open("question.json", encoding="utf-8") as f:
        q = json.load(f)

    question = q.get("question", "").strip()
    model = q.get("model", "claude-sonnet-4-5")
    max_tokens = int(q.get("max_tokens", 2048))

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        write_answer(question, model, "ERREUR: ANTHROPIC_API_KEY n'est pas configuree dans les secrets du depot (Settings > Secrets and variables > Actions).")
        return

    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": question}],
    }

    try:
        r = httpx.post(ANTHROPIC_API_URL, json=payload, headers=headers, timeout=90.0)
        r.raise_for_status()
        data = r.json()
        answer = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        used_model = data.get("model", model)
        meta = f"*{used_model} - {usage.get('input_tokens', '?')} tokens en entree, {usage.get('output_tokens', '?')} en sortie*"
        write_answer(question, used_model, answer, meta)
    except Exception as e:
        detail = str(e)
        try:
            detail = r.text[:800]
        except Exception:
            pass
        write_answer(question, model, f"ERREUR API Anthropic: {detail}")


def write_answer(question: str, model: str, answer: str, meta: str = "") -> None:
    with open("answer.md", "w", encoding="utf-8") as f:
        f.write("# Reponse de Claude\n\n")
        f.write(f"**Question :** {question}\n\n")
        if meta:
            f.write(f"{meta}\n\n---\n\n")
        f.write(answer)


if __name__ == "__main__":
    main()
