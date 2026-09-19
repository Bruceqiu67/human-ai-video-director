import asyncio
import subprocess
import edge_tts

SEGMENTS = [
    {"id": "s3_1", "text": "点击挑战，你的对手比真实客户更挑剔！"},
    {"id": "s3_2", "text": "AI 瞬间化身各种刁钻性格的客户，逼真模拟高压通话。"},
    {"id": "s3_3", "text": "在零风险的安全屋里，"},
    {"id": "s3_4", "text": "把所有怯场和大脑空白，在正式开单前全部排雷！"}
]

async def measure():
    total_dur = 0.0
    for seg in SEGMENTS:
        mp3_path = f"output/audio/{seg['id']}_test.mp3"
        comm = edge_tts.Communicate(seg['text'], "zh-CN-YunjianNeural", rate="+20%")
        await comm.save(mp3_path)
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", mp3_path
        ], capture_output=True, text=True)
        dur = float(res.stdout.strip())
        print(f"[{seg['id']}] '{seg['text']}': 净时长 = {dur:.2f}s")
        total_dur += dur
    print(f"纯语音净时长合计: {total_dur:.2f}s")

if __name__ == "__main__":
    asyncio.run(measure())
