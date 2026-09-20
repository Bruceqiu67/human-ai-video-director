"""Side-by-side compare of the historical master vs a studio rebuild (local helper)."""

from __future__ import annotations

import json
import os
import subprocess
import sys

from PIL import Image

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
hist_path = os.path.join(ROOT, "output", "video", "好帮手AI话术私教_终极宣传大片_云希合规版.mp4")
new_path = os.path.join(ROOT, "tests", "benchmark_test", "output", "video", "benchmark_test_1080P_Final.mp4")


def get_media_info(path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
        "-of", "json", path,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}:\n{res.stderr}")
    return json.loads(res.stdout)


def main() -> None:
    if not os.path.isfile(hist_path) or not os.path.isfile(new_path):
        raise FileNotFoundError(
            "Both historical master and new studio master must exist:\n"
            f"  {hist_path}\n  {new_path}"
        )

    hist_info = get_media_info(hist_path)
    new_info = get_media_info(new_path)
    hist_dur = float(hist_info["format"]["duration"])
    new_dur = float(new_info["format"]["duration"])
    hist_size = os.path.getsize(hist_path) / (1024 * 1024)
    new_size = os.path.getsize(new_path) / (1024 * 1024)
    hist_v = next(s for s in hist_info["streams"] if s["codec_type"] == "video")
    new_v = next(s for s in new_info["streams"] if s["codec_type"] == "video")
    hist_a = next(s for s in hist_info["streams"] if s["codec_type"] == "audio")
    new_a = next(s for s in new_info["streams"] if s["codec_type"] == "audio")

    print("=" * 80)
    print("Historical master vs studio pipeline rebuild")
    print("=" * 80)
    print(f"Duration     | {hist_dur:.2f}s | {new_dur:.2f}s")
    print(f"Size         | {hist_size:.2f} MB | {new_size:.2f} MB")
    print(f"Resolution   | {hist_v['width']}x{hist_v['height']} | {new_v['width']}x{new_v['height']}")
    print(f"Video codec  | {hist_v['codec_name']} | {new_v['codec_name']}")
    print(f"Audio codec  | {hist_a['codec_name']} {hist_a.get('sample_rate')}Hz | {new_a['codec_name']} {new_a.get('sample_rate')}Hz")

    qa_dir = os.path.join(ROOT, "tests", "benchmark_test", "output", "qa_comparison")
    os.makedirs(qa_dir, exist_ok=True)
    timestamps = [2.0, 15.0, 30.0, 48.0, 58.0]
    scene_names = ["Scene01", "Scene02", "Scene03", "Scene04", "Scene05"]
    for t, sname in zip(timestamps, scene_names):
        hist_frame = os.path.join(qa_dir, f"{sname}_t{int(t)}s_hist.jpg")
        new_frame = os.path.join(qa_dir, f"{sname}_t{int(t)}s_new.jpg")
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(t), "-i", hist_path, "-vframes", "1", "-q:v", "2", hist_frame],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-ss", str(t), "-i", new_path, "-vframes", "1", "-q:v", "2", new_frame],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
        )
        if os.path.exists(hist_frame) and os.path.exists(new_frame):
            img_h = Image.open(hist_frame)
            img_n = Image.open(new_frame)
            comb = Image.new("RGB", (img_h.width + img_n.width, img_h.height))
            comb.paste(img_h, (0, 0))
            comb.paste(img_n, (img_h.width, 0))
            comb.save(os.path.join(qa_dir, f"{sname}_side_by_side.jpg"), quality=88)
            print(f"Wrote comparison for {sname} t={t:.1f}s")


if __name__ == "__main__":
    main()
