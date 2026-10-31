# -*- coding: utf-8 -*-
"""يزامن صوت المايك (فيديو/ملف صوت بلا صورة) مع فيديو الكاميرا، ويبدّل صوت الكاميرا بصوت المايك.

    python 36_sync_audio.py <video_with_picture> <mic_audio_or_video> <out.mp4> [--no-replace]

الفكرة: يقارن موجة صوت الكاميرا بموجة المايك (ارتباط متقاطع) ويحسب الإزاحة بالضبط،
ثم يقصّ أو يؤخّر صوت المايك ويركّبه على الصورة. يفحص الانجراف (drift) في أول الفيديو وآخره
ويحذّر لو تجاوز 40 مللي ثانية (ما يصحّحه: يطبعه للمراجعة).
--no-replace: يكتفي بطباعة الإزاحة بلا إخراج ملف.
"""
import sys, os, subprocess, tempfile, numpy as np

SR = 8000
def wav(path, start=0, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(start)] + (["-t", str(dur)] if dur else []) + \
          ["-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)

def env(x):
    # غلاف طاقة مصقول: يتجاهل اختلاف جودة المايكين والضجيج
    n = SR // 100
    k = len(x) // n
    e = np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1) + 1e-9)
    e = np.log(e + 1e-4)
    return e - e.mean(), 100.0

def xcorr_lag(a, b, maxlag_s=None):
    """b[n+k] ≈ a[n] → k بالثواني (موجب = b متأخر عن a)"""
    ea, f = env(a); eb, _ = env(b)
    n = 1 << (len(ea) + len(eb)).bit_length()
    c = np.fft.irfft(np.fft.rfft(eb, n) * np.conj(np.fft.rfft(ea, n)), n)
    c = np.concatenate([c[-(len(ea) - 1):], c[:len(eb)]])
    lags = np.arange(-(len(ea) - 1), len(eb))
    if maxlag_s: m = np.abs(lags) <= maxlag_s * f; c, lags = c[m], lags[m]
    i = int(np.argmax(c)); return lags[i] / f, float(c[i] / (np.linalg.norm(ea) * np.linalg.norm(eb) + 1e-9))

def refine(cam_path, mic_path, coarse):
    """تدقيق بالعينات: ارتباط الموجة نفسها حول الإزاحة التقريبية (±50ms)"""
    d = 20.0
    a = wav(cam_path, 0, d)
    s = max(0.0, coarse)
    b = wav(mic_path, s - 0.2 if s > 0.2 else 0, d + 0.6)
    off0 = (s - 0.2) if s > 0.2 else 0.0
    n = 1 << (len(a) + len(b)).bit_length()
    c = np.fft.irfft(np.fft.rfft(b, n) * np.conj(np.fft.rfft(a, n)), n)
    c = np.concatenate([c[-(len(a) - 1):], c[:len(b)]])
    lags = np.arange(-(len(a) - 1), len(b)) / SR + off0
    m = np.abs(lags - coarse) <= 0.05
    return float(lags[m][np.argmax(c[m])])

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2: sys.exit(__doc__)
    cam, mic = args[0], args[1]
    out = args[2] if len(args) > 2 else None
    a, b = wav(cam), wav(mic)
    lag, score = xcorr_lag(a, b)
    lag = refine(cam, mic, lag)
    print(f"الإزاحة: {lag:+.3f} ثانية (موجب = المايك متأخر عن الكاميرا · سالب = المايك مبكّر) · ثقة {score:.2f}")
    if score < 0.25: print("⚠️ الثقة منخفضة — تأكد إن الملفين نفس التسجيل")
    # الانجراف: قارن إزاحة آخر 20 ثانية
    dur_cam = len(a) / SR
    if dur_cam > 60:
        t = dur_cam - 25
        a2 = wav(cam, t, 20); b2 = wav(mic, max(0, t + lag - 2), 24)
        l2, s2 = xcorr_lag(a2, b2)
        l2 = l2 + max(0, t + lag - 2) - t
        print(f"إزاحة آخر الفيديو: {l2:+.3f}ث · فرق الانجراف {abs(l2 - lag) * 1000:.0f}ms" +
              ("  ⚠️ فوق 40ms" if abs(l2 - lag) > 0.04 else ""))
    if "--no-replace" in sys.argv or not out: return
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", cam],
                         capture_output=True, text=True).stdout.strip()
    if lag >= 0: af = f"atrim=start={lag:.4f},asetpts=PTS-STARTPTS"
    else: af = f"adelay={int(round(-lag * 1000))}:all=1"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", cam, "-i", mic, "-filter_complex",
                    f"[1:a]{af},apad[a]", "-map", "0:v", "-map", "[a]", "-t", dur,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out], check=True)
    print("✅", out)

if __name__ == "__main__": main()
