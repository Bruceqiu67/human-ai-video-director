import os
import subprocess

BASE_DIR = r"d:\video\视频3"
OUTPUT_AUDIO_DIR = os.path.join(BASE_DIR, "output", "audio")
VOICE_SPEED_WAV = os.path.join(OUTPUT_AUDIO_DIR, "scene5_voice_speed.wav")
MASTER_WAV = os.path.join(OUTPUT_AUDIO_DIR, "scene5_master_audio.wav")

PAGE_TURN_SFX = os.path.join(BASE_DIR, "素材", "06_音效与音频资产", "sfx_page_turn_翻书声.wav")
DING_SFX = os.path.join(BASE_DIR, "素材", "06_音效与音频资产", "sfx_ding_解锁声.wav")

def mix_audio():
    print("Synthesizing Master Audio for Scene 05 (strict 10.00s)...")
    
    # Filter complex:
    # 0: Voice delayed by 650ms
    # 1: Page turn at 0ms
    # 2: Ding SFX at 5250ms (when App icon bounces out)
    # amix together and pad with apad to exact 10.000s
    filter_complex = (
        "[0:a]adelay=650|650,volume=1.0[v];"
        "[1:a]volume=0.85[sfx1];"
        "[2:a]adelay=5250|5250,volume=0.80[sfx2];"
        "[v][sfx1][sfx2]amix=inputs=3:duration=longest:dropout_transition=0[mix];"
        "[mix]apad=whole_dur=10.000,atrim=0:10.000[out]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", VOICE_SPEED_WAV,
        "-i", PAGE_TURN_SFX,
        "-i", DING_SFX,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "pcm_s16le",
        "-ar", "44100",
        "-ac", "1",
        MASTER_WAV
    ]
    
    subprocess.run(cmd, check=True)
    
    # Verify duration
    dur_str = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", MASTER_WAV
    ]).decode().strip()
    print(f"Master Audio created: {MASTER_WAV}")
    print(f"Verified Duration: {float(dur_str):.6f} seconds")

if __name__ == "__main__":
    mix_audio()
