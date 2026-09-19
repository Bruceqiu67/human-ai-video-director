import os
import asyncio
import subprocess
import edge_tts

BASE_DIR = r"d:\video\视频3"
OUTPUT_AUDIO_DIR = os.path.join(BASE_DIR, "output", "audio")
os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)

VOICE_RAW_MP3 = os.path.join(OUTPUT_AUDIO_DIR, "scene5_voice_raw.mp3")
VOICE_CLEAN_WAV = os.path.join(OUTPUT_AUDIO_DIR, "scene5_voice_clean.wav")
VTT_FILE = os.path.join(OUTPUT_AUDIO_DIR, "scene5_voice.vtt")
MASTER_AUDIO_WAV = os.path.join(OUTPUT_AUDIO_DIR, "scene5_master_audio.wav")

TEXT = "哪里卡壳，就一键“再练一次”，直到把金牌话术化作你的本能应变。现在就打开好帮手 APP，进入【话术私教】，开启你的销冠通关之旅吧！"
VOICE = "zh-CN-YunjianNeural"
RATE = "+18%"

async def generate_tts():
    print(f"Generating TTS for Scene 05 with voice={VOICE}, rate={RATE}...")
    communicate = edge_tts.Communicate(TEXT, VOICE, rate=RATE)
    submaker = edge_tts.SubMaker()
    with open(VOICE_RAW_MP3, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)
    with open(VTT_FILE.replace(".vtt", ".srt"), "w", encoding="utf-8") as f:
        f.write(submaker.get_srt())
    print(f"Saved raw voice: {VOICE_RAW_MP3}")
    print(f"Saved subtitles: {VTT_FILE}")

if __name__ == "__main__":
    asyncio.run(generate_tts())
