# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import shutil

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = r"d:\video\视频3"
VIDEO_DIR = os.path.join(BASE_DIR, "output", "video")
MASTER_ORIG = os.path.join(VIDEO_DIR, "好帮手AI话术私教_终极宣传大片_1080P.mp4")
BACKUP_NO_BGM = os.path.join(VIDEO_DIR, "好帮手AI话术私教_终极宣传大片_1080P_无BGM纯享版.mp4")
BGM_FILE = os.path.join(BASE_DIR, "素材", "06_音效与音频资产", "bgm_first_beat.mp3")
MASTER_FINAL = os.path.join(VIDEO_DIR, "好帮手AI话术私教_终极宣传大片_1080P.mp4")
TEMP_FINAL = os.path.join(VIDEO_DIR, "master_with_bgm_temp.mp4")

def mix_bgm():
    print("=== 开始为终极宣传大片混录背景音乐 (BGM Mixing Pipeline) ===")
    
    # 1. 备份原纯人声+音效版本
    if not os.path.exists(BACKUP_NO_BGM) and os.path.exists(MASTER_ORIG):
        print(f"备份无 BGM 原始视频 -> {BACKUP_NO_BGM}")
        shutil.copy2(MASTER_ORIG, BACKUP_NO_BGM)
        
    source_video = BACKUP_NO_BGM if os.path.exists(BACKUP_NO_BGM) else MASTER_ORIG
    
    # 2. 获取成片精确时长
    cmd_dur = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", source_video
    ]
    total_dur = float(subprocess.check_output(cmd_dur, text=True).strip())
    print(f"视频总时长: {total_dur:.3f} 秒")
    print(f"BGM 音频文件: {BGM_FILE}")
    
    fade_out_start = max(0.0, total_dur - 3.0)
    
    # 3. 构建音频混音滤镜链 (Audio Filter Graph)
    # - [0:a]: 原主音轨 (人声+物理音效), 微调 volume=1.05 增强穿透力
    # - [1:a]: BGM 背景音乐
    #   * volume=0.13 (-17.7dB), 确保背景音乐柔和铺底、绝对不抢人声
    #   * equalizer: 2.2kHz (人声核心频段) 衰减 3dB, 为导师人声留出透明频响口袋 (Vocal Pocketing)
    #   * afade in: 0~1.0s 柔和淡入
    #   * afade out: 最后 3 秒柔和淡出
    #   * aresample=44100 采样率严格统一
    # - amix: 混合双轨
    # - alimiter: -0.45dBFS 硬限幅防爆音
    filter_complex = (
        "[0:a]volume=1.05,aresample=44100[voice];"
        f"[1:a]volume=0.13,equalizer=f=2200:width_type=h:width=1800:g=-3,"
        f"afade=t=in:ss=0:d=1.0,afade=t=out:st={fade_out_start:.2f}:d=3.0,"
        f"aresample=44100,atrim=0:{total_dur}[bgm];"
        "[voice][bgm]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mixed];"
        "[mixed]alimiter=limit=0.95[out_a]"
    )
    
    # 4. 执行 FFmpeg 流复制与音频重封装 (视频流 -c:v copy 零损耗秒速封装)
    cmd = [
        "ffmpeg", "-y",
        "-i", source_video,
        "-i", BGM_FILE,
        "-filter_complex", filter_complex,
        "-map", "0:v:0",
        "-map", "[out_a]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "320k",
        "-movflags", "+faststart",
        TEMP_FINAL
    ]
    
    print("执行音频流混响合成命令...")
    res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
    if res.returncode != 0:
        print("合成出错:", res.stderr)
        return False
        
    # 替换目标成品文件
    if os.path.exists(MASTER_FINAL):
        os.remove(MASTER_FINAL)
    shutil.move(TEMP_FINAL, MASTER_FINAL)
    
    final_size = os.path.getsize(MASTER_FINAL) / (1024 * 1024)
    print(f"\n[SUCCESS] 终极宣传大片 (含专属 BGM) 混音封装成功！")
    print(f"成片路径: {MASTER_FINAL}")
    print(f"成片大小: {final_size:.2f} MB")
    print(f"成片总时长: {total_dur:.3f} 秒")
    return True

if __name__ == "__main__":
    mix_bgm()
