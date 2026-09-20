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
        return CinematicPromptEngine.generate_full_sop_markdown(self.config)

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
