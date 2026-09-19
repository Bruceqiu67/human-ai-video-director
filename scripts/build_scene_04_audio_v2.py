import asyncio
import os
import subprocess
import edge_tts

BASE_DIR = r"d:\video\视频3"
AUDIO_DIR = os.path.join(BASE_DIR, "output", "audio")
SFX_DIR = os.path.join(BASE_DIR, "素材", "06_音效与音频资产")
MASTER_OUT = os.path.join(AUDIO_DIR, "scene4_v2_master_audio.wav")

os.makedirs(AUDIO_DIR, exist_ok=True)

# 7 段科学细分台词 (zh-CN-YunjianNeural, rate=+20%, 0% atempo)
# 自然呼吸气口合理分布，全幕标准时长精准锁定 17.000 秒
SEGMENTS = [
    {
        "id": "s4_1",
        "text": "一通练完，AI立刻输出深度体检单！",
        "start": 0.50
    },
    {
        "id": "s4_2",
        "text": "第一次只有45分？",
        "start": 3.50
    },
    {
        "id": "s4_3",
        "text": "别慌，它给的可不是泛泛的加油，",
        "start": 5.10
    },
    {
        "id": "s4_4",
        "text": "而是指骨到肉的解法：",
        "start": 7.45
    },
    {
        "id": "s4_5",
        "text": "开场白太冗长？直接教你‘利益前置’——",
        "start": 9.10
    },
    {
        "id": "s4_6",
        "text": "第一句话抛出‘为您预留了800元续保补贴’，",
        "start": 12.40
    },
    {
        "id": "s4_7",
        "text": "一秒锁死客户注意力！",
        "start": 15.20
    }
]

async def build_master_audio():
    print("=== 1. 生成第四幕分句语音 (zh-CN-YunjianNeural, rate=+20%, 0% atempo) ===")
    timed_files = []
    
    for seg in SEGMENTS:
        raw_mp3 = os.path.join(AUDIO_DIR, f"{seg['id']}_raw.mp3")
        trim_wav = os.path.join(AUDIO_DIR, f"{seg['id']}_trim.wav")
        timed_wav = os.path.join(AUDIO_DIR, f"{seg['id']}_timed.wav")
        
        comm = edge_tts.Communicate(seg["text"], "zh-CN-YunjianNeural", rate="+20%")
        await comm.save(raw_mp3)
        
        # 掐头去尾精准消音
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_mp3,
            "-af", "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse",
            trim_wav
        ], capture_output=True, check=True)
        
        # 44.1kHz 重采样
        subprocess.run([
            "ffmpeg", "-y", "-i", trim_wav,
            "-af", "aresample=44100", timed_wav
        ], capture_output=True, check=True)
        
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", timed_wav
        ], capture_output=True, text=True)
        actual_dur = float(res.stdout.strip())
        print(f"[{seg['id']}] {seg['text']}: 净时长={actual_dur:.2f}s | 启动时间={seg['start']:.2f}s | 结束={seg['start']+actual_dur:.2f}s")
        timed_files.append((timed_wav, seg["start"], actual_dur))

    target_total_dur = 17.000
    print(f"\n整幕标准规格总时长: {target_total_dur:.3f} 秒 (510 帧 @ 30fps)")

    print("\n=== 2. 混音与音效 (起始翻书声 + 3.55s 盖印重砸声 + 7段纯正人声母带) ===")
    page_turn_sfx = os.path.join(SFX_DIR, "sfx_page_turn_翻书声.wav")
    stamp_slam_sfx = os.path.join(AUDIO_DIR, "sfx_stamp_slam.wav")
    
    # 0: page turn
    # 1: stamp slam
    # 2..8: voice segments
    inputs = [
        "-i", page_turn_sfx,
        "-i", stamp_slam_sfx
    ]
    
    for fpath, _, _ in timed_files:
        inputs.extend(["-i", fpath])
        
    filter_complex = []
    # 0.0s 翻入 Scene 04
    filter_complex.append("[0:a]volume=0.85,adelay=0|0,aresample=44100[sfx_page]")
    # 3.55s 念到“45分”时印章砸落重响
    filter_complex.append("[1:a]volume=1.35,adelay=3550|3550,aresample=44100[sfx_stamp]")
    
    track_labels = ["[sfx_page]", "[sfx_stamp]"]
    for idx, (_, start_sec, _) in enumerate(timed_files, start=2):
        delay_ms = int(round(start_sec * 1000))
        label = f"[v{idx}]"
        filter_complex.append(f"[{idx}:a]volume=1.05,adelay={delay_ms}|{delay_ms},aresample=44100{label}")
        track_labels.append(label)
        
    num_tracks = len(track_labels)
    filter_complex.append(f"{''.join(track_labels)}amix=inputs={num_tracks}:dropout_transition=0:normalize=0[mixed]")
    # 严格锁定 17.000 秒
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
    print(f"\n混音完成！第四幕全新母带输出至: {MASTER_OUT}")
    print(f"最终母带时长: {final_dur:.3f} 秒 (严格锁定 17.000s)")

if __name__ == "__main__":
    asyncio.run(build_master_audio())
