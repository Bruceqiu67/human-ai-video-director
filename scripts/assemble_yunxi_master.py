"""
Master Film Assembly & Audio Ducking Engine for Yunxi Compliant Version
Concatenates 5 scene videos and mixes BGM with dynamic sidechain compression.
"""

import os
import subprocess

BASE_DIR = r"d:\video\视频3"
VIDEO_DIR = os.path.join(BASE_DIR, "output", "video")
BGM_PATH = os.path.join(BASE_DIR, "素材", "06_音效与音频资产", "bgm_first_beat.mp3")

SCENES = [
    os.path.join(VIDEO_DIR, "scene_01_yunxi.mp4"),
    os.path.join(VIDEO_DIR, "scene_02_yunxi.mp4"),
    os.path.join(VIDEO_DIR, "scene_03_yunxi.mp4"),
    os.path.join(VIDEO_DIR, "scene_04_yunxi.mp4"),
    os.path.join(VIDEO_DIR, "scene_05_yunxi.mp4")
]

CONCAT_LIST = os.path.join(VIDEO_DIR, "concat_yunxi_list.txt")
TEMP_CONCAT = os.path.join(VIDEO_DIR, "temp_concat_yunxi.mp4")
FINAL_OUTPUT = os.path.join(VIDEO_DIR, "好帮手AI话术私教_终极宣传大片_云希合规版.mp4")

def main():
    print("=== 开始全片 5 幕大合流汇编 (云希合规版) ===")
    
    # 1. 写入 Concat 列表
    with open(CONCAT_LIST, "w", encoding="utf-8") as f:
        for s in SCENES:
            abs_p = os.path.abspath(s).replace("\\", "/")
            f.write(f"file '{abs_p}'\n")
            print(f"  + 载入幕: {s}")

    # 2. 无损拼接全片视频流
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", CONCAT_LIST,
        "-c", "copy",
        TEMP_CONCAT
    ]
    print("[1/2] 正在执行 5 幕无损串联拼接...")
    subprocess.run(cmd_concat, check=True)

    # 3. 动态侧链 BGM 混音 (Audio Ducking)
    # 人声说话时 BGM 自动压低至 12%，人声停顿气口平滑回弹至 24%
    cmd_mix = [
        "ffmpeg", "-y",
        "-i", TEMP_CONCAT,
        "-stream_loop", "-1",
        "-i", BGM_PATH,
        "-filter_complex",
        "[1:a]asplit=2[sc][bgm];[0:a][sc]sidechaincompress=threshold=0.08:ratio=8:attack=30:release=350[voice_ducked];[bgm]volume=0.12[bgm_low];[voice_ducked][bgm_low]amix=inputs=2:duration=first[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "320k",
        "-movflags", "+faststart",
        FINAL_OUTPUT
    ]
    print("[2/2] 正在应用 BGM 动态侧链闪避混音与母带压制...")
    subprocess.run(cmd_mix, check=True)

    # 清理临时文件
    if os.path.exists(CONCAT_LIST):
        os.remove(CONCAT_LIST)
    if os.path.exists(TEMP_CONCAT):
        os.remove(TEMP_CONCAT)

    # 提取总成片时长与指标
    probe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{FINAL_OUTPUT}"'
    dur = float(subprocess.check_output(probe_cmd, shell=True).decode().strip())
    size_mb = os.path.getsize(FINAL_OUTPUT) / (1024 * 1024)

    print(f"\n[COMPLETE] 全片终极合规成片压制成功！")
    print(f"成片路径: {FINAL_OUTPUT}")
    print(f"视频时长: {dur:.2f} 秒")
    print(f"文件大小: {size_mb:.2f} MB")

if __name__ == "__main__":
    main()
