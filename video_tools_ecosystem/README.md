# 🎬 视频制作工具箱生态与配套军火库 (Video Tools Ecosystem)

欢迎来到 **human-ai-video-director** 配套的 AI 视频创作工具箱生态！

本目录汇集并打包了我们在工业化短视频生产全流程中验证过的顶级开源工具、桌面剪辑控制协议（MCP）与配套视觉导演 Skills。无论是真人出镜、知识科普、代码动画、白板手绘还是火柴人幽默短剧，你都可以在这里找到最佳工具支持。

---

## 🛠️ 一、 桌面自动化控制中枢 (`mcp_chatcut_desktop/`)

- **定位**：连接 AI Agent 与 **剪映 / CapCut 桌面客户端** 的双向通信中枢。
- **核心能力**：内置 **60 个原子工具 Schema** 与最佳实践说明（`instructions.md`），支持：
  - `create_project` / `edit_project`：直接生成剪映标准本地草稿工程（JianYing Drafts）；
  - `edit_track` / `edit_item` / `split_item`：毫秒级操控时间线、切气口、贴画中画、对齐音轨；
  - `create_motion_graphic_from_code`：将前端代码生成的动态 MG 视效无缝塞入剪辑时间线；
  - `local_export`：调用剪映本地引擎静默导出成品视频。
- **详情参阅**：[mcp_chatcut_desktop/README.md](mcp_chatcut_desktop/README.md)

---

## 🌟 二、 精选配套开源 Skills 矩阵 (`companion_skills/`)

本目录收录了社区 5 大顶尖视频制作 Skills 以及实战中常用的实用工具：

### 1. `srt-whiteboard-animation` (暖白纸流墨手绘白板动画)
- **GitHub 官方源**：[geeklee/srt-whiteboard-animation](https://github.com/geeklee/srt-whiteboard-animation)
- **美学特征**：暖白底网格纸、仿真运笔手势（`drawing-hand.png`）、随音频字幕逐字流墨书写、简笔涂鸦动态绘制。
- **协同场景**：可在手账风视频中作为**手绘便签生长、核心知识点手写划线**的高级视觉发生器。

### 2. `anything2explainer` (黑底极简科技感讲解视频)
- **GitHub 官方源**：[Vincentwei1021/anything2explainer](https://github.com/Vincentwei1021/anything2explainer)
- **美学特征**：对标“图灵宇宙”风格的科普白描 MG 视频。深黑深邃底色、星光点阵波、纯白矢量线图元、巨大数据看板与顶部章节进度条。
- **协同场景**：当需要制作**硬核底层原理剖析、复杂架构连线、大模型/算法讲解**时的首选代码动画引擎。

### 3. `video-shotcraft` (157+ 镜头配方卡与 2.5D 动效分镜工坊)
- **GitHub 官方源**：[Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft)
- **美学特征**：基于 Remotion 的视觉特效配方百科全书。涵盖发牌式入场、2.5D 手机外框、实时音频波形律动、聚光灯扫掠、打字机展开等 **157+ 张工业级配方卡**。
- **协同场景**：为短视频中的转场过渡、UI卡片弹出提供现成的代码动画参考与纹理素材。

### 4. `stickman-video-director` (火柴人叙事视频导演)
- **GitHub 官方源**：[kaomei/stickman-video-director](https://github.com/kaomei/stickman-video-director)
- **美学特征**：基于 SVG 与极简黑白线条的小火柴人定格叙事。
- **协同场景**：零美术门槛的趣味自嘲、痛点吐槽短剧，适合轻量级爆款自媒体创作。

### 5. `hand-drawn-video-prompts` (暖白底 Q 版蜡笔手绘 9:16 分镜)
- **GitHub 官方源**：[kaomei/hand-drawn-video-prompts](https://github.com/kaomei/hand-drawn-video-prompts)
- **美学特征**：9:16 竖屏暖白底、高饱和蜡笔涂鸦、Q版大头人物与童趣手账排版。
- **协同场景**：生活类、女性向、职场新人避坑指南等高亲和力知识科普。

---

## 🔧 三、 实战辅助工具集

- **`cut-director`**：专为真人出镜口播打造的视觉导演，智能切除说话停顿气口，并在重点词处弹窗出画中画与数据卡片；
- **`ffmpeg-video-editor`**：涵盖硬件加速无损拼接、侧链动态闪避混音与高保真转码的底层原子脚本；
- **`yh-tools-video2srt`**：开箱即用的离线/在线智能音视频提取字幕与毫秒级时间戳工具。

---

## 💡 如何在项目中调用这些工具？

1. **主流水线调度**：日常使用建议以项目根目录的 `studio` CLI 和 `human-ai-video-director` Skill 为总指挥；
2. **多风格切换**：当你想要更换视频风格时，可直接参考 `companion_skills` 中对应 Skill 的剧本模板与提示词规范；
3. **剪映二次精修**：成片导出后，可通过 `mcp_chatcut_desktop` 自动生成剪映工程，实现所见即所得的鼠标拖拽微调。
