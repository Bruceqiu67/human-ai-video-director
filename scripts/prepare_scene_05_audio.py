import os
import asyncio
import subprocess
import edge_tts

BASE_DIR = r"d:\video\视频3"
OUTPUT_AUDIO_DIR = os.path.join(BASE_DIR, "output", "audio")
os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)

VOICE_RAW_MP3 = os.path.join(OUTPUT_AUDIO_DIR, "scene5_voice_raw.mp3")
VOICE_RAW_WAV = os.path.join(OUTPUT_AUDIO_DIR, "scene5_voice_raw.wav")
SRT_FILE = os.path.join(OUTPUT_AUDIO_DIR, "scene5_voice.srt")

TEXT = "哪里卡壳，就一键“再练一次”，直到把金牌话术化作你的本能应变。现在就打开好帮手 APP，进入【话术私教】，开启你的销冠通关之旅吧！"
VOICE = "zh-CN-YunjianNeural"
RATE = "+20%"

async def generate():
    print(f"Generating TTS for Scene 05: voice={VOICE}, rate={RATE}...")
    communicate = edge_tts.Communicate(TEXT, VOICE, rate=RATE)
    submaker = edge_tts.SubMaker()
    
    with open(VOICE_RAW_MP3, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
                
    srt_content = submaker.get_srt()
    with open(SRT_FILE, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"Saved SRT to {SRT_FILE}")
    print("SRT Content:\n", srt_content)
    
    # Convert MP3 to WAV
    subprocess.run(["ffmpeg", "-y", "-i", VOICE_RAW_MP3, VOICE_RAW_WAV], check=True)
    
    # Probe duration
    dur_str = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", VOICE_RAW_WAV
    ]).decode().strip()
    raw_dur = float(dur_str)
    print(f"Raw voice duration: {raw_dur:.3f} seconds")

if __name__ == "__main__":
    asyncio.run(generate())
