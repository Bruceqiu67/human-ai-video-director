import os
import subprocess

class SceneConcatenator:
    """Losslessly concatenates rendered scene MP4 files using FFmpeg Concat Demuxer."""
    
    @staticmethod
    def concat(scene_mp4_paths: list[str], output_path: str) -> str:
        if not scene_mp4_paths:
            raise ValueError("No scene MP4 files provided for concatenation.")
            
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        concat_txt = os.path.join(os.path.dirname(output_path), "concat_list.tmp.txt")
        
        with open(concat_txt, "w", encoding="utf-8") as f:
            for p in scene_mp4_paths:
                # Format for FFmpeg concat demuxer
                escaped_path = os.path.abspath(p).replace("\\", "/")
                f.write(f"file '{escaped_path}'\n")
                
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_txt,
            "-c", "copy",
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        if os.path.exists(concat_txt):
            os.remove(concat_txt)
            
        return output_path
