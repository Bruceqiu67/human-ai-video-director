import asyncio
import os
import subprocess
import edge_tts

BASE_DIR = r"d:\video\视频3"
AUDIO_DIR = os.path.join(BASE_DIR, "output", "audio")
SFX_DIR = os.path.join(BASE_DIR, "素材", "06_音效与音频资产")
MASTER_OUT = os.path.join(AUDIO_DIR, "scene1_v3_master_audio.wav")

os.makedirs(AUDIO_DIR, exist_ok=True)

SEGMENTS = [
    {
        "id": "s1_1",
        "text": "刚开口，就被客户秒挂；",
        "start": 0.30
    },
    {
        "id": "s1_2",
        "text": "面对客户的‘现在忙、不需要’，大脑一片空白不知如何回复。",
        "start": 2.45
    },
    {
        "id": "s1_3",
        "text": "新人缺乏异议经验，根本留不住客户，",
        "start": 7.30
    },
    {
        "id": "s1_4",
        "text": "最后导致开单率怎么也上不去。",
        "start": 9.95
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
        
        # 100% 保持 Edge-TTS 原生自然恒定语速，严禁逐句忽快忽慢变速！
        # 直接重采样为 44100Hz 标准音频
        subprocess.run([
            "ffmpeg", "-y", "-i", trim_wav,
            "-af", "aresample=44100", timed_wav
        ], capture_output=True)
        
        res2 = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", timed_wav
        ], capture_output=True, text=True)
        actual_dur = float(res2.stdout.strip())
        print(f"[{seg['id']}] {seg['text'][:12]}...: 原生自然时长={actual_dur:.2f}s | 启动时间={seg['start']:.2f}s")
        timed_files.append((timed_wav, seg["start"], actual_dur))

    print("\n=== 2. 混音与音效融合 (挂机忙音 + 翻书声 + 纯正人声母带) ===")
    beep_sfx = os.path.join(SFX_DIR, "sfx_beep_挂机忙音.wav")
    page_turn_sfx = os.path.join(SFX_DIR, "sfx_page_turn_翻书声.wav")
    
    # 构造 ffmpeg 混音滤镜链
    inputs = []
    # 0: beep SFX
    inputs.extend(["-i", beep_sfx])
    # 1: page turn SFX
    inputs.extend(["-i", page_turn_sfx])
    
    # 2..5: voice segments
    for fpath, _, _ in timed_files:
        inputs.extend(["-i", fpath])
        
    filter_complex = []
    # 挂机忙音在 2.25s 响起，音量 1.05
    filter_complex.append("[0:a]volume=1.05,adelay=2250|2250,aresample=44100[sfx_beep]")
    # 翻书声在 6.60s 响起，音量 0.90
    filter_complex.append("[1:a]volume=0.90,adelay=6600|6600,aresample=44100[sfx_page]")
    
    track_labels = ["[sfx_beep]", "[sfx_page]"]
    for idx, (_, start_sec, _) in enumerate(timed_files, start=2):
        delay_ms = int(round(start_sec * 1000))
        label = f"[v{idx}]"
        filter_complex.append(f"[{idx}:a]volume=1.05,adelay={delay_ms}|{delay_ms},aresample=44100{label}")
        track_labels.append(label)
        
    num_tracks = len(track_labels)
    filter_complex.append(f"{''.join(track_labels)}amix=inputs={num_tracks}:dropout_transition=0:normalize=0[mixed]")
    # 严格锁定 12.000 秒 (360 帧) 标准商业规格
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
    print(f"\n混音完成！第一幕终极恒定自然语速母带输出至: {MASTER_OUT}")
    print(f"最终母带时长: {final_dur:.6f} 秒 (严格锁定 12.000s / 360帧)")
    return True

if __name__ == "__main__":
    asyncio.run(build_master_audio())
