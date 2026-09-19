import os
import glob
import subprocess
from PIL import Image

from studio.core.config import StoryboardConfig
from studio.core.manifest import TimestampManifest
from studio.styles import get_style
from studio.engine.transitions import PageFlipTransition
from studio.engine.stopmotion import StopMotionSequencer
from studio.engine.subtitles import AdaptiveCapsuleSubtitle
from studio.engine.camera import KenBurnsZoom
from studio.engine.fx.stamp import StampFX
from studio.engine.fx.marker import MarkerFX
from studio.engine.fx.pulse import PulseFX
from studio.engine.fx.waveform import WaveformFX

class SceneRenderer:
    """
    Modular Scene Renderer executing the multi-layer pipeline:
    Transitions -> Native Stop-Motion -> Dynamic FX -> KenBurns -> Adaptive Subtitles.
    """
    
    def __init__(self, config: StoryboardConfig, manifest: TimestampManifest = None):
        self.config = config
        self.project_dir = config.project_dir
        self.style = get_style(config.style_preset)
        self.fps = config.fps
        self.res = config.resolution # (1080, 1920)
        
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
        
        self.subtitle_engine = AdaptiveCapsuleSubtitle(
            default_font_size=self.style.subtitle_font_size,
            max_width=self.style.subtitle_max_width
        )

    def _load_pose_images(self, scene_id: str, segments: list) -> tuple[dict, Image.Image]:
        """Loads all available masterframe pose images for the scene."""
        pose_map = {}
        default_img = None
        
        # Search patterns in assets/masterframes/
        patterns = [
            os.path.join(self.masterframes_dir, f"{scene_id}*.*"),
            os.path.join(self.masterframes_dir, f"*{scene_id}*.*"),
            os.path.join(self.project_dir, "素材", "04_分幕原生画卷", f"*{scene_id}*.*"),
            os.path.join(self.project_dir, "素材", f"*{scene_id}*.*")
        ]
        
        found_files = []
        for pat in patterns:
            found_files.extend(glob.glob(pat))
            
        # Deduplicate while preserving order
        unique_files = []
        for f in found_files:
            if f not in unique_files and os.path.isfile(f) and f.lower().endswith((".png", ".jpg", ".jpeg")):
                unique_files.append(f)
                
        # Load and resize
        loaded_images = []
        for f in unique_files:
            try:
                img = Image.open(f).convert("RGBA").resize(self.res, Image.Resampling.LANCZOS)
                loaded_images.append((os.path.basename(f), img))
            except Exception as e:
                print(f"Warning: Could not open {f}: {e}")
                
        if loaded_images:
            default_img = loaded_images[0][1]
            
            # Map images to segments
            for idx, seg in enumerate(segments):
                seg_id = seg.get("id", "")
                pose_name = seg.get("pose", "")
                
                # Match by filename substring or fallback to index
                matched_img = None
                for fname, img in loaded_images:
                    if pose_name and pose_name.lower() in fname.lower():
                        matched_img = img
                        break
                    if f"pose{idx+1}" in fname.lower() or f"pose_{idx+1}" in fname.lower():
                        matched_img = img
                        break
                        
                if matched_img is None:
                    matched_img = loaded_images[min(idx, len(loaded_images)-1)][1]
                    
                if pose_name:
                    pose_map[pose_name] = matched_img
                if seg_id:
                    pose_map[seg_id] = matched_img
        else:
            # Fallback placeholder canvas if user hasn't generated images yet
            print(f"Notice: No masterframe image found for {scene_id}. Creating fallback placeholder canvas.")
            default_img = Image.new("RGBA", self.res, (*self.style.background_color, 255))
            for seg in segments:
                pose_map[seg.get("id", "")] = default_img
                if seg.get("pose"):
                    pose_map[seg["pose"]] = default_img
                    
        return pose_map, default_img

    def render_scene(self, scene_id_or_num) -> str:
        sc = self.config.get_scene(scene_id_or_num)
        if not sc:
            raise ValueError(f"Scene {scene_id_or_num} not found in storyboard.")
            
        scene_id = sc.get("id", "scene_01")
        print(f"\n==========================================")
        print(f"[Render] Starting render for: {scene_id} ({sc.get('stage_tag', '')})")
        print(f"==========================================")
        
        scene_data = self.manifest.get_scene(scene_id)
        if not scene_data:
            raise ValueError(f"Manifest has no record for {scene_id}. Run 'studio audio build' first!")
            
        segments = scene_data.get("segments", [])
        total_duration = scene_data.get("total_duration", 10.0)
        total_frames = int(round(total_duration * self.fps))
        
        # Audio path
        master_audio_path = os.path.join(self.project_dir, "audio", f"{scene_id}_master.wav")
        if not os.path.exists(master_audio_path):
            raise FileNotFoundError(f"Master audio not found: {master_audio_path}")
            
        # Assets & Sequencer
        pose_map, default_img = self._load_pose_images(scene_id, segments)
        sequencer = StopMotionSequencer(segments, pose_map, default_img)
        
        # Check transition (Page flip from previous scene anchor)
        trans_config = sc.get("transition", {})
        trans_type = trans_config.get("type", "none")
        page_flip_dur = trans_config.get("duration", self.style.default_page_flip_dur)
        
        prev_anchor_img = None
        if trans_type == "page_flip":
            # Find previous scene id
            scene_idx = self.config.scenes.index(sc)
            if scene_idx > 0:
                prev_sc_id = self.config.scenes[scene_idx - 1].get("id")
                anchor_file = os.path.join(self.anchors_dir, f"{prev_sc_id}_end.png")
                if os.path.exists(anchor_file):
                    prev_anchor_img = Image.open(anchor_file).convert("RGBA").resize(self.res)
                    print(f"✓ Loaded previous anchor for page flip: {anchor_file}")
                else:
                    print(f"Notice: Previous anchor {anchor_file} not found. Skipping page flip.")
                    
        # Output paths
        output_mp4 = os.path.join(self.output_video_dir, f"{scene_id}.mp4")
        scene_qa_dir = os.path.join(self.qa_dir, scene_id)
        os.makedirs(scene_qa_dir, exist_ok=True)
        
        # FFmpeg process
        cmd = [
            "ffmpeg", "-y",
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
            "-shortest",
            output_mp4
        ]
        
        pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        qa_frame_indices = set([0, int(page_flip_dur * self.fps), total_frames - 1])
        for seg in segments:
            qa_frame_indices.add(int(seg["start"] * self.fps))
            qa_frame_indices.add(int(seg["end"] * self.fps))
            
        print(f"Rendering {total_frames} frames @ {self.fps}fps ({total_duration:.2f}s)...")
        last_frame = default_img
        
        for frame_idx in range(total_frames):
            t = frame_idx / self.fps
            
            # Layer 1: Base pose
            current_frame = sequencer.get_frame(t).copy()
            
            # Page flip transition
            if prev_anchor_img and t < page_flip_dur:
                flip_progress = t / page_flip_dur
                current_frame = PageFlipTransition.render(prev_anchor_img, current_frame, flip_progress)
                
            # Layer 2: Camera slow push
            push_progress = frame_idx / total_frames
            current_frame = KenBurnsZoom.apply(current_frame, push_progress)
            
            # Layer 3: Subtitle overlay
            active_text = ""
            for seg in segments:
                if seg["start"] <= t <= seg["end"]:
                    active_text = seg["text"]
                    break
                    
            if active_text:
                current_frame = self.subtitle_engine.render(current_frame, active_text, y_center=self.style.subtitle_y)
                
            # Pipe to FFmpeg
            raw_bytes = current_frame.tobytes()
            pipe.stdin.write(raw_bytes)
            
            # Save QA frame if matched
            if frame_idx in qa_frame_indices:
                qa_path = os.path.join(scene_qa_dir, f"frame_{frame_idx:04d}_{t:.2f}s.jpg")
                current_frame.convert("RGB").save(qa_path, quality=90)
                
            last_frame = current_frame
            
        pipe.stdin.close()
        pipe.wait()
        
        # Save last frame as anchor for next scene
        anchor_save_path = os.path.join(self.anchors_dir, f"{scene_id}_end.png")
        last_frame.save(anchor_save_path)
        print(f"✓ Scene anchor saved to: {anchor_save_path}")
        print(f"✓ Scene MP4 delivered: {output_mp4}")
        print(f"✓ QA Frames saved in: {scene_qa_dir}")
        return output_mp4
