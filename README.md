# 🎬 human-ai-video-director
### 人机协同全流程 AI 短视频工业化制作工坊 (Human-AI Hybrid Video Studio)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Edge-TTS](https://img.shields.io/badge/TTS-Edge--TTS-brightgreen.svg)](https://github.com/rany2/edge-tts)
[![FFmpeg](https://img.shields.io/badge/Render-FFmpeg-red.svg)](https://ffmpeg.org/)
[![Architecture](https://img.shields.io/badge/Architecture-In--Context%20Conditioning-orange.svg)](#️-整体架构与流水线-architecture)

> **“骨骼与节奏归确定性工程，灵魂与神态归生成式 AI。”**
>
> 告别纯代码硬搓假人立牌的生硬塑料感，告别纯大模型生视频的汉字乱码与界面形变。
> 本项目将**大模型同底同质直出 (In-Context Conditioning)** 与 **参数化定格动画流水线 (Python/FFmpeg/Remotion/HyperFrames/剪映)** 深度咬合，实现高完播率、印刷级质感与极高交付确定性的短视频批量生产。

---

## 🌟 核心特色 (Key Highlights)

- 🚀 **保姆级 7 步交互式向导**：搭载专用 Agent Skill，小白用户只需输入想法，AI 自动完成从 5 幕剧本拆解、声音工程、Prompt 矩阵到成片输出的全套工序。
- 🎯 **单一真理源 (Single Source of Truth)**：以结构化 `storyboard.yaml` 统领全片分幕、台词、姿态与动效，字幕与发音波形毫秒级绝对同源。
- 🎨 **风格解耦系统 (Style Decoupling)**：默认内置**经典杂志手账风**（米白暖调纸底 `#FAF7F2` + 思源粗黑排版 + 荧光橙马克笔），并支持一键换装为**现代科技 SaaS 风**或自定义品牌调性。
- 🗣️ **广播级声音工程**：微软高拟真语音（云希/云健/晓晓），严格坚持自然恒定语速直出（0% 逐句 atempo 变速），配合呼吸气口设计与 BGM 动态侧链闪避（Sidechain Ducking）。
- 🖼️ **同底同质多姿态直出**：四段式生图指令锁死排版与文字，仅置换右侧出镜人物姿态表情，彻底根除代码羽化拼接带来的文字错位与重影。
- ⚡ **代码级动效矩阵**：2.5D 物理卷边翻书、实体定格瞬切（Jump Cut）、复古印章下砸震颤、自适应防溢出胶囊字幕与呼吸微距缓推。
- 🧰 **全套视频工具箱生态**：内置剪映/CapCut 桌面自动化 MCP 协议，并收录 **5 大顶级开源配套 Skills**（白板流墨动画、黑底科技科普、157+ 镜头配方、火柴人叙事、蜡笔手绘）。

---

## 🏗️ 整体架构与流水线 (Architecture)

```
                            [ 用户创意 / 需求 ]
                                     │
                                     ▼
      ┌─────────────────────────────────────────────────────────────┐
      │  Stage 1: 灵魂定调 (Concept & Script)                        │
      │  - 黄金 5 幕结构拆解 (Hook ➔ Solution ➔ Simulation ➔ CTA)   │
      │  - 产出单一真理源: storyboard.yaml                          │
      └──────────────────────────────┬──────────────────────────────┘
                                     │
                                     ▼
      ┌─────────────────────────────────────────────────────────────┐
      │  Stage 2: 声音工程与时间锚定 (Audio Engineering)            │
      │  - Edge-TTS 恒定自然语速直出 (Yunxi/Yunjian)               │
      │  - 毫秒级时间戳清单: timestamps_manifest.json (时间锚点锁死) │
      └──────────────────────────────┬──────────────────────────────┘
                                     │
                                     ▼
      ┌─────────────────────────────────────────────────────────────┐
      │  Stage 3: 同底画卷生图矩阵 (In-Context Prompt Matrix)        │
      │  - 导出 MASTER_PROMPTS.md (版面100%像素级锁定)              │
      │  - 用户在外部工具 (Grok/MJ/Gemini) 3分钟出图放入 masterframes │
      └──────────────────────────────┬──────────────────────────────┘
                                     │
                                     ▼
      ┌─────────────────────────────────────────────────────────────┐
      │  Stage 4: 模块化定格渲染与状态锚定 (Modular Render Engine)    │
      │  - 2.5D 物理翻书 + 实体定格瞬切 + 自适应居中防溢出胶囊字幕     │
      │  - 单幕独立成片交付 + 抽取 QA 走查帧 + 保存末帧作为下一幕锚点  │
      └──────────────────────────────┬──────────────────────────────┘
                                     │
                                     ▼
      ┌─────────────────────────────────────────────────────────────┐
      │  Stage 5: 全片大汇编与智能混音 (Master Assembly)            │
      │  - 无损拼接全片 + BGM 侧链动态闪避 (开讲降至12%, 停顿回弹至25%)│
      │  - 输出 1080P/30fps 广播级成品 MP4（剪映工程需另走 ChatCut MCP）│
      └─────────────────────────────────────────────────────────────┘
```

---

## ⚡ 极速上手 (Quick Start)

### 1. 环境准备
```bash
# 克隆本仓库
git clone https://github.com/Bruceqiu67/human-ai-video-director.git
cd human-ai-video-director

# 安装 Python 依赖
pip install -r requirements.txt

# 确保系统已安装 FFmpeg 并且在 PATH 环境变量中可用
ffmpeg -version
```

### 2. 初始化新项目
```bash
# 一键生成标准脚手架与分镜剧本模板
python -m studio init my_project
```

### 3. 一键构建声音母带与时间戳清单
```bash
# 自动生成各幕母带 WAV 与毫秒级时间戳 manifest
python -m studio audio build --project my_project
```

### 4. 导出大模型提示词矩阵并在外部生图
```bash
# 导出包含四段式同底直出指令的 MASTER_PROMPTS.md
python -m studio prompt generate --project my_project
```
*将生成的原画放入 `my_project/assets/masterframes/` 目录。*

### 5. 单幕渲染与 QA 走查
```bash
# 独立渲染第一幕成片并自动提取关键帧走查
python -m studio render --project my_project --scene 1
```

### 6. 全片无缝拼接与 BGM 动态闪避混音
```bash
# 自动汇聚所有验收通过的分幕成片，应用侧链压缩混音
python -m studio assemble --project my_project
```

---

## 🧰 视频制作工具箱生态 (`video_tools_ecosystem/`)

本项目打包了完整的周边开源视频创作军火库，位于 `video_tools_ecosystem/` 目录：

| 工具/技能名称 | 原开源项目仓库链接 | 核心特色与适用场景 |
| :--- | :--- | :--- |
| **`mcp_chatcut_desktop`** | 内置 MCP 协议中枢 | **剪映 / CapCut 桌面端自动化**：60 个原子工具直接操控本地剪辑轨道 |
| **`srt-whiteboard-animation`** | [geeklee/srt-whiteboard-animation](https://github.com/geeklee/srt-whiteboard-animation) | **暖白纸流墨手绘白板动画**：仿真实体笔触与知识点手绘涂鸦 |
| **`anything2explainer`** | [Vincentwei1021/anything2explainer](https://github.com/Vincentwei1021/anything2explainer) | **黑底极简科技感讲解视频**：图灵宇宙风格，硬核算法与代码讲解 |
| **`video-shotcraft`** | [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | **157+ 镜头配方卡与 2.5D 动效分镜工坊**：Remotion 视觉动效全家桶 |
| **`stickman-video-director`** | [kaomei/stickman-video-director](https://github.com/kaomei/stickman-video-director) | **火柴人叙事视频导演**：极低美术成本的幽默故事科普 |
| **`hand-drawn-video-prompts`** | [kaomei/hand-drawn-video-prompts](https://github.com/kaomei/hand-drawn-video-prompts) | **暖白底 Q 版蜡笔手绘 9:16 分镜**：高亲和力生活与职场指南 |
| **`cut-director`** | 内置实用 Skill | **口播切气口与画中画视觉导演**：真人视频智能切除停顿并弹出产品 UI |
| **`ffmpeg-video-editor`** | 内置实用 Skill | **FFmpeg 命令行高保真剪切转码工具** |
| **`yh-tools-video2srt`** | 内置实用 Skill | **离线/在线智能音视频提取字幕与时间戳** |

---

## ⚡ HyperFrames 代码动效集成

当项目需要 WebGL、3D 手机壳悬浮翻转或复杂交互录屏动效时，可无缝结合 **HyperFrames**：

```bash
# 全局安装 HyperFrames CLI
npm install -g hyperframes

# 语法合规检查
npx hyperframes check ./my_hyperframes_project

# 交互式时间轴预览
npx hyperframes preview ./my_hyperframes_project

# 高保真导出
npx hyperframes render ./my_hyperframes_project -o ./output/video.mp4
```

---

## 🛑 六大不可逾越工程红线 (The 6 Non-Negotiables)

1. **【绝不擅自合并总片】**：单幕必须独立交付，经 QA 抽帧验收满意后方可推进下一幕。
2. **【绝不逐句强行变速】**：严禁在单句上使用 `atempo` 强拉硬拽，声音自然流淌，画面适配声音。
3. **【绝不切文字区做羽化】**：严禁在带有文字、卡片的区域做代码羽化拼合，100% 同底整页直出。
4. **【绝不添加代码正弦微晃】**：严禁人物正弦晃动、骨骼扭动，坚守实体定格抽帧瞬切（Jump Cut）。
5. **【字音毫秒同源绝对对应】**：字幕文本与配音文本单一真理源，由配音实际波形起止点驱动。
6. **【必须输出 QA 关键帧走查】**：自动抽取动作切换点与转场帧，肉眼复核无重影后方可汇报交付。

---

## 📁 目录规范 (Repository Layout)

```text
human-ai-video-director/
├── .gemini/skills/human-ai-video-director/   # Agent 核心 Skill (含全流程向导)
├── studio/                                  # 核心 Python 模块化流水线引擎
├── video_tools_ecosystem/                    # 全套视频制作工具箱生态 (MCP + 8大Skills)
├── templates/default_project/               # 标准空白脚手架模版
├── examples/                                # 纯文本实战案例模板 (零大文件)
├── docs/                                    # 开发者与使用手册（含全量审查报告）
├── tests/                                   # 冒烟测试与流水线契约测试
├── requirements.txt                         # 依赖清册
├── .gitignore                               # 物理级隔离私有音视频大文件
└── README.md                                # 项目主页
```

---

## 📄 开源许可证 (License)

本项目遵循 [MIT License](LICENSE) 协议开源。
