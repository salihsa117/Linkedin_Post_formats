# التشغيل المحلي على ويندوز

1. نزّل المستودع (مرة وحدة):
   `git clone -b claude/mobile-video-editing-me9lgl https://github.com/salihsa117/linkedin_post_formats`
2. من PowerShell داخل المجلد:
   ```
   Set-ExecutionPolicy -Scope Process Bypass
   .\windows\install.ps1 -WorkDir "C:\Users\ASUS\Videos\mon"
   ```
   يثبّت: ffmpeg · python · node · git · Chrome · faster-whisper · puppeteer-core ونموذج وِسبر medium، وينسخ السكل لمجلد الشغل.
   (لم يُجرَّب على ويندوز؛ أول تشغيل على جهازك هو الاختبار.)
3. افتح Claude Code من مجلد الشغل واطلب المونتاج. مزامنة صوت المايك مع فيديو الكاميرا:
   `python .claude\skills\saleh-reels\scripts\36_sync_audio.py cam.mp4 mic.mp4 synced.mp4`
