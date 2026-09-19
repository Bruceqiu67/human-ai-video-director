import os
import subprocess

class SilenceTrimmer:
    """Uses FFmpeg to accurately trim head and tail silence and probe duration."""
    
    @staticmethod
    def trim_silence(input_path: str, output_path: str, threshold_db: float = -45.0) -> float:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        # Double-pass reverse silence removal to cut both head and tail
        af_filter = (
            f"silenceremove=start_periods=1:start_duration=0.01:start_threshold={threshold_db}dB,"
            f"areverse,silenceremove=start_periods=1:start_duration=0.01:start_threshold={threshold_db}dB,areverse"
        )
        
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-af", af_filter,
            output_path
        ]
        res = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace"
        )
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg trim failed: {res.stderr}")
            
        return SilenceTrimmer.get_duration(output_path)
        
    @staticmethod
    def get_duration(audio_path: str) -> float:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path
        ]
        res = subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        return float(res.stdout.strip())
