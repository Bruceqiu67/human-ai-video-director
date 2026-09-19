import asyncio
import os
import subprocess
import edge_tts

BASE_DIR = r"d:\video\视频3"
AUDIO_DIR = os.path.join(BASE_DIR, "output", "audio")
SFX_DIR = os.path.join(BASE_DIR, "素材", "06_音效与音频资产")
MASTER_OUT = os.path.join(AUDIO_DIR, "scene2_v3_master_audio.wav")

os.makedirs(AUDIO_DIR, exist_ok=True)

SEGMENTS = [
    {
        "id": "s2_1",
        "part": "2A",
        "text": "别担心，只是你练少了！",
        "start": 0.40
    },
    {
        "id": "s2_2",
        "part": "2A",
        "text": "主管忙、没空教？",
        "start": 2.20
    },
    {
        "id": "s2_3",
        "part": "2B",
        "text": "好帮手 AI 学习助手重磅上线——话术私教！",
        "start": 4.10
    },
    {
        "id": "s2_4",
        "part": "2B",
        "text": "从开场白、报价到促成，24 关实战异议地图，",
        "start": 7.45
    },
    {
        "id": "s2_5",
        "part": "2B",
        "text": "随时随地像打游戏一样刷满肌肉记忆。",
        "start": 11.20
    }
]

async def build_master_audio():
    print("=== 1. 生成第二幕分句语音 (严格对齐第一幕：zh-CN-YunjianNeural, rate=+20%, 0 atempo) ===")
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
        print(f"[{seg['id']}] [{seg['part']}] {seg['text']}: 净时长={actual_dur:.2f}s | 启动时间={seg['start']:.2f}s | 结束={seg['start']+actual_dur:.2f}s")
        timed_files.append((timed_wav, seg["start"], actual_dur))

    target_total_dur = 14.200
    print(f"\n整幕标准规格总时长: {target_total_dur:.3f} 秒 (426 帧 @ 30fps)")

    print("\n=== 2. 混音与音效 (起始翻书声 + 3.8s二次翻书声 + 7.45s三次翻书声 + 8.5s解锁Ding响 + 纯正恒定人声) ===")
    page_turn_sfx = os.path.join(SFX_DIR, "sfx_page_turn_翻书声.wav")
    ding_sfx = os.path.join(SFX_DIR, "sfx_ding_解锁声.wav")
    
    # 0: page turn 1 (0.0s)
    # 1: page turn 2 (3.80s)
    # 2: page turn 3 (7.45s)
    # 3: ding (8.50s)
    # 4..8: voice segments
    inputs = [
        "-i", page_turn_sfx,
        "-i", page_turn_sfx,
        "-i", page_turn_sfx,
        "-i", ding_sfx
    ]
    
    for fpath, _, _ in timed_files:
        inputs.extend(["-i", fpath])
        
    filter_complex = []
    # 0.0s 翻入 2A 困境
    filter_complex.append("[0:a]volume=0.85,adelay=0|0,aresample=44100[sfx_page1]")
    # 3.80s 翻入 2B 重磅上线功能卡
    filter_complex.append("[1:a]volume=0.85,adelay=3800|3800,aresample=44100[sfx_page2]")
    # 7.45s 翻入 2C 异议地图
    filter_complex.append("[2:a]volume=0.85,adelay=7450|7450,aresample=44100[sfx_page3]")
    # 8.50s 划亮开场白与促成解锁声
    filter_complex.append("[3:a]volume=0.90,adelay=8500|8500,aresample=44100[sfx_ding]")
    
    track_labels = ["[sfx_page1]", "[sfx_page2]", "[sfx_page3]", "[sfx_ding]"]
    for idx, (_, start_sec, _) in enumerate(timed_files, start=4):
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
    print(f"\n混音完成！第二幕恒定自然语速全新母带输出至: {MASTER_OUT}")
    print(f"最终母带时长: {final_dur:.3f} 秒")

if __name__ == "__main__":
    asyncio.run(build_master_audio())
