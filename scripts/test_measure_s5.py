# -*- coding: utf-8 -*-
import asyncio, edge_tts, subprocess

lines = [
    ("s5_1", "哪里卡壳，就一键“再练一次”，"),
    ("s5_2", "直到把金牌话术化作你的本能应变。"),
    ("s5_3", "现在就打开好帮手 APP，"),
    ("s5_4", "进入【话术私教】，"),
    ("s5_5", "开启你的销冠通关之旅吧！")
]

async def test():
    for r in ["+15%", "+18%", "+20%"]:
        total = 0
        print(f"=== Testing rate={r} ===")
        for sid, text in lines:
            raw = f"output/audio/{sid}_{r}.mp3"
            trim = f"output/audio/{sid}_{r}_trim.wav"
            comm = edge_tts.Communicate(text, "zh-CN-YunjianNeural", rate=r)
            await comm.save(raw)
            subprocess.run([
                "ffmpeg", "-y", "-i", raw,
                "-af", "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse",
                trim
            ], capture_output=True)
            res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", trim], capture_output=True, text=True)
            dur = float(res.stdout.strip())
            total += dur
            print(f"  {sid}: {dur:.2f}s | chars={len(text)} | {text}")
        print(f"Total net speech ({r}): {total:.2f}s\n")

if __name__ == "__main__":
    asyncio.run(test())
