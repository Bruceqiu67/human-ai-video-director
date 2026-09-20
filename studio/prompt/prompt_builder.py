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
            "> 1. **母版基底严格锁定**：背景底板、机位角度、环境光影、标题文字 100% 保持原位；",
            "> 2. **【🛑 机位与三脚架绝对锁死 (Rigid Tripod & Coordinate Lock)】**：同一幕内的所有姿态（pose_1, pose_2...）必须保持 100% 同一摄像机机位、同一焦距、同一背景环境与同一主体屏幕坐标 (x, y)。严禁在同一幕内随意换背景、换桌面、换机位！",
            "> 3. **局部增量微姿态演进 (Delta Pose Shift)**：后续姿态以第一张母版为参考，严禁全图重绘，推荐使用 Midjourney 局部重绘（Vary Region）或低降噪图生图（Denoise 0.35~0.45），仅置换人物/产品的表情与肢体动作；",
            "> 4. **质感与轮廓锁定**：与风格描述严格一致，光照阴影投射稳定，消除画面跳脱与穿帮。",
            "",
            "---",
            "",
        ]
        bg_lines = self.style.prompt_background_lines()
        character = self.config.character_prompt
        silhouette = self.style.prompt_character_lock()
        is_journal = self.style.name == "journal_scrapbook"
        aesthetic = (
            "professional stationery journal scrapbook collage aesthetic, paper cutout style"
            if is_journal
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
            lines.append("### 画面 1（主母版画卷 · 初始姿态 · 锁定三脚架机位）")
            lines.append("```markdown")
            lines.append(f"9:16 vertical (1080x1920), {aesthetic}.")
            lines.append("")
            lines.append("【Background & Layout Lock】:")
            lines.extend(bg_lines)
            lines.append(
                f"- Top header typography: Small subtitle '{stage_tag}' in uppercase bold sans-serif, "
                f"bold headline '{headline}'."
            )
            if is_journal:
                lines.append("- Left side information card summarizing the core topic of this scene.")
                lines.append(f"- On the right side: {character}.")
            else:
                lines.append(f"- Scene center / hero subject: {character}.")
            lines.append("")

            user_assets_dir = os.path.join(self.project_dir, "assets", "user_assets")
            if os.path.isdir(user_assets_dir):
                user_asset_files = [
                    f for f in sorted(os.listdir(user_assets_dir))
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg"))
                ]
                if user_asset_files:
                    asset_list = ", ".join(f"`assets/user_assets/{f}`" for f in user_asset_files)
                    lines.append("【User Assets & Brand Fidelity (垫图与物料注入)】:")
                    lines.append(f"- Dedicated user assets detected: {asset_list}.")
                    lines.append("- Upload these assets as image conditioning (--cref / --sref / ControlNet) to maintain exact 1:1 brand identity.")
                    lines.append("")

            lines.append("【Character & Pose】:")
            lines.append(f"- {silhouette}")
            lines.append(f"- Initial Pose: {first_pose}.")
            lines.append("- Camera: LOCKED RIGID TRIPOD, stable eye-level perspective, no Dutch angle.")
            lines.append("- Sharp graphic details, no blurred seams, no extra watermarks.")
            lines.append("```")
            lines.append("")

            for p_idx, seg in enumerate(segments[1:], 2):
                pose_desc = seg.get("pose", f"姿态 {p_idx}")
                lines.append(f"### 画面 {p_idx}（同底微动姿态 {p_idx} · 绝对同机位增量置换）")
                lines.append("```markdown")
                lines.append(f"[🛑 STOP-MOTION TRIPOD LOCK & DELTA POSE]:")
                lines.append(f"- Reference: Use Scene {idx:02d} Masterframe 1 as primary image reference (--cref / inpainting).")
                lines.append(f"- Camera Rig: 100% LOCKED TRIPOD. Exact same camera focal length, angle, and distance.")
                lines.append(f"- Environment & Desk: 100% IDENTICAL background, lighting, and surrounding objects. DO NOT re-generate or alter the desk.")
                lines.append(f"- Character Coordinate: Retain exact screen coordinates (x, y) and body scale.")
                lines.append(f"- Incremental Micro-Pose: ONLY change expression or micro-action: {pose_desc}.")
                lines.append(f"- Character Identity: {silhouette}")
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
