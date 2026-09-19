import os
import json
import shutil

test_dir = r"d:\video\视频3\tests\benchmark_test"
os.makedirs(os.path.join(test_dir, "assets", "masterframes"), exist_ok=True)
os.makedirs(os.path.join(test_dir, "assets", "bgm"), exist_ok=True)
os.makedirs(os.path.join(test_dir, "assets", "anchors"), exist_ok=True)
os.makedirs(os.path.join(test_dir, "audio"), exist_ok=True)

# Copy the exact manifest_yunxi.json as audio manifest
manifest_src = r"d:\video\视频3\output\audio\manifest_yunxi.json"
with open(manifest_src, "r", encoding="utf-8") as f:
    raw_manifest = json.load(f)

std_manifest = {}
for sc_id, segs in raw_manifest.items():
    tot = segs[-1]["end"] + segs[-1].get("pause_after", 0.4)
    std_manifest[sc_id] = {
        "total_duration": round(tot, 3),
        "segments": segs
    }

manifest_dst = os.path.join(test_dir, "audio", "timestamps_manifest.json")
with open(manifest_dst, "w", encoding="utf-8") as f:
    json.dump(std_manifest, f, ensure_ascii=False, indent=2)

# Copy existing master audio wav files
for sc_id in raw_manifest.keys():
    src_wav = os.path.join(r"d:\video\视频3\output\audio", f"{sc_id}_yunxi_master.wav")
    dst_wav = os.path.join(test_dir, "audio", f"{sc_id}_master.wav")
    if os.path.exists(src_wav):
        shutil.copy2(src_wav, dst_wav)

# Copy BGM
bgm_src = r"d:\video\视频3\素材\06_音效与音频资产\bgm_first_beat.mp3"
if os.path.exists(bgm_src):
    shutil.copy2(bgm_src, os.path.join(test_dir, "assets", "bgm", "bgm.mp3"))

# Copy real masterframes from 素材/04_分幕原生画卷 to assets/masterframes/
masterframes_src = r"d:\video\视频3\素材\04_分幕原生画卷"
masterframes_dst = os.path.join(test_dir, "assets", "masterframes")
for fname in os.listdir(masterframes_src):
    if fname.lower().endswith((".jpg", ".png", ".jpeg")):
        shutil.copy2(os.path.join(masterframes_src, fname), os.path.join(masterframes_dst, fname))

print("Real masterframes copied to benchmark test:", len(os.listdir(masterframes_dst)))
