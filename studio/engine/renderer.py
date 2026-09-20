"""Per-scene stop-motion renderer with FX, captions, and QA frames."""

from __future__ import annotations

import math
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

from studio.core.config import StoryboardConfig
from studio.core.manifest import TimestampManifest
from studio.core.proc import require_ffmpeg
from studio.engine.assets import (
    list_scene_masterframes,
    match_pose_filename,
    unique_pose_index,
)
from studio.engine.camera import CameraDirector, KenBurnsZoom
from studio.engine.fx.marker import MarkerFX
from studio.engine.fx.pulse import PulseFX
from studio.engine.fx.stamp import StampFX
from studio.engine.fx.waveform import WaveformFX
from studio.engine.stopmotion import StopMotionSequencer
from studio.engine.subtitles import AdaptiveCapsuleSubtitle
from studio.engine.transitions import PageFlipTransition
from studio.styles import get_style

KNOWN_FX = {
    "highlighter_sweep",
    "click_pulse",
    "waveform_equalizer",
    "stamp_impact",
    "score_stamp_impact",
    "warning_badge_shake",
    "gold_light_sweep",
    "camera_push",
}


class SceneRenderer:
    """Transitions -> Stop-Motion -> FX -> KenBurns -> Adaptive Subtitles."""

    def __init__(self, config: StoryboardConfig, manifest: TimestampManifest | None = None):
        self.config = config
        self.project_dir = config.project_dir
        self.style = get_style(config.style_preset)
        self.fps = config.fps
        self.res = config.resolution
        width, height = self.res
        if width % 2 or height % 2:
            raise ValueError(f"Resolution {width}x{height} must be even for yuv420p.")

        manifest_path = os.path.join(self.project_dir, "audio", "timestamps_manifest.json")
        self.manifest = manifest or TimestampManifest.load(manifest_path)

        self.assets_dir = os.path.join(self.project_dir, "assets")
        self.masterframes_dir = os.path.join(self.assets_dir, "masterframes")
        self.anchors_dir = os.path.join(self.assets_dir, "anchors")
        self.output_video_dir = os.path.join(self.project_dir, "output", "video")
        self.qa_dir = os.path.join(self.project_dir, "output", "qa_frames")
        os.makedirs(self.anchors_dir, exist_ok=True)
        os.makedirs(self.output_video_dir, exist_ok=True)
        os.makedirs(self.qa_dir, exist_ok=True)

        max_width, _y = self.style.subtitle_layout(self.res)
        self.subtitle_y = self.style.subtitle_layout(self.res)[1]
        self.subtitle_engine = AdaptiveCapsuleSubtitle(
            default_font_size=self.style.subtitle_font_size,
            max_width=max_width,
            fill=self.style.subtitle_bg,
            text_fill=self.style.subtitle_text,
        )
        self._stamp_cache: dict[str, Image.Image] = {}

    def _search_dirs(self) -> list[str]:
        return [
            self.masterframes_dir,
            os.path.join(self.project_dir, "素材", "04_分幕原生画卷"),
        ]

    def _load_pose_images(self, scene_id: str, segments: list) -> tuple[dict, Image.Image]:
        paths = list_scene_masterframes(self._search_dirs(), scene_id)
        if not paths:
            searched = ", ".join(self._search_dirs())
            raise FileNotFoundError(
                f"No masterframe images found for {scene_id}. "
                f"Put pose files in assets/masterframes/. Searched: {searched}"
            )

        loaded: list[tuple[str, Image.Image]] = []
        by_name: dict[str, Image.Image] = {}
        for path in paths:
            try:
                img = Image.open(path).convert("RGBA").resize(self.res, Image.Resampling.LANCZOS)
            except Exception as exc:
                print(f"Warning: Could not open {path}: {exc}")
                continue
            fname = os.path.basename(path)
            loaded.append((fname, img))
            by_name[fname] = img

        if not loaded:
            raise FileNotFoundError(f"Masterframes for {scene_id} exist but none could be decoded.")

        filenames = [name for name, _img in loaded]
        pose_map: dict[str, Image.Image] = {}
        unmatched: list[str] = []
        for idx, seg in enumerate(segments):
            pose_name = (seg.get("pose") or "").strip()
            pose_idx = unique_pose_index(segments, pose_name, idx)
            chosen = match_pose_filename(pose_name, pose_idx, filenames)
            if chosen is None:
                unmatched.append(pose_name or seg.get("id", f"seg{idx}"))
                continue
            img = by_name[chosen]
            if pose_name:
                pose_map[pose_name] = img
            if seg.get("id"):
                pose_map[seg["id"]] = img

        if unmatched:
            raise FileNotFoundError(
                f"Could not match masterframes for {scene_id} poses: {unmatched}. "
                "Name files with the pose string or pose_1, pose_2, ..."
            )
        default_img = loaded[0][1]
        if segments:
            first_pose = (segments[0].get("pose") or "").strip()
            default_img = pose_map.get(first_pose) or pose_map.get(segments[0].get("id", ""), default_img)
        return pose_map, default_img

    def _scale_xy(self, x: int, y: int) -> tuple[int, int]:
        sx = self.res[0] / 1080
        sy = self.res[1] / 1920
        return int(x * sx), int(y * sy)

    def _scale_box(self, box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        x1, y1 = self._scale_xy(box[0], box[1])
        x2, y2 = self._scale_xy(box[2], box[3])
        return x1, y1, x2, y2

    def _find_stamp_image(self, score: bool) -> Image.Image:
        key = "score" if score else "pass"
        if key in self._stamp_cache:
            return self._stamp_cache[key]
        roots = [
            os.path.join(self.assets_dir, "stamps"),
            os.path.join(self.assets_dir, "fx"),
            os.path.join(self.project_dir, "素材", "05_分层动画切片"),
        ]
        hits: list[str] = []
        for root in roots:
            if not os.path.isdir(root):
                continue
            for fname in os.listdir(root):
                lower = fname.lower()
                if not lower.endswith((".png", ".webp")):
                    continue
                if "stamp" in lower or "印" in fname:
                    hits.append(os.path.join(root, fname))
        chosen = None
        if score:
            for path in hits:
                if "45" in os.path.basename(path):
                    chosen = path
                    break
        if chosen is None and hits:
            chosen = sorted(hits)[0]
        if chosen:
            img = Image.open(chosen).convert("RGBA")
        else:
            img = self._make_stamp("45" if score else "PASS")
        self._stamp_cache[key] = img
        return img

    def _make_stamp(self, text: str) -> Image.Image:
        img = Image.new("RGBA", (280, 280), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        color = (*self.style.stamp_color, 210)
        draw.ellipse([12, 12, 268, 268], outline=color, width=14)
        draw.ellipse([28, 28, 252, 252], outline=color, width=3)
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 64)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((280 - tw) / 2, (280 - th) / 2 - 8), text, font=font, fill=color)
        return img

    def _apply_warning_badge(self, canvas: Image.Image, t: float) -> Image.Image:
        canvas = canvas.copy()
        angle = math.sin(t * 22.0) * 8.0
        size = self._scale_xy(120, 48)
        badge = Image.new("RGBA", (size[0] + 20, size[1] + 20), (0, 0, 0, 0))
        draw = ImageDraw.Draw(badge)
        draw.rounded_rectangle([4, 4, size[0] + 4, size[1] + 4], radius=12, fill=(185, 28, 28, 230))
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)
        except Exception:
            font = ImageFont.load_default()
        draw.text((18, 12), "SEC HANG", font=font, fill=(255, 255, 255, 255))
        rotated = badge.rotate(angle, expand=True, resample=Image.Resampling.BILINEAR)
        pos = self._scale_xy(780, 70)
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        overlay.paste(rotated, pos, rotated)
        canvas.paste(overlay, (0, 0), overlay)
        return canvas

    def _collect_unknown_fx(self, segments: list) -> list[str]:
        unknown: list[str] = []
        for seg in segments:
            for name in seg.get("fx") or []:
                if name not in KNOWN_FX and name not in unknown:
                    unknown.append(name)
        return unknown

    def _apply_fx(self, frame: Image.Image, t: float, segments: list) -> Image.Image:
        current = frame
        accent = (*self.style.primary_accent, 110)
        gold = (212, 175, 55, 120)
        wave_color = (*self.style.secondary_accent, 220)
        for seg in segments:
            fxs = seg.get("fx") or []
            if not fxs:
                continue
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start))
            dur = max(0.001, end - start)
            in_seg = start <= t < end
            after_start = t >= start

            if "highlighter_sweep" in fxs and after_start:
                progress = 1.0 if t >= end else min(1.0, (t - start) / min(0.7, dur))
                current = MarkerFX.apply(current, self._scale_box((80, 520, 520, 620)), progress, accent)
            if "gold_light_sweep" in fxs and after_start:
                progress = 1.0 if t >= end else min(1.0, (t - start) / min(0.6, dur))
                current = MarkerFX.apply(current, self._scale_box((120, 180, 960, 280)), progress, gold)
            if "click_pulse" in fxs:
                current = PulseFX.apply(
                    current,
                    self._scale_xy(540, 1100),
                    t,
                    start,
                    duration=0.8,
                    color=self.style.primary_accent,
                )
            if "waveform_equalizer" in fxs and in_seg:
                x, y = self._scale_xy(90, 980)
                bw, bh = self._scale_xy(420, 160)
                current = WaveformFX.apply(current, (x, y, bw, bh), t, True, color=wave_color)
            if "stamp_impact" in fxs and after_start:
                current = StampFX.apply(
                    current, self._find_stamp_image(False), t, start,
                    self._scale_xy(820, 640),
                )
            if "score_stamp_impact" in fxs and after_start:
                current = StampFX.apply(
                    current, self._find_stamp_image(True), t, start,
                    self._scale_xy(820, 640),
                )
            if "warning_badge_shake" in fxs and in_seg:
                current = self._apply_warning_badge(current, t)
        return current

    def _qa_indices(self, segments: list, total_frames: int, page_flip_dur: float, has_flip: bool) -> set[int]:
        last = max(0, total_frames - 1)
        indices = {0, last}
        if has_flip:
            indices.add(min(last, max(0, int(round(page_flip_dur * self.fps)))))
        for seg in segments:
            start_i = int(round(seg["start"] * self.fps))
            end_i = int(round(seg["end"] * self.fps)) - 1
            indices.add(min(last, max(0, start_i)))
            indices.add(min(last, max(0, end_i)))
            if seg["end"] - seg["start"] >= 2.0:
                mid = int(round(((seg["start"] + seg["end"]) / 2.0) * self.fps))
                indices.add(min(last, max(0, mid)))
        return {i for i in indices if 0 <= i <= last}

    def render_scene(self, scene_id_or_num) -> str:
        sc = self.config.get_scene(scene_id_or_num)
        if not sc:
            raise ValueError(f"Scene {scene_id_or_num} not found in storyboard.")

        scene_id = sc.get("id", "scene_01")
        print(f"\n==========================================")
        print(f"[Render] Starting render for: {scene_id} ({sc.get('stage_tag', '')})")
        print("==========================================")

        self.manifest.assert_matches_storyboard(sc)
        scene_data = self.manifest.get_scene(scene_id)
        segments = scene_data.get("segments", [])
        unknown = self._collect_unknown_fx(segments)
        if unknown:
            raise ValueError(f"Unknown fx tags in {scene_id}: {unknown}. Known: {sorted(KNOWN_FX)}")

        total_duration = float(scene_data.get("total_duration", 10.0))
        total_frames = max(1, int(round(total_duration * self.fps)))
        master_audio_path = os.path.join(self.project_dir, "audio", f"{scene_id}_master.wav")
        if not os.path.exists(master_audio_path):
            raise FileNotFoundError(f"Master audio not found: {master_audio_path}")

        pose_map, default_img = self._load_pose_images(scene_id, segments)
        sequencer = StopMotionSequencer(segments, pose_map, default_img)

        trans_config = sc.get("transition", {}) or {}
        trans_type = trans_config.get("type", "none")
        page_flip_dur = float(trans_config.get("duration", self.style.default_page_flip_dur))
        prev_anchor_img = None
        if trans_type == "page_flip":
            scene_idx = self.config.scenes.index(sc)
            if scene_idx > 0:
                prev_sc_id = self.config.scenes[scene_idx - 1].get("id")
                anchor_file = os.path.join(self.anchors_dir, f"{prev_sc_id}_end.png")
                if os.path.exists(anchor_file):
                    prev_anchor_img = Image.open(anchor_file).convert("RGBA").resize(
                        self.res, Image.Resampling.LANCZOS
                    )
                    print(f"✓ Loaded previous anchor for page flip: {anchor_file}")
                else:
                    print(f"Notice: Previous anchor {anchor_file} not found. Skipping page flip.")

        output_mp4 = os.path.join(self.output_video_dir, f"{scene_id}.mp4")
        scene_qa_dir = os.path.join(self.qa_dir, scene_id)
        os.makedirs(scene_qa_dir, exist_ok=True)

        require_ffmpeg()
        cmd = [
            "ffmpeg", "-y",
            "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo",
            "-pix_fmt", "rgba",
            "-s", f"{self.res[0]}x{self.res[1]}",
            "-r", str(self.fps),
            "-i", "-",
            "-i", master_audio_path,
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "320k",
            "-t", f"{total_duration:.3f}",
            "-movflags", "+faststart",
            output_mp4,
        ]
        err_log = os.path.join(scene_qa_dir, "ffmpeg_stderr.log")
        err_handle = open(err_log, "wb")
        pipe = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=err_handle,
        )

        qa_frame_indices = self._qa_indices(segments, total_frames, page_flip_dur, prev_anchor_img is not None)
        cut_times = [
            float(seg["start"])
            for seg in segments
            if float(seg.get("start", 0.0)) > 0.05
        ]
        print(f"Rendering {total_frames} frames @ {self.fps}fps ({total_duration:.2f}s)...")
        last_t = (total_frames - 1) / self.fps
        broken = False
        try:
            for frame_idx in range(total_frames):
                t = frame_idx / self.fps
                current_frame = sequencer.get_frame(t).copy()
                if prev_anchor_img and t < page_flip_dur:
                    current_frame = PageFlipTransition.render(
                        prev_anchor_img, current_frame, t / page_flip_dur
                    )
                current_frame = self._apply_fx(current_frame, t, segments)
                push_progress = frame_idx / max(1, total_frames - 1)
                display_frame = CameraDirector.apply_combined(
                    current_frame, push_progress, t, cut_times, max_zoom=1.030
                )
                active_text = ""
                for seg in segments:
                    if seg["start"] <= t < seg["end"]:
                        active_text = seg["text"]
                if active_text:
                    display_frame = self.subtitle_engine.render(
                        display_frame, active_text, y_center=self.subtitle_y
                    )
                try:
                    pipe.stdin.write(display_frame.tobytes())
                except BrokenPipeError as exc:
                    broken = True
                    raise RuntimeError(f"FFmpeg pipeline broken while writing frame {frame_idx}.") from exc
                if frame_idx in qa_frame_indices:
                    qa_path = os.path.join(scene_qa_dir, f"frame_{frame_idx:04d}_{t:.2f}s.jpg")
                    display_frame.convert("RGB").save(qa_path, quality=90)
        finally:
            if pipe.stdin and not pipe.stdin.closed:
                try:
                    pipe.stdin.close()
                except Exception:
                    pass
            pipe.wait()
            err_handle.close()
            if pipe.returncode not in (0, None) and not broken:
                try:
                    with open(err_log, "r", encoding="utf-8", errors="replace") as handle:
                        err_text = handle.read().strip()
                except Exception:
                    err_text = ""
                raise RuntimeError(
                    f"FFmpeg render process failed with code {pipe.returncode}:\n{err_text}"
                )
            if os.path.exists(err_log) and os.path.getsize(err_log) == 0:
                os.remove(err_log)

        anchor_frame = sequencer.get_frame(last_t).copy()
        anchor_frame = self._apply_fx(anchor_frame, last_t, segments)
        anchor_save_path = os.path.join(self.anchors_dir, f"{scene_id}_end.png")
        anchor_frame.save(anchor_save_path)
        print(f"✓ Scene anchor saved to: {anchor_save_path}")
        print(f"✓ Scene MP4 delivered: {output_mp4}")
        print(f"✓ QA Frames saved in: {scene_qa_dir}")
        return output_mp4
