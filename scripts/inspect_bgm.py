import os
import subprocess
import json

BASE_DIR = r"d:\video\视频3"
BGM_DIR = os.path.join(BASE_DIR, "BGM")
files = os.listdir(BGM_DIR)
for f in files:
    full_path = os.path.join(BGM_DIR, f)
    print("Found BGM file:", full_path)
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration,size,bit_rate:stream=codec_name,sample_rate,channels", "-of", "json", full_path]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    info = json.loads(res.stdout)
    dur = float(info["format"]["duration"])
    s = info["streams"][0]
    print(f"Duration: {dur:.2f}s | Codec: {s.get('codec_name')} | SampleRate: {s.get('sample_rate')} | Channels: {s.get('channels')}")

    # Measure loudness with ebur128
    loud_cmd = ["ffmpeg", "-i", full_path, "-af", "ebur128=framelog=verbose", "-f", "null", "-"]
    res_loud = subprocess.run(loud_cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    # find Integrated loudness
    for line in res_loud.stderr.splitlines():
        if "Integrated loudness:" in line or "I:" in line or "LRA:" in line or "Threshold:" in line:
            print(line.strip())
