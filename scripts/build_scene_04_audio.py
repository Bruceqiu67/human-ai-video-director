import asyncio
import os
import subprocess
import edge_tts

BASE_DIR = r"d:\video\视频3"
AUDIO_DIR = os.path.join(BASE_DIR, "output", "audio")
SFX_DIR = os.path.join(BASE_DIR, "素材", "06_音效与音频资产")
MASTER_OUT = os.path.join(AUDIO_DIR, "scene4_master_audio.wav")

os.makedirs(AUDIO_DIR, exist_ok=True)

SEGMENTS = [
    {
        "id": "s1",
        "text": "一通练完，AI立刻输出深度体检单！",
        "target_dur": 1.90,
        "start": 0.50
    },
    {
        "id": "s2",
        "text": "第一次只有45分？",
        "target_dur": 1.15,
        "start": 2.50
    },
    {
        "id": "s3",
        "text": "别慌，它给的可不是泛泛的加油，而是指骨到肉的解法：开场白太冗长？直接教你‘利益前置’——",
        "target_dur": 2.65,
        "start": 3.75
    },
    {
        "id": "s4",
        "text": "第一句话抛出‘为您预留了800元续保补贴’，",
        "target_dur": 2.40,
        "start": 6.50
    },
    {
        "id": "s5",
        "text": "一秒锁死客户注意力！",
        "target_dur": 1.45,
        "start": 9.05
    }
]

async def build_master_audio():
    print("=== 1. 生成各分句配音 (zh-CN-YunjianNeural, rate=+20%) ===")
    timed_files = []
    
    for seg in SEGMENTS:
        raw_mp3 = os.path.join(AUDIO_DIR, f"{seg['id']}_raw.mp3")
        trim_wav = os.path.join(AUDIO_DIR, f"{seg['id']}_trim.wav")
        timed_wav = os.path.join(AUDIO_DIR, f"{seg['id']}_timed.wav")
        
        comm = edge_tts.Communicate(seg["text"], "zh-CN-YunjianNeural", rate="+20%")
        await comm.save(raw_mp3)
        
        # 掐头去尾静音
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_mp3,
            "-af", "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse",
            trim_wav
        ], capture_output=True)
        
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", trim_wav
        ], capture_output=True, text=True)
        cur_dur = float(res.stdout.strip())
        
        tempo = cur_dur / seg["target_dur"]
        # atempo filter can only accept 0.5 to 2.0 per instance
        if tempo > 2.0:
            filter_str = f"atempo=2.0,atempo={tempo/2.0:.4f},aresample=44100"
        elif tempo < 0.5:
            filter_str = f"atempo=0.5,atempo={tempo/0.5:.4f},aresample=44100"
        else:
            filter_str = f"atempo={tempo:.4f},aresample=44100"
            
        subprocess.run([
            "ffmpeg", "-y", "-i", trim_wav,
            "-af", filter_str, timed_wav
        ], capture_output=True)
        
        res2 = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", timed_wav
        ], capture_output=True, text=True)
        actual_dur = float(res2.stdout.strip())
        print(f"[{seg['id']}] {seg['text'][:8]}...: 目标={seg['target_dur']:.2f}s | 实际={actual_dur:.2f}s | 启动时间={seg['start']:.2f}s")
        timed_files.append((timed_wav, seg["start"]))

    print("\n=== 2. 混音与音效融合 (Page Turn + Stamp Slam + Voice Master) ===")
    page_turn_sfx = os.path.join(SFX_DIR, "sfx_page_turn_翻书声.wav")
    stamp_slam_sfx = os.path.join(AUDIO_DIR, "sfx_stamp_slam.wav")
    
    # 构造 ffmpeg 混音滤镜链
    inputs = []
    # 0: page turn SFX
    inputs.extend(["-i", page_turn_sfx])
    # 1: stamp slam SFX
    inputs.extend(["-i", stamp_slam_sfx])
    
    # 2..6: voice segments
    for fpath, _ in timed_files:
        inputs.extend(["-i", fpath])
        
    filter_complex = []
    # Page turn starts at 0ms, volume 0.85
    filter_complex.append("[0:a]volume=0.85,adelay=0|0,aresample=44100[sfx_page]")
    # Stamp slam starts at 2500ms, volume 1.35
    filter_complex.append("[1:a]volume=1.35,adelay=2500|2500,aresample=44100[sfx_stamp]")
    
    track_labels = ["[sfx_page]", "[sfx_stamp]"]
    for idx, (_, start_sec) in enumerate(timed_files, start=2):
        delay_ms = int(round(start_sec * 1000))
        label = f"[v{idx}]"
        filter_complex.append(f"[{idx}:a]volume=1.05,adelay={delay_ms}|{delay_ms},aresample=44100{label}")
        track_labels.append(label)
        
    num_tracks = len(track_labels)
    filter_complex.append(f"{''.join(track_labels)}amix=inputs={num_tracks}:dropout_transition=0:normalize=0[mixed]")
    # 严格锁定 12.00 秒：使用 apad + atrim
    filter_complex.append("[mixed]apad=whole_dur=12.000,atrim=0:12.000,aresample=44100[out_audio]")
    
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", ";".join(filter_complex),
        "-map", "[out_audio]",
        "-c:a", "pcm_s16le",
        MASTER_OUT
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg 混音出错:", res.stderr)
        return False
        
    # 验证最终时长
    res_dur = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", MASTER_OUT
    ], capture_output=True, text=True)
    final_dur = float(res_dur.stdout.strip())
    print(f"\n混音完成！第四幕母带输出至: {MASTER_OUT}")
    print(f"最终母带时长: {final_dur:.6f} 秒 (严格锁定 12.000s)")
    return True

if __name__ == "__main__":
    asyncio.run(build_master_audio())
