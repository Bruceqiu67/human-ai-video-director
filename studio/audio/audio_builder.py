import os
import asyncio
import subprocess
from studio.core.config import StoryboardConfig
from studio.core.manifest import TimestampManifest
from studio.audio.tts_engine import TTSEngine
from studio.audio.silence_trimmer import SilenceTrimmer

class AudioBuilder:
    """Orchestrates scene master audio building, timing alignment, and manifest export."""
    
    def __init__(self, config: StoryboardConfig):
        self.config = config
        self.project_dir = config.project_dir
        self.audio_dir = os.path.join(self.project_dir, "audio")
        self.raw_dir = os.path.join(self.audio_dir, "raw_segments")
        os.makedirs(self.raw_dir, exist_ok=True)
        
        self.tts = TTSEngine(voice=config.voice, rate=config.rate)
        
    async def build_scene_audio(self, scene: dict) -> tuple[str, list, float]:
        scene_id = scene.get("id", "scene_01")
        timing = scene.get("timing", {})
        initial_delay = timing.get("initial_delay", 0.30)
        pause_between = timing.get("pause_between", 0.28)
        tail_pad = timing.get("tail_pad", 0.50)
        
        segments = scene.get("dialogue_segments", [])
        if not segments:
            raise ValueError(f"Scene {scene_id} has no dialogue_segments!")
            
        cur_time = initial_delay
        scene_manifest_segments = []
        inputs = []
        filter_complex = []
        track_labels = []
        
        for idx, seg in enumerate(segments):
            seg_id = seg.get("id", f"{scene_id}_{idx+1}")
            text = seg.get("text", "")
            raw_mp3 = os.path.join(self.raw_dir, f"{seg_id}_raw.mp3")
            trim_wav = os.path.join(self.raw_dir, f"{seg_id}_trim.wav")
            
            # Step 1: Synthesize
            await self.tts.synthesize(text, raw_mp3)
            
            # Step 2: Trim head/tail silence & get precise duration
            dur = SilenceTrimmer.trim_silence(raw_mp3, trim_wav)
            
            start_time = round(cur_time, 2)
            end_time = round(cur_time + dur, 2)
            
            scene_manifest_segments.append({
                "id": seg_id,
                "text": text,
                "start": start_time,
                "end": end_time,
                "duration": round(dur, 2),
                "pose": seg.get("pose", ""),
                "fx": seg.get("fx", [])
            })
            
            inputs.extend(["-i", trim_wav])
            delay_ms = int(round(start_time * 1000))
            lbl = f"[v{idx}]"
            filter_complex.append(f"[{idx}:a]aresample=44100,adelay={delay_ms}|{delay_ms}{lbl}")
            track_labels.append(lbl)
            
            cur_time = end_time + pause_between
            
        scene_total_dur = round(cur_time + tail_pad, 2)
        scene_master_wav = os.path.join(self.audio_dir, f"{scene_id}_master.wav")
        
        # Mix tracks with adelay and brickwall peak limiter
        filter_str = (
            ";".join(filter_complex) + 
            f";{''.join(track_labels)}amix=inputs={len(track_labels)}:dropout_transition=0,volume=2.0dB,alimiter=limit=0.98[outa]"
        )
        
        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", filter_str,
            "-map", "[outa]",
            "-t", str(scene_total_dur),
            scene_master_wav
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        actual_dur = SilenceTrimmer.get_duration(scene_master_wav)
        
        return scene_master_wav, scene_manifest_segments, actual_dur
        
    async def build_all(self) -> TimestampManifest:
        manifest_path = os.path.join(self.audio_dir, "timestamps_manifest.json")
        manifest = TimestampManifest({}, manifest_path)
        
        for sc in self.config.scenes:
            scene_id = sc.get("id", "")
            print(f"Building audio for {scene_id} ({sc.get('stage_tag', '')})...")
            master_wav, segments, total_dur = await self.build_scene_audio(sc)
            manifest.set_scene_segments(scene_id, segments, total_dur)
            print(f"  -> {scene_id} master generated: {total_dur:.2f}s, {len(segments)} segments.")
            
        manifest.save()
        print(f"Manifest saved to: {manifest_path}")
        return manifest
