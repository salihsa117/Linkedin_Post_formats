"""Cut silences, reframe to 9:16 and burn word-synced Arabic captions with ffmpeg."""
import json
import os
import subprocess

W, H = 1080, 1920


def _ass_color(hex_rgb):
    h = hex_rgb.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}".upper()


def keep_segments(words, t0, t1, max_gap=0.45, pad=0.10):
    """Speech spans inside [t0, t1], merging gaps shorter than max_gap."""
    ws = [w for w in words if w["end"] > t0 and w["start"] < t1]
    if not ws:
        return [(t0, t1)]
    spans = []
    for w in ws:
        s, e = max(w["start"], t0), min(w["end"], t1)
        if spans and s - spans[-1][1] <= max_gap:
            spans[-1][1] = e
        else:
            spans.append([s, e])
    out = []
    for s, e in spans:
        s, e = max(t0, s - pad), min(t1, e + pad)
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [tuple(x) for x in out]


def _remap(t, segs):
    off = 0.0
    for s, e in segs:
        if t <= e:
            return off + max(0.0, t - s)
        off += e - s
    return off


def _fmt(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def build_ass(words, segs, t0, t1, brand):
    c = brand["caption"]
    ws = [w for w in words if w["start"] >= t0 - 0.05 and w["end"] <= t1 + 0.05]
    n = c.get("words_per_line", 4)
    chunks, cur = [], []
    for w in ws:
        cur.append(w)
        if len(cur) >= n or w["word"][-1:] in ".!?؟،,":
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
        "WrapStyle: 0", "", "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
        "Alignment,MarginL,MarginR,MarginV,Encoding",
        f"Style: Default,{c['font']},{c['size']},{_ass_color(c['color'])},{_ass_color(c['color'])},"
        f"{_ass_color(c['outline'])},&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,60,60,{c['margin_bottom']},1",
        "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    ]
    hi = _ass_color(c["highlight"])
    base = _ass_color(c["color"])
    for chunk in chunks:
        for i, w in enumerate(chunk):
            start = _remap(w["start"], segs)
            end = _remap(chunk[i + 1]["start"], segs) if i + 1 < len(chunk) else _remap(w["end"], segs)
            end = max(end, start + 0.12)
            # one colour run per word: libass keeps Arabic word order only when runs are single words
            text = " ".join(f"{{\\c{hi if j == i else base}}}{x['word']}" for j, x in enumerate(chunk))
            lines.append(f"Dialogue: 0,{_fmt(start)},{_fmt(end)},Default,,0,0,0,,{text}")
    return "\n".join(lines) + "\n"


def probe_size(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "json", path],
        capture_output=True, text=True, check=True)
    st = json.loads(r.stdout)["streams"][0]
    return st["width"], st["height"]


def render(src, out, words, t0, t1, brand, workdir, fit="auto"):
    segs = keep_segments(words, t0, t1)
    ass_path = os.path.join(workdir, "captions.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(build_ass(words, segs, t0, t1, brand))
    w, h = probe_size(src)
    if fit == "auto":
        fit = "crop" if w / h <= 0.8 else "blur"
    parts, labels = [], []
    for i, (s, e) in enumerate(segs):
        parts.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    parts.append(f"{''.join(labels)}concat=n={len(segs)}:v=1:a=1[cv][ca]")
    if fit == "crop":
        parts.append(f"[cv]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[fv]")
    else:
        parts.append("[cv]split[bg][fg]")
        parts.append(f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:5[b]")
        parts.append(f"[fg]scale={W}:-2[f]")
        parts.append("[b][f]overlay=(W-w)/2:(H-h)/2,setsar=1[fv]")
    ass_esc = ass_path.replace("\\", "/").replace(":", "\\:")
    fonts = os.environ.get("FONTS_DIR")
    fd = f":fontsdir={fonts}" if fonts else ""
    parts.append(f"[fv]ass='{ass_esc}'{fd}[vout]")
    parts.append("[ca]loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
    script = os.path.join(workdir, "filter.txt")
    with open(script, "w", encoding="utf-8") as f:
        f.write(";\n".join(parts))
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", src, "-filter_complex_script", script,
         "-map", "[vout]", "-map", "[aout]", "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
         "-movflags", "+faststart", out], check=True)
    return sum(e - s for s, e in segs)
