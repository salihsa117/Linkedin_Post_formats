# إعداد النظام (مجاني بالكامل)

```
تحط الفيديو في فولدر Inbox على Drive
  → Apps Script (يعمل كل 5 دقائق) ينقل الفيديو ويشغّل GitHub Actions
  → Actions: تفريغ Whisper ← قص السكتات ← 9:16 + كابشن عربي ← اختيار ريلز ← نصوص كل منصة
  → يرفع الـ MP4 للدرايف ويضيف صفوف الجدولة في Google Sheet (صف لكل منصة)
  → أنت تغيّر الحالة إلى approved من الجوال ← Apps Script يرسلها لأداة النشر في موعدها
```

## 1) في Google Drive
1. أنشئ ثلاثة فولدرات: `Inbox` (ترفع فيه الخام) و`Work` و`Reels` (المخرجات). خذ ID كل فولدر من رابطه.
2. أنشئ Google Sheet فيه تبويبان:
   - `Posts`: الصف الأول هذه الأعمدة بالترتيب:
     `id, created_at, source, clip, platform, scheduled_at, status, caption, hashtags, marketing_message, comments, video_url`
   - `Links`: العمود A لروابط يوتيوب (اللصق هنا يشغّل المعالجة).

## 2) مفاتيح جوجل (مرة واحدة، تُعمل من متصفح الجوال أو الكمبيوتر)
1. في Google Cloud Console أنشئ مشروعاً وفعّل Drive API وSheets API.
2. أنشئ OAuth Client من نوع Web وأضف `https://developers.google.com/oauthplayground` كـ redirect URI.
3. في OAuth Playground فعّل "Use your own OAuth credentials"، واختر نطاقي `drive` و`spreadsheets`، ثم Exchange لتحصل على **refresh token**.
4. تأكد أن شاشة الموافقة مضبوطة على "In production" وإلا ينتهي التوكن بعد 7 أيام.

## 3) أسرار GitHub (Settings → Secrets and variables → Actions)
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, `DRIVE_OUTPUT_FOLDER_ID` (فولدر Reels), `SHEET_ID`,
و`ANTHROPIC_API_KEY` اختياري (بدونه تُكتب كابشنات بدائية وتُوسم الصفوف `needs_review`).
الريبو عام، فلا تضع أي مفتاح داخل الملفات أبداً.

متغير اختياري (Variables): `WHISPER_MODEL` = `small` (الافتراضي) أو `medium` للدقة الأعلى في العربي مع بطء أكثر.

## 4) Apps Script
1. من الشيت: Extensions → Apps Script، والصق `apps-script/Code.gs`.
2. Project Settings → Script Properties: `GH_TOKEN` (توكن GitHub محدد على هذا الريبو بصلاحية Actions: Read and write)،
   `GH_REPO`, `INBOX_FOLDER_ID`, `WORK_FOLDER_ID`, `SHEET_ID`.
3. Triggers: `scanInbox` كل 5 دقائق، و`publishDue` كل 15 دقيقة.

## 5) ادمج الفرع في main
تشغيل الـ workflow عبر Apps Script يتم على `main`، فلازم يوجد ملف `.github/workflows/process-video.yml` هناك.

## 6) النشر
`publishDue` يرسل JSON بكل صف معتمد إلى `PUBLISH_WEBHOOK`. اختر أداة النشر (Postiz أو Blotato أو غيرها) وحدد رابطها لاحقاً؛
الرابط والتوثيق يختلفان حسب الأداة، وهذه الخطوة لم تُختبر بعد.

## حدود معروفة
- لم يُختبر التفريغ على كلام عربي حقيقي بعد، ارفع أول فيديو قصير واحكم على الدقة.
- تحميل يوتيوب بـ yt-dlp قد يُحجب من خوادم GitHub؛ الأضمن رفع الفيديو على الدرايف.
- الجدولة تستخدم أوقاتاً افتراضية لكل منصة (تعدّل من `pipeline/schedule.py`) وليست مبنية على تحليلات حقيقية.
