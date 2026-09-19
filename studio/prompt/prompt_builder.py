import os
from studio.core.config import StoryboardConfig

class PromptBuilder:
    """Generates standardized 4-section In-Context Prompts for Grok/Midjourney/Gemini."""
    
    def __init__(self, config: StoryboardConfig):
        self.config = config
        self.project_dir = config.project_dir
        
    def generate_markdown(self) -> str:
        lines = [
            f"# 《{self.config.title}》大模型同底画卷标准提示词矩阵",
            "## (Master Prompts for Model-Native In-Context Conditioning)",
            "",
            "> [!IMPORTANT]",
            "> **生图核心铁律 (The In-Context Non-Negotiables)**：",
            "> 1. **母版基底严格锁定**：背景网格纸纹/纯色折痕、装订阴影、左侧信息便签卡片、顶部标题文字 100% 保持印刷级原位；",
            "> 2. **同底同质多姿态直出**：严禁在代码中对文字卡片进行切片或渐变羽化！第二张、第三张图片以第一张母版作为图生图参考图，仅要求大模型置换右侧人物肢体动作与面部表情；",
            "> 3. **人物轮廓锁定**：人物边缘带 15px 纯白剪纸撕边轮廓，带柔和投射阴影，与背景浑然一体。",
            "",
            "---",
            ""
        ]
        
        for idx, sc in enumerate(self.config.scenes, 1):
            sc_id = sc.get("id", f"scene_{idx:02d}")
            stage_tag = sc.get("stage_tag", f"STAGE {idx:02d}")
            headline = sc.get("headline", "")
            segments = sc.get("dialogue_segments", [])
            
            lines.append(f"## 🎨 Scene {idx:02d}：{stage_tag}")
            lines.append(f"**核心主标题**：`{headline}`")
            lines.append("")
            
            # Masterframe prompt (Pose 1)
            first_pose = segments[0].get("pose", "标准出镜姿态") if segments else "出镜讲解"
            lines.append("### 画面 1（主母版画卷 · 初始姿态）")
            lines.append("```markdown")
            lines.append("9:16 vertical (1080x1920), professional stationery journal scrapbook collage aesthetic, paper cutout style.")
            lines.append("")
            lines.append("【Background & Layout Lock】:")
            lines.append("- Warm off-white textured grid kraft paper background (#FAF7F2), vertical bookbinding crease with subtle soft center shadow, faint technical grid ruler lines, sleek silver mechanical pencil lying diagonally at the bottom left corner.")
            lines.append(f"- Top header typography: Small subtitle '{stage_tag}' in uppercase bold sans-serif, bold headline '{headline}' in clean Song/Hei print black ink.")
            lines.append("- Left side sticky note card: Off-white textured post-it note with tape at top, handwritten keynotes summarizing core topic.")
            lines.append("")
            lines.append("【Character & Pose】:")
            lines.append("- On the right side, an East Asian young presenter (neat black hair, rectangular glasses, clean black crewneck t-shirt).")
            lines.append("- Character silhouette has a crisp, precise 15px pure white sticker paper-cut outline with a soft natural drop shadow cast onto the background paper.")
            lines.append(f"- Initial Pose: {first_pose}.")
            lines.append("- Seamless paper collage lighting, sharp graphic vector details, 8k resolution, no blurred seams.")
            lines.append("```")
            lines.append("")
            
            # Variant poses (Poses 2..N)
            for p_idx, seg in enumerate(segments[1:], 2):
                pose_desc = seg.get("pose", f"姿态 {p_idx}")
                lines.append(f"### 画面 {p_idx}（同底置换姿态 {p_idx}）")
                lines.append("```markdown")
                lines.append(f"[Reference: Use Scene {idx:02d} Masterframe as primary image reference]")
                lines.append(f"Maintain 100% identical background grid, left sticky note card, top headline '{headline}', and pencil position.")
                lines.append("Replace ONLY the right-side character pose and facial expression:")
                lines.append(f"- Target Pose: {pose_desc}.")
                lines.append("- Keep exact same character identity, glasses, black t-shirt, and crisp 15px white cutout border.")
                lines.append("```")
                lines.append("")
                
            lines.append("---")
            lines.append("")
            
        return "\n".join(lines)
        
    def export(self, output_file: str = "") -> str:
        target = output_file or os.path.join(self.project_dir, "MASTER_PROMPTS.md")
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        content = self.generate_markdown()
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Master prompts exported to: {target}")
        return target
