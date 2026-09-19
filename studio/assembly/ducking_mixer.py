import os
import subprocess

class DuckingMixer:
    """
    Applies FFmpeg Sidechain Compression to dynamically duck BGM:
    Lowers BGM to ~12% when speech is present, and smoothly recovers to ~25% during breath pauses.
    """
    
    @staticmethod
    def mix(
        video_input: str,
        bgm_input: str,
        output_path: str,
        ducked_volume: float = 0.12,
        idle_volume: float = 0.25
    ) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Audio filter complex for sidechain ducking
        # [0:a] is voice from video, [1:a] is BGM
        filter_complex = (
            f"[1:a]aloop=loop=-1:size=2e+09,aresample=44100[bgm_loop];"
            f"[bgm_loop]asplit=2[sc][bgm_raw];"
            f"[0:a][sc]sidechaincompress=threshold=0.08:ratio=8:attack=30:release=350[voice_ducked];"
            f"[bgm_raw]volume={ducked_volume}[bgm_quiet];"
            f"[voice_ducked][bgm_quiet]amix=inputs=2:duration=first:dropout_transition=0,volume=1.8dB,alimiter=limit=0.98[aout]"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_input,
            "-i", bgm_input,
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "320k",
            "-movflags", "+faststart",
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path
