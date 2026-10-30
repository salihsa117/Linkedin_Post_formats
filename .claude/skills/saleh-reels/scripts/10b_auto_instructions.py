# -*- coding: utf-8 -*-
"""يلقط تعليمات المونتاج تلقائياً: المنطوقة داخل الفيديو + الملف النصي جنبه. بلا أي سؤال للمستخدم.

    python 10b_auto_instructions.py <work>            # يكشف ويكتب instr_found.json و review.txt
    python 10b_auto_instructions.py <work> --apply    # + يشيل جُمل التعليمات من الفيديو (عبر 10_script_edit drop)

المنطوق: كلمة الافتتاح «تعليمات للمونتاج» والإغلاق «انتهت التعليمات» (تتعدّل من <work>/instr.json
بالمفاتيح open و close). الملف النصي: <work>/instructions.txt (يُنسخ جنب الفيديو).
يقرأ caps.json (بعد 02_captions.py). كل جملة تتقاطع مع المقطع المنطوق تُعدّ جملة تعليمات.
تنفيذ المعنى (قص جزء، حذف إعادة…) يسوّيه Claude بعدها بـ10_script_edit.py drop/keep، ويسجّله في review.txt.
"""
import sys, os, json, re, subprocess

W = os.path.abspath(sys.argv[1])
APPLY = "--apply" in sys.argv
P = lambda n: os.path.join(W, n)

def norm(w):
    w = re.sub(r"[ً-ْـ]", "", w)
    w = re.sub(r"[^\w]", "", w)
    w = w.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
    if len(w) > 4 and w.startswith("ال"): w = w[2:]
    return w

cfg = {"open": "تعليمات للمونتاج", "close": "انتهت التعليمات"}
if os.path.exists(P("instr.json")):
    cfg.update(json.load(open(P("instr.json"), encoding="utf-8")))
OPEN = [norm(x) for x in cfg["open"].split()]
CLOSE = [norm(x) for x in cfg["close"].split()]

cards = json.load(open(P("caps.json"), encoding="utf-8"))["cards"]
flat = [(ci, w) for ci, c in enumerate(cards) for w in c["w"]]
toks = [norm(w["t"]) for _, w in flat]

def find(seq, start=0):
    for i in range(start, len(toks) - len(seq) + 1):
        if toks[i:i + len(seq)] == seq: return i
    return -1

spoken, notes, drop = [], [], set()
i = find(OPEN)
while i >= 0:
    j = find(CLOSE, i + len(OPEN))
    end_i = (j + len(CLOSE) - 1) if j >= 0 else None
    if end_i is None:
        # بلا إغلاق: خذ لين نهاية الجملة اللي فيها الافتتاح
        end_i = max(k for k, (ci, _) in enumerate(flat) if ci == flat[i][0])
        notes.append(f"⚠️ فتح التعليمات عند {flat[i][1]['s']:.1f}ث بلا كلمة إغلاق — اعتبرت نهاية الجملة. راجعها.")
    cs, ce = flat[i][0], flat[end_i][0]
    drop.update(range(cs, ce + 1))
    text = " ".join(w["t"] for _, w in flat[i + len(OPEN):(j if j >= 0 else end_i + 1)])
    spoken.append({"start": flat[i][1]["s"], "end": flat[end_i][1]["e"], "cards": [c + 1 for c in range(cs, ce + 1)], "text": text})
    if any(k < i for k, (ci, _) in enumerate(flat) if ci == cs):
        notes.append(f"⚠️ الجملة {cs+1} فيها كلام عادي قبل كلمة الافتتاح — انشالت كلها مع التعليمات. راجعها.")
    i = find(OPEN, end_i + 1)

side = ""
for n in ("instructions.txt", "تعليمات.txt"):
    if os.path.exists(P(n)): side = open(P(n), encoding="utf-8").read().strip(); break

found = {"spoken": spoken, "side_file": side, "drop_cards": sorted(c + 1 for c in drop), "notes": notes}
json.dump(found, open(P("instr_found.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

lines = ["# ملف المراجعة — تعليمات المونتاج", ""]
if spoken:
    for k, s in enumerate(spoken, 1):
        lines.append(f"[منطوقة {k}] {s['start']:.1f}–{s['end']:.1f}ث (جُمل {s['cards']}): {s['text']}")
else:
    lines.append("لا تعليمات منطوقة في الفيديو.")
lines.append("[ملف نصي] " + (side if side else "لا يوجد ملف تعليمات جنب الفيديو."))
lines += notes
open(P("review.txt"), "a", encoding="utf-8").write("\n".join(lines) + "\n\n")
print("\n".join(lines))

if APPLY and drop:
    here = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([sys.executable, os.path.join(here, "10_script_edit.py"), W, "drop"] + [str(c + 1) for c in sorted(drop)], check=True)
