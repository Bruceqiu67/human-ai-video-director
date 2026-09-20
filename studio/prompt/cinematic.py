"""Cinematic Camera Motion & Video Prompt Generator for AI Video Platforms.

Targets: Kling (可灵), Runway (Gen-3), Luma Dream Machine, Sora, Minimax (海螺).
Implements industry-standard cinematography directing grammar:
- Camera Movement First Principle
- 'One-Move' per shot discipline
- Camera motion decoupled from subject physics
- In-Context reference to generated masterframes (Image-to-Video / I2V)
"""

from __future__ import annotations

from typing import Any


class CinematicPromptEngine:
    """Generates broadcast-grade AI video prompts with camera motion and physics."""

    CAMERA_PRESETS = {
        # Hook / Pain Point: intimate macro push-in, subtle tension
        "hook": {
            "camera_en": "Slow, subtle Dolly-In (push-in) from medium close-up to extreme macro close-up with shallow depth of field (f/1.8). Camera maintains steady straight trajectory.",
            "camera_zh": "缓慢平滑推镜头（Dolly-In），景深由中近景微距推至主体特写，浅景深虚化背景，镜头轨迹平稳推进。",
            "motion_brush": "微距直推 · 匀速缓入",
            "speed": "Slow (0.8x)",
        },
        # Hero / Feature: 3D depth, orbit or low-angle pedestal
        "hero": {
            "camera_en": "Smooth 30-degree horizontal Orbit / Arc shot combined with gentle low-angle tilt-up, gliding around the front and side of the subject.",
            "camera_zh": "30度小弧度平滑环绕运镜（Subtle Orbit），配合微低角度轻微仰拍，展现主体3D立体质感与光影转折。",
            "motion_brush": "水平弧形环绕 · 顺滑慢推",
            "speed": "Normal (1.0x)",
        },
        # Transition / Solution: smooth truck or pedestal
        "solution": {
            "camera_en": "Gentle Truck Right tracking shot alongside the desk setup, smooth constant velocity with cinematic parallax effect.",
            "camera_zh": "平稳横移镜头（Truck Right），匀速横向滑轨移动，前景与后景呈现电影级视差层次感。",
            "motion_brush": "横向滑轨 · 视差推进",
            "speed": "Normal (1.0x)",
        },
        # CTA / Ending: pull-back reveal, grand cozy atmosphere
        "cta": {
            "camera_en": "Slow Dolly-Out (pull-back reveal) drifting backward and slightly upward, transitioning from hero center close-up to a cozy wide atmosphere.",
            "camera_zh": "平缓后拉全景镜头（Dolly-Out / Pull-Back Reveal），由主体特写平稳拉远至温馨全局氛围全景。",
            "motion_brush": "全景后拉 · 氛围展开",
            "speed": "Slow Deceleration (0.9x)",
        },
    }

    @classmethod
    def detect_shot_type(cls, stage_tag: str, index: int, total: int) -> str:
        tag = (stage_tag or "").lower()
        if "01" in tag or "hook" in tag or "沉闷" in tag or "痛点" in tag or index == 1:
            return "hook"
        if "cta" in tag or "号召" in tag or "行动" in tag or "升华" in tag or index == total:
            return "cta"
        if "02" in tag or "hero" in tag or "点睛" in tag or "颜值" in tag or "破局" in tag:
            return "hero"
        return "solution"

    @classmethod
    def generate_scene_video_prompts(
        cls,
        scene_idx: int,
        stage_tag: str,
        headline: str,
        segments: list[dict[str, Any]],
        total_scenes: int,
        character_prompt: str,
    ) -> list[dict[str, str]]:
        shot_type = cls.detect_shot_type(stage_tag, scene_idx, total_scenes)
        preset = cls.CAMERA_PRESETS[shot_type]
        results = []

        for p_idx, seg in enumerate(segments, 1):
            text = seg.get("text", "")
            pose = seg.get("pose", "出镜演示")
            dur = seg.get("duration", 3.0)

            # Kling AI prompt format (Bilingual, camera-first)
            kling_prompt = (
                f"【首帧图生视频指令】\n"
                f"运镜指令：{preset['camera_zh']}\n"
                f"主体物理动态：画面主体在保持第一帧外观与材质的前提下，产生自然的微呼吸感与轻微动态响应（{pose}），动作自然舒展，避免形变。\n"
                f"环境与光影：背景环境光源产生自然的轻微光斑呼吸律动与漫反射，保持背景空间几何稳定。\n"
                f"画质与稳定性：电影级商业质感，30fps超稳定动态，无融化，无画面撕裂，无文字扭曲。"
            )

            # Runway Gen-3 / Sora format (English strict camera-first formula)
            runway_prompt = (
                f"[Camera]: {preset['camera_en']}\n"
                f"[Subject Motion]: Based on the first frame, the subject performs: {pose}. Natural organic micro-movements and breathing rhythm, preserving character identity and texture without warping.\n"
                f"[Lighting & Atmosphere]: Warm atmospheric light diffusion, realistic specular reflections, cinematic bokeh in background.\n"
                f"[Stability & Quality]: 4K photorealistic product commercial, 30fps smooth cadence, locked geometry, no melting, no artifacting."
            )

            results.append({
                "scene_idx": scene_idx,
                "pose_idx": p_idx,
                "stage_tag": stage_tag,
                "headline": headline,
                "dialogue": text,
                "pose": pose,
                "duration": f"{dur:.1f}s",
                "camera_zh": preset["camera_zh"],
                "camera_en": preset["camera_en"],
                "motion_type": preset["motion_brush"],
                "kling_prompt": kling_prompt,
                "runway_prompt": runway_prompt,
            })

        return results
