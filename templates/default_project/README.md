# 🚀 新视频项目脚手架 (New Project Scaffold)

本项目为基于 **human-ai-video-director** 工业化视频流水线创建的标准工程。

## 快速上手 4 步流水线：

```bash
# 1. 声音工程母带生成与时间戳标定 (基于 Edge-TTS，导出 timestamps_manifest.json)
python -m studio audio build

# 2. 生成大模型同底多姿态生图提示词 (导出 MASTER_PROMPTS.md)
python -m studio prompt generate

# 3. 将外部工具 (Grok / Midjourney) 生成的原图放入 assets/masterframes/，并渲染单幕成片与 QA 走查
python -m studio render --scene 1

# 4. 全幕走查通过后，全片无损拼接与 BGM 侧链动态闪避混音
python -m studio assemble
```

## 目录结构说明：
- `storyboard.yaml`：全案台词、分幕时间轴与动效指令的唯一真理源。
- `assets/masterframes/`：存放同底大模型生成的无文字错位原画切片（`scene_01_pose1.jpg` 等）。
- `assets/anchors/`：自动截取保存的各幕最后一帧，用于下一幕 2.5D 物理翻页转场。
- `assets/bgm/`：存放背景音乐。
- `audio/`：生成的旁白音频母带与时间戳清册。
- `output/video/`：导出的单幕与全片 MP4。
- `output/qa_frames/`：自动抽取的质检走查关键帧。
