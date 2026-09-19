# 🚀 新人从 0 到 1 保姆级操作手册 (Full-Lifecycle Onboarding Guide)

欢迎来到 **human-ai-video-director** 工业化视频流水线！无论你是初学者、独立开发者还是自媒体博主，只要跟着以下 7 步走，就能快速做出广播级质感的专属短视频。

---

## 阶段 1：定内容（灵魂定调）
1. 打开终端，运行：
   ```bash
   python -m studio init my_cool_video
   ```
2. 打开生成的 `my_cool_video/storyboard.yaml` 文件：
   - 填写视频标题与项目名；
   - 按照 **黄金 5 幕公式** 填写每幕的核心主标题与台词（每句建议 12~25 字，全片控制在 50~65 秒）；
   - 设定你喜欢的配音音色（如 `zh-CN-YunxiNeural` 阳光青年男声，或 `zh-CN-YunjianNeural` 沉稳专家男声）。

---

## 阶段 2：备物料（极简准备）
你只需要准备 **1 张人物基准图**：
- 你的清晰生活照、证件照，或者 AI 生成的虚拟角色（用于锁定发型、脸型、眼镜和服装风格）。
- 将该图放在你的电脑桌面上，稍后生图时作为参考图。

---

## 阶段 3：锁节奏（一键生成声音母带）
运行命令：
```bash
python -m studio audio build --project my_cool_video
```
- 系统将自动调用微软 Edge-TTS 高保真语音引擎；
- 自动掐头去尾剔除多余静音，注入自然呼吸气口；
- 导出 `audio/timestamps_manifest.json` 时间戳清单。
- ⚠️ **红线原则**：全片时长由声音自然流动决定，严禁随意变速，画面绝对服从声音！

---

## 阶段 4：生画卷（3 分钟导出大模型同底画卷）
1. 运行命令导出提示词：
   ```bash
   python -m studio prompt generate --project my_cool_video
   ```
2. 打开生成的 `my_cool_video/MASTER_PROMPTS.md`：
   - 复制里面的四段式提示词；
   - 打开 Grok / Midjourney / Gemini，粘贴指令；
   - **核心技巧**：第一张作为母版，后续姿态图以第一张为参考，锁定文字卡片与背景网格，仅置换右侧人物动作表情；
   - 将生成的图片重命名为 `scene_01_pose1.jpg`, `scene_01_pose2.jpg` 等，拖入 `my_cool_video/assets/masterframes/`。

---

## 阶段 5：跑单幕（单幕渲染与 5 秒走查）
运行命令渲染单幕：
```bash
python -m studio render --project my_cool_video --scene 1
```
- 系统会自动渲染出 `output/video/scene_01.mp4`；
- 自动提取关键帧存入 `output/qa_frames/scene_01/`；
- 打开图片检查：文字有无错位？人物是否利落跳切？胶囊字幕是否居中防溢出？
- 自动保存最后一帧作为下一幕翻页底板。确认满意后，继续渲染下一幕！

---

## 阶段 6：总汇聚（全片拼接与 BGM 侧链动态闪避）
当 5 幕全部渲染验收通过后，运行：
```bash
python -m studio assemble --project my_cool_video
```
- 自动无损拼接 5 幕成片；
- 自动挂载背景音乐，施加侧链动态闪避：人声开讲时 BGM 自动平滑压低至 12%，呼吸停顿时自然回弹至 25%。

---

## 阶段 7：双交付（成片或剪映二次微调）
- `output/video/my_cool_video_1080P_Final.mp4` 即为无水印成品，可直接发布；
- 若需微调，可通过 `video_tools_ecosystem/mcp_chatcut_desktop` 自动生成剪映草稿工程，在剪映客户端用鼠标拖拽调整。
