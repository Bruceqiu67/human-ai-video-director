# 🚀 新人从 0 到 1 导演级操作手册 (Full-Lifecycle Onboarding Guide)

欢迎来到 **human-ai-video-director** 工业化视频流水线！无论你是初学者、独立开发者还是自媒体博主，本手册教你如何以“总导演思维”与 AI 协同，快速做出高品质专属短视频。

---

## 阶段 1：导演前置问诊（定调三要素）

在新建任何项目或写剧本前，必须先明确四大核心要素：
1. **产品用途与受众**：
   - 这个视频是做什么的？（电商种草、软件演示、品牌故事、硬核教程还是解压搞笑？）
   - 观众是谁？（年轻打工人、学生、技术极客、商务决策者？）
2. **时长与幕数节奏**：
   - **10s ~ 15s 微短片 / 极速卡点**：适配 **2 ~ 3 幕**（痛点觉醒 ➔ 核心亮相 ➔ 立即行动）；
   - **30s ~ 45s 中短视频 / 功能拆解**：适配 **3 ~ 4 幕**（痛点 ➔ 破局 ➔ 实操 ➔ 升华）；
   - **50s ~ 65s 深度干货 / 标杆大片**：适配 **黄金 5 幕**（痛点 ➔ 破局 ➔ 对战 ➔ 诊断 ➔ 升华）；
3. **视觉风格与转场**：
   - `modern_tech`（现代科技 SaaS 风）：深空暗夜蓝底 (`#0F172A`)、赛博霓虹蓝、半透明深色玻璃拟态胶囊字幕；
   - `journal_scrapbook`（经典杂志手账风）：暖米白网格纸底 (`#FAF7F2`)、书脊折痕阴影、思源粗黑排版；
   - 转场选择：干净硬切（`transition: none`，利落卡点主流）还是 2.5D 手账折痕翻书（`transition: page_flip`）；
4. **出镜形象**：真实真人肖像、3D 拟人萌物角色、或是纯产品物料卡片。

---

## 阶段 2：剧本定制与故事板初始化

1. 打开终端，初始化项目：
   ```bash
   python -m studio init my_cool_video
   ```
2. 打开生成的 `my_cool_video/storyboard.yaml` 文件：
   - 将 `style_preset` 设定为你选定的风格（如 `modern_tech` 或 `journal_scrapbook`）；
   - 根据规划的幕数填写每幕的标题、台词（单句建议 10~22 字）与姿态；
   - 设定配音音色（如 `zh-CN-YunxiNeural` 阳光青年男声，或 `zh-CN-YunjianNeural` 沉稳专家男声）。

---

## 阶段 3：备物料（极简准备）
根据你的剧本需求准备 1 张基准图：
- 真实自拍、证件照，或是 AI 生成的角色/产品基准图（用于锁定外观、服饰或产品材质特征）。

---

## 阶段 4：锁节奏（一键生成声音母带）
运行命令：
```bash
python -m studio audio build --project my_cool_video
```
- 系统自动调用微软 Edge-TTS 高保真语音引擎；
- 自动剔除头尾杂音，通过 `apad` 真正补齐 `tail_pad` 留白；
- 导出 `audio/timestamps_manifest.json` 毫秒级时间戳清单；
- ⚠️ **红线原则**：全片时长由声音自然流淌决定，严禁逐句 atempo 强行变速，画面绝对服从声音！

---

## 阶段 5：生画卷（3 分钟导出大模型同底画卷）
1. 运行命令导出提示词：
   ```bash
   python -m studio prompt generate --project my_cool_video
   ```
2. 打开生成的 `my_cool_video/MASTER_PROMPTS.md`：
   - 复制四段式提示词至 Grok / Midjourney / Gemini；
   - 锁定第一张母版的背景与排版，后续姿态仅置换右侧动作表情；
   - 将生成的画卷放入 `my_cool_video/assets/masterframes/`。

---

## 阶段 6：跑单幕（单幕渲染与 5 秒走查）
运行命令渲染单幕或全量：
```bash
python -m studio render --project my_cool_video --scene 1
# 或全量渲染所有幕：
python -m studio render --project my_cool_video --all
```
- 自动渲染出 `output/video/scene_01.mp4`；
- 自动实装印章、荧光笔、脉冲等动态特效；
- 自动提取关键帧存入 `output/qa_frames/scene_01/` 供 5 秒快速走查；
- 自动保存纯净末帧作为下一幕翻页底板。

---

## 阶段 7：BGM 选型推荐与侧链动态汇流

1. **总导演提供 BGM 画像**：
   - 根据视频调性（如“轻快解压”、“科技硬核”、“热血卡点”），确定 BPM 节拍（如 120 BPM）与情绪关键词；
2. **用户挑选并放入**：
   - 在剪映曲库、网易云、QQ音乐或免版权曲库中挑选中意音轨，下载后重命名放入 `my_cool_video/assets/bgm/`；
3. **汇流合成**：
   ```bash
   python -m studio assemble --project my_cool_video
   ```
   - 自动无损拼接各幕；
   - 施加广播级动态侧链闪避：人声讲话时 BGM 自动压低至 12%，呼吸气口自然回弹至 25%。

---

## 阶段 8：交付成片与二次精修
- `output/video/<project>_1080P_Final.mp4` 即为无水印成片，可直接分发发布；
- 需要轨道级细微调优时，可配合本项目内置的 `video_tools_ecosystem/mcp_chatcut_desktop` MCP 协议，无头驱动剪映桌面客户端进行轨道编辑。
