"""Raw video -> edited 9:16 reels + per-platform copy + schedule -> Drive + Sheet."""
import argparse
import csv
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(__file__))
import clips as clips_mod  # noqa: E402
import content  # noqa: E402
import edit  # noqa: E402
import google_io  # noqa: E402
import schedule  # noqa: E402
from transcribe import transcribe  # noqa: E402

import json  # noqa: E402

HEADER = ["id", "created_at", "source", "clip", "platform", "scheduled_at", "status",
          "caption", "hashtags", "marketing_message", "comments", "video_url"]


def fetch_source(args, work):
    dest = os.path.join(work, "source.mp4")
    if args.youtube_url:
        subprocess.run(["yt-dlp", "-f", "bv*[height<=1080]+ba/b", "--merge-output-format", "mp4",
                        "-o", dest, args.youtube_url], check=True)
        return dest, args.youtube_url
    if args.file_id:
        name = google_io.download(args.file_id, dest)
        return dest, name
    if args.local:
        return args.local, os.path.basename(args.local)
    sys.exit("give --file-id, --youtube-url or --local")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file-id")
    ap.add_argument("--youtube-url")
    ap.add_argument("--local")
    ap.add_argument("--clips", type=int, default=5)
    ap.add_argument("--mode", choices=["auto", "single", "long"], default="auto")
    ap.add_argument("--language", default=None)
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    brand = json.load(open(os.path.join(os.path.dirname(__file__), "..", "brand.json"), encoding="utf-8"))
    os.makedirs(args.out, exist_ok=True)
    use_google = google_io.enabled()
    folder = os.environ.get("DRIVE_OUTPUT_FOLDER_ID")
    sheet = os.environ.get("SHEET_ID")

    with tempfile.TemporaryDirectory() as work:
        src, source_name = fetch_source(args, work)
        tr = transcribe(src, language=args.language)
        words = [w for s in tr["segments"] for w in s["words"]]
        if args.mode == "single":
            tr_for_clips = {"duration": min(tr["duration"], 90), "segments": tr["segments"]}
        else:
            tr_for_clips = tr
        picked = clips_mod.select_clips(tr_for_clips, args.clips)
        rows, now = [], datetime.now(ZoneInfo(brand["timezone"]))
        for i, clip in enumerate(picked):
            tag = uuid.uuid4().hex[:8]
            out_path = os.path.join(args.out, f"reel_{i + 1}_{tag}.mp4")
            edit.render(src, out_path, words, clip["start"], clip["end"], brand, work)
            copy, status = content.generate(clip, brand)
            url = out_path
            if use_google and folder:
                _, url = google_io.upload(out_path, folder)
            for p in content.PLATFORMS:
                when = schedule.slot_for(p, i, brand["timezone"], now)
                rows.append([f"{tag}-{p}", now.isoformat(timespec="seconds"), source_name, clip["title"],
                             p, when.isoformat(timespec="minutes"), status,
                             copy["captions"].get(p, ""), content.hashtag_str(copy, brand),
                             copy.get("marketing_message", ""), " | ".join(copy.get("comments", [])), url])
            print(f"clip {i + 1}/{len(picked)} done -> {url}")

    with open(os.path.join(args.out, "posts.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    if use_google and sheet:
        google_io.append_rows(sheet, rows)
        print(f"{len(rows)} rows appended to sheet")


if __name__ == "__main__":
    main()
