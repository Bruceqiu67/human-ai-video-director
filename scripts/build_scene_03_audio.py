import asyncio
import os
import subprocess
import edge_tts

BASE_DIR = r"d:\video\视频3"
AUDIO_DIR = os.path.join(BASE_DIR, "output", "audio")
SFX_DIR = os.path.join(BASE_DIR, "素材", "06_音效与音频资产")
MASTER_OUT = os.path.join(AUDIO_DIR, "scene3_v3_master_audio.wav")

os.makedirs(AUDIO_DIR, exist_ok=True)

SEGMENTS = [
    {
        "id": "s3_1",
        "text": "点击挑战，你的对手比真实客户更挑剔！",
        "start": 0.50
    },
    {
        "id": "s3_2",
        "text": "AI 瞬间化身各种刁钻性格的客户，逼真模拟高压通话。",
        "start": 3.60
    },
    {
        "id": "s3_3",
        "text": "在零风险的安全屋里，",
        "start": 7.80
    },
    {
        "id": "s3_4",
        "text": "把所有怯场和大脑空白，在正式开单前全部排雷！",
        "start": 9.50
    }
]

async def build_master_audio():
    print("=== 1. 生成第三幕分句语音 (zh-CN-YunjianNeural, rate=+20%, 0 atempo) ===")
    timed_files = []
    
    for seg in SEGMENTS:
        raw_mp3 = os.path.join(AUDIO_DIR, f"{seg['id']}_raw.mp3")
        trim_wav = os.path.join(AUDIO_DIR, f"{seg['id']}_trim.wav")
        timed_wav = os.path.join(AUDIO_DIR, f"{seg['id']}_timed.wav")
        
        comm = edge_tts.Communicate(seg["text"], "zh-CN-YunjianNeural", rate="+20%")
        await comm.save(raw_mp3)
        
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_mp3,
            "-af", "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse",
            trim_wav
        ], capture_output=True)
        
        subprocess.run([
            "ffmpeg", "-y", "-i", trim_wav,
            "-af", "aresample=44100", timed_wav
        ], capture_output=True)
        
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", timed_wav
        ], capture_output=True, text=True)
        actual_dur = float(res.stdout.strip())
        print(f"[{seg['id']}] {seg['text']}: 净时长={actual_dur:.2f}s | 启动时间={seg['start']:.2f}s | 结束={seg['start']+actual_dur:.2f}s")
        timed_files.append((timed_wav, seg["start"], actual_dur))

    target_total_dur = 13.800
    print(f"\n整幕标准规格总时长: {target_total_dur:.3f} 秒 (414 帧 @ 30fps)")

    print("\n=== 2. 混音与音效 (起始翻书声 + 纯正恒定人声母带) ===")
    page_turn_sfx = os.path.join(SFX_DIR, "sfx_page_turn_翻书声.wav")
    ding_sfx = os.path.join(SFX_DIR, "sfx_ding_解锁声.wav")
    
    # 0: page turn
    # 1: ding
    # 2..5: voice segments
    inputs = [
        "-i", page_turn_sfx,
        "-i", ding_sfx
    ]
    
    for fpath, _, _ in timed_files:
        inputs.extend(["-i", fpath])
        
    filter_complex = []
    # 0.0s 翻入 Scene 03
    filter_complex.append("[0:a]volume=0.85,adelay=0|0,aresample=44100[sfx_page]")
    # 0.9s 点击挑战轻快叮响
    filter_complex.append("[1:a]volume=0.50,adelay=900|900,aresample=44100[sfx_click]")
    
    track_labels = ["[sfx_page]", "[sfx_click]"]
    for idx, (_, start_sec, _) in enumerate(timed_files, start=2):
        delay_ms = int(round(start_sec * 1000))
        label = f"[v{idx}]"
        filter_complex.append(f"[{idx}:a]volume=1.05,adelay={delay_ms}|{delay_ms},aresample=44100{label}")
        track_labels.append(label)
        
    num_tracks = len(track_labels)
    filter_complex.append(f"{''.join(track_labels)}amix=inputs={num_tracks}:dropout_transition=0:normalize=0[mixed]")
    filter_complex.append(f"[mixed]apad=whole_dur={target_total_dur},atrim=0:{target_total_dur},aresample=44100[out_audio]")
    
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", ";".join(filter_complex),
        "-map", "[out_audio]",
        "-c:a", "pcm_s16le",
        MASTER_OUT
    ]
    
    subprocess.run(cmd, check=True)
        
    res_dur = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", MASTER_OUT
    ], capture_output=True, text=True)
    final_dur = float(res_dur.stdout.strip())
    print(f"\n混音完成！第三幕恒定自然语速全新母带输出至: {MASTER_OUT}")
    print(f"最终母带时长: {final_dur:.3f} 秒")

if __name__ == "__main__":
    asyncio.run(build_master_audio())
