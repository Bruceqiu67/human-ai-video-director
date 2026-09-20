"""Prepare a local benchmark project from repo-relative assets (not a CI test)."""

from __future__ import annotations

import json
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
test_dir = os.path.join(ROOT, "tests", "benchmark_test")
os.makedirs(os.path.join(test_dir, "assets", "masterframes"), exist_ok=True)
os.makedirs(os.path.join(test_dir, "assets", "bgm"), exist_ok=True)
os.makedirs(os.path.join(test_dir, "assets", "anchors"), exist_ok=True)
os.makedirs(os.path.join(test_dir, "audio"), exist_ok=True)

manifest_src = os.path.join(ROOT, "output", "audio", "manifest_yunxi.json")
if not os.path.isfile(manifest_src):
    raise FileNotFoundError(
        f"Local audio manifest not found: {manifest_src}. "
        "This helper is for the original film checkout only."
    )

with open(manifest_src, "r", encoding="utf-8") as handle:
    raw_manifest = json.load(handle)

std_manifest = {}
for sc_id, segs in raw_manifest.items():
    if isinstance(segs, dict) and "segments" in segs:
        std_manifest[sc_id] = segs
        continue
    tot = segs[-1]["end"] + segs[-1].get("pause_after", 0.4)
    std_manifest[sc_id] = {
        "total_duration": round(tot, 3),
        "segments": segs,
    }

manifest_dst = os.path.join(test_dir, "audio", "timestamps_manifest.json")
with open(manifest_dst, "w", encoding="utf-8") as handle:
    json.dump(std_manifest, handle, ensure_ascii=False, indent=2)

audio_root = os.path.join(ROOT, "output", "audio")
for sc_id in std_manifest:
    src_wav = os.path.join(audio_root, f"{sc_id}_yunxi_master.wav")
    dst_wav = os.path.join(test_dir, "audio", f"{sc_id}_master.wav")
    if os.path.exists(src_wav):
        shutil.copy2(src_wav, dst_wav)

bgm_src = os.path.join(ROOT, "素材", "06_音效与音频资产", "bgm_first_beat.mp3")
if os.path.exists(bgm_src):
    shutil.copy2(bgm_src, os.path.join(test_dir, "assets", "bgm", "bgm.mp3"))

masterframes_src = os.path.join(ROOT, "素材", "04_分幕原生画卷")
masterframes_dst = os.path.join(test_dir, "assets", "masterframes")
if os.path.isdir(masterframes_src):
    for fname in os.listdir(masterframes_src):
        if fname.lower().endswith((".jpg", ".png", ".jpeg")):
            shutil.copy2(os.path.join(masterframes_src, fname), os.path.join(masterframes_dst, fname))
    print("Real masterframes copied to benchmark test:", len(os.listdir(masterframes_dst)))
else:
    print("No local 素材/04_分幕原生画卷 directory; skipped masterframe copy.")
