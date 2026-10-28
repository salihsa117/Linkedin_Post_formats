"""Thin Claude wrapper. Returns None when no ANTHROPIC_API_KEY so callers can fall back."""
import json
import os
import re


def ask_json(prompt, max_tokens=3000):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    import anthropic

    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5"),
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt + "\n\nأجب بـ JSON صالح فقط بلا أي نص آخر."}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text")
    m = re.search(r"[\[{].*[\]}]", text, re.S)
    return json.loads(m.group(0)) if m else None
