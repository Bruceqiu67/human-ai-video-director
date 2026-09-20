"""Four-section in-context prompts; style and character come from the storyboard."""

from __future__ import annotations

import os

from studio.core.config import StoryboardConfig
from studio.styles import get_style


class PromptBuilder:
    """Generates standardized In-Context Prompts for Grok/Midjourney/Gemini."""

    def __init__(self, config: StoryboardConfig):
        self.config = config
        self.project_dir = config.project_dir
        self.style = get_style(config.style_preset)

    def generate_markdown(self) -> str:
        lines = [
            f"# 《{self.config.title}》大模型同底画卷标准提示词矩阵",
            "## (Master Prompts for Model-Native In-Context Conditioning)",
            "",
            "> [!IMPORTANT]",
            "> **生图核心铁律 (The In-Context Non-Negotiables)**：",
            "> 1. **母版基底严格锁定**：背景、装订阴影、左侧信息卡、顶部标题文字 100% 保持印刷级原位；",
            "> 2. **同底同质多姿态直出**：严禁在代码中对文字卡片进行切片或渐变羽化；后续姿态以第一张母版为参考，仅置换人物动作与表情；",
            "> 3. **人物轮廓锁定**：与风格描述一致的剪纸/描边轮廓，带柔和投射阴影。",
            "",
            "---",
            "",
        ]
        bg_lines = self.style.prompt_background_lines()
        character = self.config.character_prompt
        silhouette = self.style.prompt_character_lock()
        aesthetic = (
            "professional stationery journal scrapbook collage aesthetic, paper cutout style"
            if self.style.name == "journal_scrapbook"
            else "modern dark SaaS HUD collage, glass cards, cyan grid, no kraft paper"
        )

        for idx, sc in enumerate(self.config.scenes, 1):
            stage_tag = sc.get("stage_tag", f"STAGE {idx:02d}")
            headline = sc.get("headline", "")
            segments = sc.get("dialogue_segments", [])
            first_pose = segments[0].get("pose", "标准出镜姿态") if segments else "出镜讲解"

            lines.append(f"## Scene {idx:02d}：{stage_tag}")
            lines.append(f"**核心主标题**：`{headline}`")
            lines.append("")
            lines.append("### 画面 1（主母版画卷 · 初始姿态）")
            lines.append("```markdown")
            lines.append(f"9:16 vertical (1080x1920), {aesthetic}.")
            lines.append("")
            lines.append("【Background & Layout Lock】:")
            lines.extend(bg_lines)
            lines.append(
                f"- Top header typography: Small subtitle '{stage_tag}' in uppercase bold sans-serif, "
                f"bold headline '{headline}'."
            )
            lines.append("- Left side information card summarizing the core topic of this scene.")
            lines.append("")
            lines.append("【Character & Pose】:")
            lines.append(f"- On the right side: {character}.")
            lines.append(f"- {silhouette}")
            lines.append(f"- Initial Pose: {first_pose}.")
            lines.append("- Sharp graphic details, no blurred seams, no extra watermarks.")
            lines.append("```")
            lines.append("")

            for p_idx, seg in enumerate(segments[1:], 2):
                pose_desc = seg.get("pose", f"姿态 {p_idx}")
                lines.append(f"### 画面 {p_idx}（同底置换姿态 {p_idx}）")
                lines.append("```markdown")
                lines.append(f"[Reference: Use Scene {idx:02d} Masterframe as primary image reference]")
                lines.append(
                    f"Maintain 100% identical background, left information card, top headline '{headline}'."
                )
                lines.append("Replace ONLY the right-side character pose and facial expression:")
                lines.append(f"- Target Pose: {pose_desc}.")
                lines.append(f"- Keep the same character identity. {silhouette}")
                lines.append("```")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Append Part 2: Cinematic Video Directing Prompts
        lines.append(self.generate_cinematic_markdown())
        return "\n".join(lines)

    def generate_cinematic_markdown(self) -> str:
        from studio.prompt.cinematic import CinematicPromptEngine

        lines = [
            f"# 🎥 《{self.config.title}》大模型图生视频/文生视频专业运镜指令",
            "## (Cinematic Video Directing Prompts for Kling / Runway / Luma / Sora / Minimax)",
            "",
            "> [!TIP]",
            "> **AI 视频运镜指令四大铁律 (The Directing Golden Rules)**：",
            "> 1. **Camera First (运镜指令前置)**：视频模型对首句机位权重最高，必须先写运镜轨迹，再写动作；",
            "> 2. **One-Move Rule (一镜一动原则)**：单个 3~5 秒镜头严禁复合乱转，只专注一种平滑机位运动；",
            "> 3. **Camera vs. Subject (相机与主体分离)**：镜头运动（Dolly/Pan/Orbit）与物体动作（Squish/Nod）严格分开；",
            "> 4. **首帧图生视频 (I2V Mode)**：将生成的 `assets/masterframes/` 作为首帧输入可灵/Runway，直接复制下方对应指令。",
            "",
            "---",
            "",
        ]

        total_scenes = len(self.config.scenes)
        for idx, sc in enumerate(self.config.scenes, 1):
            stage_tag = sc.get("stage_tag", f"STAGE {idx:02d}")
            headline = sc.get("headline", "")
            segments = sc.get("dialogue_segments", [])
            prompts = CinematicPromptEngine.generate_scene_video_prompts(
                idx, stage_tag, headline, segments, total_scenes, self.config.character_prompt
            )

            lines.append(f"## 🎬 分镜 Scene {idx:02d}：{stage_tag}（{headline}）")
            lines.append("")

            for p in prompts:
                lines.append(f"### 镜头 {idx}.{p['pose_idx']}：{p['pose']}（预估时长: {p['duration']}）")
                lines.append(f"- **台词旁白**：*{p['dialogue']}*")
                lines.append(f"- **推荐运镜模式**：`{p['motion_type']}`")
                lines.append("")
                lines.append("#### 🌟 方案 A：可灵 AI (Kling 3.0 / 快手可灵) 专属指令")
                lines.append("```text")
                lines.append(p["kling_prompt"])
                lines.append("```")
                lines.append("")
                lines.append("#### ⚡ 方案 B：Runway Gen-3 / Luma Dream Machine / Sora 专属指令 (English Pro)")
                lines.append("```text")
                lines.append(p["runway_prompt"])
                lines.append("```")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def export(self, output_file: str = "") -> str:
        target = output_file or os.path.join(self.project_dir, "MASTER_PROMPTS.md")
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        content = self.generate_markdown()
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(content)
        print(f"Master prompts exported to: {target}")

        # Also export standalone cinematic prompts for quick access
        cinematic_target = os.path.join(self.project_dir, "CINEMATIC_VIDEO_PROMPTS.md")
        with open(cinematic_target, "w", encoding="utf-8") as handle:
            handle.write(self.generate_cinematic_markdown())
        print(f"Cinematic video directing prompts exported to: {cinematic_target}")

        return target
