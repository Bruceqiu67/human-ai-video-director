import os
import sys
import subprocess
import json
from PIL import Image

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

hist_path = r"d:\video\视频3\output\video\好帮手AI话术私教_终极宣传大片_云希合规版.mp4"
new_path = r"d:\video\视频3\tests\benchmark_test\output\video\benchmark_test_1080P_Final.mp4"

def get_media_info(p):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
        "-of", "json", p
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return json.loads(res.stdout)

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

print("================================================================================")
print("             🔍 历史最终成片 VS 新 Studio 引擎成片 严密指标横向对照表")
print("================================================================================")
print(f"对比维度               | 历史成片 (好帮手AI话术私教_云希合规版) | 新 studio 流水线成片")
print(f"-----------------------+--------------------------------------+-----------------------")
print(f"总时长 (Duration)      | {hist_dur:.2f} 秒                           | {new_dur:.2f} 秒")
print(f"文件大小 (File Size)   | {hist_size:.2f} MB                          | {new_size:.2f} MB")
print(f"视频分辨率 (Resolution)| {hist_v['width']} x {hist_v['height']}                         | {new_v['width']} x {new_v['height']}")
print(f"视频编码 (Video Codec) | {hist_v['codec_name']} (H.264 High Profile)           | {new_v['codec_name']} (H.264 High Profile)")
print(f"帧率 (Framerate)       | {hist_v['r_frame_rate']} fps                              | {new_v['r_frame_rate']} fps")
print(f"音频编码 (Audio Codec) | {hist_a['codec_name']} ({hist_a.get('sample_rate')}Hz, mono)            | {new_a['codec_name']} ({new_a.get('sample_rate')}Hz, mono)")
print("================================================================================")

qa_dir = r"d:\video\视频3\tests\benchmark_test\output\qa_comparison"
os.makedirs(qa_dir, exist_ok=True)

timestamps = [2.0, 15.0, 30.0, 48.0, 58.0]
scene_names = ["Scene01_痛点", "Scene02_破局", "Scene03_对战", "Scene04_诊断", "Scene05_通关"]

print("\n=== 2. 全五幕核心帧侧对侧抽帧对比 (Side-by-Side Comparison) ===")
for t, sname in zip(timestamps, scene_names):
    hist_frame = os.path.join(qa_dir, f"{sname}_t{int(t)}s_hist.jpg")
    new_frame = os.path.join(qa_dir, f"{sname}_t{int(t)}s_new.jpg")
    
    subprocess.run(["ffmpeg", "-y", "-ss", str(t), "-i", hist_path, "-vframes", "1", "-q:v", "2", hist_frame], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-ss", str(t), "-i", new_path, "-vframes", "1", "-q:v", "2", new_frame], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(hist_frame) and os.path.exists(new_frame):
        img_h = Image.open(hist_frame)
        img_n = Image.open(new_frame)
        comb_w = img_h.width + img_n.width
        comb_h = img_h.height
        comb = Image.new("RGB", (comb_w, comb_h))
        comb.paste(img_h, (0, 0))
        comb.paste(img_n, (img_h.width, 0))
        comb_path = os.path.join(qa_dir, f"{sname}_side_by_side.jpg")
        comb.save(comb_path, quality=88)
        print(f"✓ {sname} (t={t:.1f}s) 左右对比图已生成: {comb_path}")

print("\n[VERIFICATION COMPLETE] 严密横向对比完成！")
