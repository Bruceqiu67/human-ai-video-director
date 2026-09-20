"""Cinematic Camera Motion & Video Prompt Generator for AI Video Platforms.

Targets: Kling (可灵), Runway (Gen-3), Luma Dream Machine, Sora, Minimax (海螺), Jimeng (即梦).
Implements industry-standard cinematography directing grammar:
- Camera Movement First Principle
- 'One-Move' per shot discipline
- Camera motion decoupled from subject physics
- In-Context reference to generated masterframes (Image-to-Video / I2V)
- Multi-act chunking and first/end frame relay SOP
"""

from __future__ import annotations

import os
from typing import Any


class CinematicPromptEngine:
    """Generates broadcast-grade AI video prompts with camera motion, settings, and step-by-step SOP."""

    PLATFORMS = {
        "kling": {
            "name": "快手可灵 AI (Kling 3.0 / 1.5)",
            "mode": "图生视频 (I2V) · 首尾帧模式",
            "duration": "5s (标准分镜) / 10s (长篇拆解)",
            "motion_scale": "3 ~ 4 (推荐，防肢体面部过度形变)",
            "camera_feature": "运镜控制 (水平/垂直/变焦/俯仰/横摇) 或 运动笔刷",
            "file_naming": "scene_{idx:02d}_ai.mp4",
        },
        "runway": {
            "name": "Runway Gen-3 (Alpha / Turbo)",
            "mode": "Image-to-Video (First Frame / Last Frame)",
            "duration": "5s or 10s",
            "motion_scale": "2 ~ 3 (保持物理拟真度，避免 >4 融化)",
            "camera_feature": "Camera Control Sliders (Pan, Tilt, Zoom, Roll, Speed 1-10)",
            "file_naming": "scene_{idx:02d}_ai.mp4",
        },
        "luma": {
            "name": "Luma Dream Machine",
            "mode": "Image-to-Video + Extend",
            "duration": "5s (可使用 Extend 延长 5s)",
            "motion_scale": "默认物理引擎",
            "camera_feature": "Camera Motion 预设 + 自然语言精准运镜",
            "file_naming": "scene_{idx:02d}_ai.mp4",
        },
        "hailuo": {
            "name": "海螺 AI (Minimax) / 智谱清影",
            "mode": "图生视频",
            "duration": "6s",
            "motion_scale": "高物理动态模式",
            "camera_feature": "文本强引导，自动推演光影流动",
            "file_naming": "scene_{idx:02d}_ai.mp4",
        },
        "jimeng": {
            "name": "字节即梦 (Jimeng)",
            "mode": "图生视频 · 首尾帧插值",
            "duration": "3s / 5s",
            "motion_scale": "中度运动",
            "camera_feature": "运镜轨迹选择 + 首尾帧过渡",
            "file_naming": "scene_{idx:02d}_ai.mp4",
        },
    }

    CAMERA_PRESETS = {
        # Hook / Pain Point: intimate macro push-in, subtle tension
        "hook": {
            "camera_en": "Slow, subtle Dolly-In (push-in) from medium close-up to extreme macro close-up with shallow depth of field (f/1.8). Camera maintains steady straight trajectory.",
            "camera_zh": "缓慢平滑推镜头（Dolly-In），景深由中近景微距推至主体特写，浅景深虚化背景，镜头轨迹平稳推进。",
            "motion_brush": "微距直推 · 匀速缓入 (Dolly-In)",
            "speed": "Slow (0.8x)",
            "slider_runway": "Zoom: +1.5 ~ +2.0, Speed: 3",
            "slider_kling": "变焦 (Zoom): +2.0, 其余轴锁定为 0",
        },
        # Hero / Feature: 3D depth, orbit or low-angle pedestal
        "hero": {
            "camera_en": "Smooth 30-degree horizontal Orbit / Arc shot combined with gentle low-angle tilt-up, gliding around the front and side of the subject.",
            "camera_zh": "30度小弧度平滑环绕运镜（Subtle Orbit），配合微低角度轻微仰拍，展现主体3D立体质感与光影转折。",
            "motion_brush": "水平弧形环绕 · 顺滑慢推 (Subtle Orbit)",
            "speed": "Normal (1.0x)",
            "slider_runway": "Pan: +1.5, Tilt: +0.5, Speed: 3",
            "slider_kling": "水平横移 (Pan): +1.5, 俯仰 (Tilt): +0.5",
        },
        # Transition / Solution: smooth truck or pedestal
        "solution": {
            "camera_en": "Gentle Truck Right tracking shot alongside the desk setup, smooth constant velocity with cinematic parallax effect.",
            "camera_zh": "平稳横移镜头（Truck Right），匀速横向滑轨移动，前景与后景呈现电影级视差层次感。",
            "motion_brush": "横向滑轨 · 视差推进 (Truck Right)",
            "speed": "Normal (1.0x)",
            "slider_runway": "Pan: +2.0, Speed: 3",
            "slider_kling": "水平移动 (Pan): +2.0",
        },
        # CTA / Ending: pull-back reveal, grand cozy atmosphere
        "cta": {
            "camera_en": "Slow Dolly-Out (pull-back reveal) drifting backward and slightly upward, transitioning from hero center close-up to a cozy wide atmosphere.",
            "camera_zh": "平缓后拉全景镜头（Dolly-Out / Pull-Back Reveal），由主体特写平稳拉远至温馨全局氛围全景。",
            "motion_brush": "全景后拉 · 氛围展开 (Dolly-Out)",
            "speed": "Slow Deceleration (0.9x)",
            "slider_runway": "Zoom: -2.0, Tilt: +0.5, Speed: 3",
            "slider_kling": "变焦 (Zoom): -2.0, 俯仰 (Tilt): +0.5",
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
        project_name: str = "",
    ) -> list[dict[str, Any]]:
        shot_type = cls.detect_shot_type(stage_tag, scene_idx, total_scenes)
        preset = cls.CAMERA_PRESETS[shot_type]
        results = []

        for p_idx, seg in enumerate(segments, 1):
            text = seg.get("text", "")
            pose = seg.get("pose", "出镜演示")
            dur = seg.get("duration", 3.0)

            # Target matching masterframe filename
            first_frame_name = f"Scene{scene_idx:02d}_pose_{p_idx}.jpg"
            first_frame_path = os.path.join(
                "projects", project_name, "assets", "masterframes", first_frame_name
            ) if project_name else f"assets/masterframes/{first_frame_name}"

            # End frame anchor for scene
            end_frame_name = f"scene_{scene_idx:02d}_end.png"
            end_frame_path = os.path.join(
                "projects", project_name, "assets", "anchors", end_frame_name
            ) if project_name else f"assets/anchors/{end_frame_name}"

            # Next scene first frame for cross-scene transition
            next_scene_idx = scene_idx + 1 if scene_idx < total_scenes else None
            next_frame_name = f"Scene{next_scene_idx:02d}_pose_1.jpg" if next_scene_idx else ""
            next_frame_path = os.path.join(
                "projects", project_name, "assets", "masterframes", next_frame_name
            ) if next_scene_idx and project_name else (f"assets/masterframes/{next_frame_name}" if next_scene_idx else "")

            # Kling AI prompt format (Bilingual, camera-first)
            kling_prompt = (
                f"【运镜指令】{preset['camera_zh']}\n"
                f"【主体动态】保持第一帧材质纹理与几何轮廓，进行微距呼吸与轻微动态响应（{pose}），动作平缓稳定，零融化。\n"
                f"【光影漫射】演播室级漫反射光影流动，高光反射随视角平滑移动，背景空间几何完全锁定。\n"
                f"【画质标准】电影级质感，30fps稳定帧率，物理拟真，无伪影。"
            )
            kling_negative = (
                "画面撕裂，扭曲形变，融化，金属变软，肢体变异，突变镜头，频闪，水印，杂乱背景，低分辨率，模糊，卡顿，怪异手部，额外肢体，突兀变色，大幅度抽搐"
            )

            # Runway Gen-3 / Sora format (English strict camera-first formula)
            runway_prompt = (
                f"[Camera]: {preset['camera_en']}\n"
                f"[Subject]: Strictly preserve first-frame geometry and textures, performing subtle micro-action: {pose}. Locked physical structure.\n"
                f"[Lighting]: Subtle specular highlight displacement across surface, cinematic soft atmospheric diffusion, stable bokeh.\n"
                f"[Quality]: 4K commercial quality, 30fps smooth cadence, zero morphing, zero jitter."
            )
            runway_negative = (
                "morphing, melting, distortions, warped geometry, noisy, sudden cuts, camera jitter, text, watermark, extra limbs, deformed body, blurry, flickering, temporal artifacts, low resolution, unnatural bending"
            )

            results.append({
                "scene_idx": scene_idx,
                "pose_idx": p_idx,
                "stage_tag": stage_tag,
                "headline": headline,
                "dialogue": text,
                "pose": pose,
                "duration": f"{dur:.1f}s",
                "first_frame_path": first_frame_path,
                "first_frame_name": first_frame_name,
                "end_frame_path": end_frame_path,
                "next_frame_path": next_frame_path,
                "camera_zh": preset["camera_zh"],
                "camera_en": preset["camera_en"],
                "motion_type": preset["motion_brush"],
                "slider_kling": preset["slider_kling"],
                "slider_runway": preset["slider_runway"],
                "kling_prompt": kling_prompt,
                "kling_negative": kling_negative,
                "runway_prompt": runway_prompt,
                "runway_negative": runway_negative,
                "output_ai_name": f"scene_{scene_idx:02d}.mp4",
            })

        return results

    @classmethod
    def generate_full_sop_markdown(cls, config: Any) -> str:
        """Produces a comprehensive platform-adaptive production plan."""
        project_name = config.name
        title = config.title
        total_scenes = len(config.scenes)

        lines = [
            f"# 🎥 《{title}》大模型生视频平台工业化实战 SOP 与专业运镜指令全案",
            "## (Platform-Adaptive AI Video Directing SOP & Multi-Shot Chunking Guide)",
            "",
            "> [!IMPORTANT]",
            "> **长视频拆解与平台协同核心逻辑 (The Core AI Video Workflow)**：",
            "> 1. **单次生成时长限制与分镜头切片**：主流平台（可灵/Runway/Luma）单次生成上限通常为 5s 或 10s，全片无法单次生成。本工坊已自动将全剧本按叙事节奏拆解为独立的 3~5 秒微镜头切片，天然完美契合各平台的 5s 生成窗口！",
            "> 2. **首尾帧无缝接力 (First-End Frame Relay)**：",
            ">    - **首帧 (First Frame)**：上传本镜头母版原画（`assets/masterframes/`）；",
            ">    - **尾帧 (End Frame / 锚点过渡)**：若平台支持首尾帧，上传本镜头末帧锚点（`assets/anchors/`）或下一镜头首帧，平台将自动计算位移与光影过渡，彻底告别镜头切换跳脱！",
            "> 3. **Camera First 运镜法则**：机位指令绝对前置，一镜一动，相机轨迹与主体动作解耦，运动幅度锁定在 `3~4`（防融化）。",
            "> 4. **本地回流智能总装 (Round-trip Master Assembly)**：外部生成完成后，将视频存入 `assets/raw_video/`，本地执行一行命令即可与**微软高清声音母带**完成毫秒对齐与**动态侧链闪避混音**！",
            "",
            "---",
            "",
            "## 🛡️ 生产级「零抽卡」五大防线 (The 5 Anti-Gacha Engineering Rules)",
            "> 为什么常规 AI 生视频需要重复抽卡 20 次？因为开环扩散模型在没有边界和负面约束时，潜在空间会产生无序发散，导致金属融化、人物变脸、镜头抽搐！",
            "> 本工坊通过以下 5 道确定性防线将废片率降至最低：",
            "",
            "1. **【首尾双锚点定界】**：上传首帧母版图 + 尾帧锚点（或下一幕首图），将无限发散的推演收敛为首尾定界插值方程，模型物理结构被牢牢夹死；",
            "2. **【机位与物理绝对解耦】**：恪守 One-Move Rule（一镜一动），相机只走平滑单一轨迹，主体仅保留微距呼吸与光影漫反射，杜绝指令冲突撕裂；",
            "3. **【安全运动幅度阈值】**：严格锁定运动幅度为 `3 ~ 4`（Runway `2 ~ 3`），绝不使用容易导致融化崩坏的高运动阈值；",
            "4. **【反向负面词重装甲 (Negative Shield)】**：为每个分镜提供工业级反向提示词，直接在采样前剔除频闪、形变、乱码与软化；",
            "5. **【声画毫秒级锁相总装】**：彻底丢弃外部 AI 生成的廉价音效与变调人声，由本地 `studio assemble` 将高质量母带与 AI 画面无损对齐汇流！",
            "",
            "---",
            "",
            "## 🎛️ 主流 AI 视频制作平台参数配置速查表 (Platform Settings Checklist)",
            "",
            "| 平台名称 | 推荐模式 | 建议生成时长 | 运动幅度 (Motion Scale) | 核心运镜设置指南 | 生成后保存路径 |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
            "| **快手可灵 (Kling 3.0)** | 图生视频 (首尾帧) | `5s` | `3 ~ 4` (推荐防形变) | 开启【运镜控制】，选择平推或弧形环绕 | `assets/raw_video/scene_XX.mp4` |",
            "| **Runway Gen-3 (Alpha/Turbo)** | Image-to-Video | `5s` | `2 ~ 3` (锁定拟真度) | 使用 Camera Control 滑块设置 Zoom / Pan | `assets/raw_video/scene_XX.mp4` |",
            "| **Luma Dream Machine** | Image-to-Video | `5s` (支持 Extend) | 默认物理引擎 | 复制下方英文指令，选择内置运镜预设 | `assets/raw_video/scene_XX.mp4` |",
            "| **海螺 AI (Minimax)** | 图生视频 | `6s` | 高物理动态 | 复制下方中文指令，文本强控制 | `assets/raw_video/scene_XX.mp4` |",
            "| **字节即梦 (Jimeng)** | 图生视频 (首尾帧) | `3s` 或 `5s` | 中度运动 | 上传首尾帧，选择运镜轨迹 | `assets/raw_video/scene_XX.mp4` |",
            "",
            "---",
            "",
            "## 📋 逐幕分镜头实战任务卡 (Step-by-Step Production Cards)",
            "",
        ]

        for idx, sc in enumerate(config.scenes, 1):
            stage_tag = sc.get("stage_tag", f"STAGE {idx:02d}")
            headline = sc.get("headline", "")
            segments = sc.get("dialogue_segments", [])
            prompts = cls.generate_scene_video_prompts(
                idx, stage_tag, headline, segments, total_scenes, config.character_prompt, project_name
            )

            lines.append(f"### 🎬 分镜 Scene {idx:02d}：{stage_tag}（{headline}）")
            lines.append("")

            for p in prompts:
                lines.append(f"#### 🎯 镜头 {idx}.{p['pose_idx']} 实战任务卡：{p['pose']}")
                lines.append(f"- **台词旁白**：*{p['dialogue']}*")
                lines.append(f"- **分镜时长**：`{p['duration']}`（对应平台 5s 档位）")
                lines.append("")
                lines.append(f"**【第 1 步 · 首帧图片上传】**：")
                lines.append(f"- 在平台选择【图生视频 (Image-to-Video)】模式；")
                lines.append(f"- **首帧输入 (First Frame)** 上传：`{p['first_frame_path']}`")
                lines.append("")

                if p["next_frame_path"]:
                    lines.append(f"**【第 2 步 · 尾帧接力上传（首尾帧平台专享，彻底锁定终点）】**：")
                    lines.append(f"- **尾帧输入 (Last Frame / End Anchor)** 上传：`{p['end_frame_path']}` 或下一幕首图 `{p['next_frame_path']}`")
                    lines.append(f"- *防抽卡作用：锁定镜头末尾位移与形态，两点定界消除形变与断崖！*")
                    lines.append("")

                lines.append(f"**【第 3 步 · 平台参数面板设置】**：")
                lines.append(f"- **生成时长**：`5s`（或 `6s`）")
                lines.append(f"- **运动幅度 (Motion)**：锁定在 `3 ~ 4`（Runway 设置为 `2 ~ 3`，严禁超过 4.5）")
                lines.append(f"- **运镜轨迹**：`{p['motion_type']}`")
                lines.append(f"- **可灵运镜参数建议**：`{p['slider_kling']}`")
                lines.append(f"- **Runway 滑块建议**：`{p['slider_runway']}`")
                lines.append("")

                lines.append(f"**【第 4 步 · 复制对应平台专用指令与反向装甲】**：")
                lines.append("##### 🌟 方案 A：可灵 AI (Kling 3.0 / 海螺 AI / 即梦) 专属中文指令")
                lines.append("- **正向提示词 (Positive)**（点击一键复制）：")
                lines.append("```text")
                lines.append(p["kling_prompt"])
                lines.append("```")
                lines.append("- **反向负面提示词 (Negative Shield)**（点击一键复制粘贴至反向提示词框）：")
                lines.append("```text")
                lines.append(p["kling_negative"])
                lines.append("```")
                lines.append("")

                lines.append("##### ⚡ 方案 B：Runway Gen-3 / Luma Dream Machine / Sora 专属英文指令")
                lines.append("- **Positive Prompt** (Click to copy):")
                lines.append("```text")
                lines.append(p["runway_prompt"])
                lines.append("```")
                lines.append("- **Negative Prompt** (Paste into Runway negative prompt box):")
                lines.append("```text")
                lines.append(p["runway_negative"])
                lines.append("```")
                lines.append("")

                lines.append(f"**【第 5 步 · 生成下载与本地回传】**：")
                lines.append(f"- 平台生成完成后，点击下载 MP4；")
                lines.append(f"- 将文件重命名并放入本项目目录：`projects/{project_name}/assets/raw_video/{p['output_ai_name']}`")
                lines.append("")

            lines.append("---")
            lines.append("")

        lines.extend([
            "## 🚀 最终回流总装与交付 (Master Assembly & Final Delivery)",
            "",
            f"当你在 AI 视频平台生成完全部分镜片段，并存入 `projects/{project_name}/assets/raw_video/` 后，回到终端执行：",
            "",
            "```bash",
            f"python -m studio assemble --project projects/{project_name}",
            "```",
            "",
            "**工坊底层将全自动完成以下工序**：",
            "1. **视频自动接管**：自动优先加载 `assets/raw_video/` 中的电影级 AI 动态视频片段；",
            "2. **音画精确锁相**：将 AI 画面与本地打磨好的 **Edge-TTS / 真人声母带 WAV** 进行毫秒级对齐压制；",
            "3. **动态侧链混音**：施加广播级 Sidechain Ducking，人声开讲 BGM 自动压低至 12%，呼吸气口自然回弹至 25%；",
            f"4. **交付最终大片**：在 `projects/{project_name}/output/video/{project_name}_1080P_Final.mp4` 输出无水印超清成片！",
            "",
        ])

        return "\n".join(lines)
