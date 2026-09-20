"""Build per-scene master WAVs and the timestamp manifest."""

from __future__ import annotations

import os

from studio.audio.silence_trimmer import SilenceTrimmer
from studio.audio.tts_engine import TTSEngine
from studio.core.config import StoryboardConfig
from studio.core.manifest import TimestampManifest
from studio.core.proc import require_ffmpeg, run_command


class AudioBuilder:
    """Orchestrates scene master audio building, timing alignment, and manifest export."""

    def __init__(self, config: StoryboardConfig):
        self.config = config
        self.project_dir = config.project_dir
        self.audio_dir = os.path.join(self.project_dir, "audio")
        self.raw_dir = os.path.join(self.audio_dir, "raw_segments")
        os.makedirs(self.raw_dir, exist_ok=True)
        self.tts = TTSEngine(voice=config.voice, rate=config.rate)

    @staticmethod
    def build_mix_filter(delays_ms: list[int], tail_pad: float) -> str:
        """adelay each clip, amix without 1/N attenuation, then pad the tail."""
        if not delays_ms:
            raise ValueError("No audio delays provided.")
        parts: list[str] = []
        labels: list[str] = []
        for idx, delay in enumerate(delays_ms):
            lbl = f"[v{idx}]"
            parts.append(f"[{idx}:a]aresample=44100,adelay={delay}|{delay}{lbl}")
            labels.append(lbl)
        pad = f"apad=pad_dur={tail_pad:.3f}" if tail_pad > 0 else "anull"
        n_tracks = len(labels)
        if n_tracks == 1:
            mix = f"{labels[0]}volume=2.0dB,{pad},alimiter=limit=0.98[outa]"
        else:
            joined = "".join(labels)
            mix = (
                f"{joined}amix=inputs={n_tracks}:dropout_transition=0:normalize=0,"
                f"volume=2.0dB,{pad},alimiter=limit=0.98[outa]"
            )
        return ";".join(parts + [mix])

    async def build_scene_audio(self, scene: dict) -> tuple[str, list, float]:
        scene_id = scene.get("id") or ""
        if not scene_id:
            raise ValueError("Every scene must have a non-empty id.")
        timing = scene.get("timing", {}) or {}
        initial_delay = float(timing.get("initial_delay", 0.30))
        pause_between = float(timing.get("pause_between", 0.28))
        tail_pad = float(timing.get("tail_pad", 0.50))

        segments = scene.get("dialogue_segments") or []
        if not segments:
            raise ValueError(f"Scene {scene_id} has no dialogue_segments!")

        cur_time = initial_delay
        scene_manifest_segments: list[dict] = []
        inputs: list[str] = []
        delays_ms: list[int] = []

        for idx, seg in enumerate(segments):
            seg_id = seg.get("id") or f"{scene_id}_{idx + 1}"
            text = (seg.get("text") or "").strip()
            if not text:
                raise ValueError(f"Scene {scene_id} segment {seg_id} has empty text.")
            raw_mp3 = os.path.join(self.raw_dir, f"{seg_id}_raw.mp3")
            trim_wav = os.path.join(self.raw_dir, f"{seg_id}_trim.wav")

            await self.tts.synthesize(text, raw_mp3)
            dur = SilenceTrimmer.trim_silence(raw_mp3, trim_wav)
            if dur < 0.05:
                raise RuntimeError(f"Trimmed audio for {seg_id} is too short ({dur:.3f}s).")

            start_time = round(cur_time, 2)
            end_time = round(cur_time + dur, 2)
            scene_manifest_segments.append({
                "id": seg_id,
                "text": text,
                "start": start_time,
                "end": end_time,
                "duration": round(dur, 2),
                "pose": seg.get("pose", ""),
                "fx": seg.get("fx", []) or [],
            })
            inputs.extend(["-i", trim_wav])
            delays_ms.append(int(round(start_time * 1000)))
            if idx < len(segments) - 1:
                cur_time = end_time + pause_between
            else:
                cur_time = end_time

        scene_total_dur = round(cur_time + tail_pad, 2)
        scene_master_wav = os.path.join(self.audio_dir, f"{scene_id}_master.wav")
        filter_str = self.build_mix_filter(delays_ms, tail_pad)
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + inputs + [
            "-filter_complex", filter_str,
            "-map", "[outa]",
            "-t", str(scene_total_dur),
            scene_master_wav,
        ]
        run_command(cmd)
        actual_dur = SilenceTrimmer.get_duration(scene_master_wav)
        if actual_dur + 0.08 < scene_total_dur:
            raise RuntimeError(
                f"Master audio for {scene_id} is {actual_dur:.3f}s, "
                f"expected at least {scene_total_dur:.3f}s (tail_pad missing?)."
            )
        return scene_master_wav, scene_manifest_segments, scene_total_dur

    async def build_all(self, scene_id: str | None = None) -> TimestampManifest:
        require_ffmpeg()
        manifest_path = os.path.join(self.audio_dir, "timestamps_manifest.json")
        if scene_id:
            manifest = TimestampManifest.load(manifest_path)
            sc = self.config.get_scene(scene_id)
            if not sc:
                raise ValueError(f"Scene {scene_id} not found in storyboard.")
            scenes = [sc]
        else:
            manifest = TimestampManifest({}, manifest_path)
            scenes = list(self.config.scenes)

        for sc in scenes:
            sid = sc.get("id", "")
            print(f"Building audio for {sid} ({sc.get('stage_tag', '')})...")
            _master_wav, segments, total_dur = await self.build_scene_audio(sc)
            manifest.set_scene_segments(sid, segments, total_dur)
            manifest.save()
            print(f"  -> {sid} master generated: {total_dur:.2f}s, {len(segments)} segments.")

        print(f"Manifest saved to: {manifest_path}")
        return manifest
