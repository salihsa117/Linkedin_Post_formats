"""Per-platform copy: captions, marketing line, hashtags, comment ideas."""
import json

from llm import ask_json

PLATFORMS = ["instagram", "tiktok", "youtube", "facebook", "linkedin", "x"]


def generate(clip, brand):
    res = ask_json(
        f"أنت كاتب محتوى لحساب «{brand['name']}». الأسلوب: {brand['voice']}\n"
        "اكتب محتوى لريل نصه التالي. لا تختلق أرقاماً أو وعوداً غير موجودة في النص.\n"
        f"النص:\n{clip['text'][:6000]}\n\n"
        "أعد JSON بالشكل: {\"hook\":\"...\",\"marketing_message\":\"...\","
        "\"hashtags\":[\"..\"],\"comments\":[\"3 تعليقات مقترحة للتفاعل\"],"
        "\"captions\":{\"instagram\":\"..\",\"tiktok\":\"..\",\"youtube\":\"عنوان قصير | وصف\","
        "\"facebook\":\"..\",\"linkedin\":\"..\",\"x\":\"أقل من 270 حرفاً\"}}")
    if res and isinstance(res.get("captions"), dict):
        return res, "ready"
    plain = clip["text"][:200].strip()
    base = f"{clip['title']}\n\n{plain}\n\n{brand['cta']}"
    return {
        "hook": clip["title"], "marketing_message": brand["cta"],
        "hashtags": brand["hashtags_base"], "comments": [],
        "captions": {p: base for p in PLATFORMS},
    }, "needs_review"


def hashtag_str(res, brand):
    tags = list(dict.fromkeys(res.get("hashtags", []) + brand["hashtags_base"]))
    return " ".join("#" + t.lstrip("#").replace(" ", "_") for t in tags)


def dump(res):
    return json.dumps(res, ensure_ascii=False)
