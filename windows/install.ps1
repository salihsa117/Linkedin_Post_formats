# تثبيت أدوات المونتاج على ويندوز — saleh-reels
# التشغيل (PowerShell عادي، مو لازم Administrator):
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\windows\install.ps1 -WorkDir "C:\Users\ASUS\Videos\mon"
# ⚠️ لم يُجرَّب على ويندوز. أي خطأ الصقه لـClaude يصلحه.
param(
  [string]$WorkDir = "$env:USERPROFILE\Videos\mon",
  [switch]$SkipModel
)
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot          # جذر المستودع (المجلد اللي فيه windows\)
function Have($c){ [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Step($m){ Write-Host "`n==> $m" -ForegroundColor Green }

if (-not (Have winget)) { throw "winget غير موجود. حدّث 'App Installer' من متجر مايكروسوفت ثم أعد التشغيل." }

# 1) البرامج (تُنزَّل فقط لو ناقصة)
$pk = @(
  @{cmd="ffmpeg"; id="Gyan.FFmpeg"},
  @{cmd="python"; id="Python.Python.3.12"},
  @{cmd="node";   id="OpenJS.NodeJS.LTS"},
  @{cmd="git";    id="Git.Git"}
)
foreach ($p in $pk) {
  if (Have $p.cmd) { Write-Host "✓ $($p.cmd) موجود" }
  else { Step "تثبيت $($p.id)"; winget install --id $p.id -e --silent --accept-package-agreements --accept-source-agreements }
}
$chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe","${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe","$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $chrome) { Step "تثبيت Chrome"; winget install --id Google.Chrome -e --silent --accept-package-agreements --accept-source-agreements
  $chrome = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe" }

# تحديث PATH للجلسة الحالية بعد التثبيت
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
foreach ($c in "ffmpeg","python","node") { if (-not (Have $c)) { throw "$c ما زال غير ظاهر. أغلق PowerShell وافتحه من جديد ثم أعد تشغيل السكربت." } }

# 2) حزم بايثون
Step "حزم بايثون (faster-whisper, numpy)"
python -m pip install --upgrade pip
python -m pip install faster-whisper numpy pillow

# 3) puppeteer-core للرسم
$Tools = "$env:USERPROFILE\montage-tools"
New-Item -ItemType Directory -Force $Tools | Out-Null
Step "تثبيت puppeteer-core"
Push-Location $Tools; if (-not (Test-Path package.json)) { npm init -y | Out-Null }; npm install puppeteer-core; Pop-Location
[Environment]::SetEnvironmentVariable("PUPPETEER_PATH", "$Tools\node_modules\puppeteer-core", "User")
[Environment]::SetEnvironmentVariable("CHROME_PATH", $chrome, "User")
$env:PUPPETEER_PATH = "$Tools\node_modules\puppeteer-core"; $env:CHROME_PATH = $chrome

# 4) نموذج وِسبر (~1.5GB)
if (-not $SkipModel) {
  Step "تنزيل نموذج وِسبر medium (~1.5GB، مرة وحدة)"
  python -c "from faster_whisper import WhisperModel; WhisperModel('medium', device='cpu', compute_type='int8'); print('model ok')"
}

# 5) نسخ السكل والثيمات لمجلد الشغل
Step "نسخ السكل إلى $WorkDir"
New-Item -ItemType Directory -Force "$WorkDir\.claude\skills" | Out-Null
Copy-Item "$Repo\.claude\skills\saleh-reels" "$WorkDir\.claude\skills\" -Recurse -Force
Copy-Item "$Repo\themes" "$WorkDir\themes" -Recurse -Force
Copy-Item "$Repo\CLAUDE.md" "$WorkDir\CLAUDE.md" -Force

Step "فحص نهائي"
ffmpeg -version | Select-Object -First 1
python --version; node --version
Write-Host "Chrome: $chrome"
Write-Host "`n✅ جاهز. افتح Claude Code من المجلد: cd `"$WorkDir`"; claude" -ForegroundColor Green
Write-Host "ملاحظة: متغيرات PUPPETEER_PATH وCHROME_PATH انحفظت للمستخدم؛ افتح PowerShell جديد."
