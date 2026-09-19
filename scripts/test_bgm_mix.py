import os
import subprocess

BASE_DIR = r"d:\video\视频3"
MASTER_VIDEO = os.path.join(BASE_DIR, "output", "video", "好帮手AI话术私教_终极宣传大片_1080P.mp4")
BGM_FILE = os.path.join(BASE_DIR, "BGM", "GD后台@2690286639@First Beat@K Koushik Singha.mp3")

# Extract 15s snippet (e.g. 10s to 25s, covering S1 end, flip, and S2 speech)
test_snippet = os.path.join(BASE_DIR, "output", "test_snippet_orig.wav")
subprocess.run([
    "ffmpeg", "-y", "-ss", "10", "-t", "15",
    "-i", MASTER_VIDEO,
    "-vn", "-c:a", "pcm_s16le", test_snippet
], check=True)

# Test mix at volume=0.15 (-16.5 dB)
out_mix_15 = os.path.join(BASE_DIR, "output", "test_mix_vol15.wav")
subprocess.run([
    "ffmpeg", "-y",
    "-i", test_snippet,
    "-ss", "10", "-t", "15", "-i", BGM_FILE,
    "-filter_complex", "[1:a]volume=0.15,aresample=44100[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]",
    "-map", "[aout]",
    "-c:a", "pcm_s16le", out_mix_15
], check=True)

# Test mix at volume=0.20 (-14 dB)
out_mix_20 = os.path.join(BASE_DIR, "output", "test_mix_vol20.wav")
subprocess.run([
    "ffmpeg", "-y",
    "-i", test_snippet,
    "-ss", "10", "-t", "15", "-i", BGM_FILE,
    "-filter_complex", "[1:a]volume=0.20,aresample=44100[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]",
    "-map", "[aout]",
    "-c:a", "pcm_s16le", out_mix_20
], check=True)

print("Test mixes created successfully!")
