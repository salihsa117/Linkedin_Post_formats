"""Pick reel-worthy spans from a long transcript."""
from llm import ask_json

MIN_LEN, MAX_LEN = 25.0, 75.0


def _heuristic(segments, n):
    """No LLM: cut consecutive sentence-aligned windows of ~45s, spread evenly."""
    windows, start, end, text = [], None, None, []
    for s in segments:
        if start is None:
            start = s["start"]
        end = s["end"]
        text.append(s["text"])
        if end - start >= 45:
            windows.append({"start": start, "end": end, "title": text[0][:60], "text": " ".join(text)})
            start, text = None, []
    if not windows:
        return []
    step = max(1, len(windows) // n)
    return windows[::step][:n]


def select_clips(tr, n=5):
    segs = tr["segments"]
    if tr["duration"] <= 90:
        return [{"start": 0.0, "end": tr["duration"], "title": segs[0]["text"][:60] if segs else "clip",
                 "text": " ".join(s["text"] for s in segs)}]
    listing = "\n".join(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segs)
    res = ask_json(
        f"هذا تفريغ محاضرة. اختر حتى {n} مقاطع تصلح ريلز مستقلة، كل منها بين {MIN_LEN:.0f} و{MAX_LEN:.0f} ثانية، "
        "تبدأ بجملة قوية وتنتهي عند نهاية فكرة. استخدم حدود الجمل الموجودة فقط.\n"
        'الصيغة: [{"start":0.0,"end":0.0,"title":"..."}]\n\n' + listing[:60000])
    clips = []
    for c in res or []:
        try:
            s, e = float(c["start"]), float(c["end"])
        except (KeyError, TypeError, ValueError):
            continue
        if MIN_LEN <= e - s <= MAX_LEN + 15 and 0 <= s < e <= tr["duration"] + 1:
            text = " ".join(x["text"] for x in segs if x["start"] >= s - 0.3 and x["end"] <= e + 0.3)
            clips.append({"start": s, "end": e, "title": c.get("title", text[:60]), "text": text})
    return clips[:n] or _heuristic(segs, n)
