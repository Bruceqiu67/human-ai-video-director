import asyncio
import os
import subprocess
import edge_tts

SEGMENTS = [
    {"id": "s2_1", "text": "别担心，只是你练少了！"},
    {"id": "s2_2", "text": "主管忙、没空教？"},
    {"id": "s2_3", "text": "好帮手 AI 学习助手重磅上线——话术私教！"},
    {"id": "s2_4", "text": "从开场白、报价到促成，24 关实战异议地图，"},
    {"id": "s2_5", "text": "随时随地像打游戏一样刷满肌肉记忆。"}
]

async def test_audio():
    os.makedirs("output/audio/scene2_segments", exist_ok=True)
    total_dur = 0.0
    for seg in SEGMENTS:
        mp3_path = f"output/audio/scene2_segments/{seg['id']}.mp3"
        wav_path = f"output/audio/scene2_segments/{seg['id']}.wav"
        comm = edge_tts.Communicate(seg['text'], "zh-CN-YunjianNeural", rate="+20%")
        await comm.save(mp3_path)
        subprocess.run([
            "ffmpeg", "-y", "-i", mp3_path,
            "-af", "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse",
            wav_path
        ], capture_output=True)
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", wav_path
        ], capture_output=True, text=True)
        dur = float(res.stdout.strip())
        print(f"[{seg['id']}] '{seg['text']}': 原生时长 = {dur:.3f}s")
        total_dur += dur
    print(f"纯语音净时长合计: {total_dur:.3f}s")

if __name__ == "__main__":
    asyncio.run(test_audio())
