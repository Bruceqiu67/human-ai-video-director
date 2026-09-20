# 全仓库审查报告（2026-09-20）

> **定位**：全仓库审查 + 同日修复对照。第 1–12 节保留审查当时的发现；**第 13 节写清做了什么、没做什么**。  
> **效力**：Issue 编号以本文为准。状态：`closed` = 已改代码/文档并用测试锁住；`open` = 本轮没做。  
> **复查**：`python tests/smoke_test.py` 全绿（约 5.15s，含 14 项契约 + 1 帧 FFmpeg 实渲）。

---

## 1. 审查结论

### 1.1 审查当时（修复前）

**仓库骨架能跑，冒烟测试通过，但 `studio` CLI 还不能当生产引擎用。**

《好帮手 AI 话术私教》竖屏成片已经交付（云希合规版约 68s），那条片子主要靠早期按幕手搓脚本（现已进 `archive/`）打磨出来。后来抽成的通用流水线 `studio/` 把「声音驱动画面、同底定格、胶囊字幕、单幕 QA」的骨架搭起来了，但关键链路有多处会直接做出**错片**或**错声**：

- BGM 侧链压缩接反，气口回弹音量从未生效。
- 故事板里的印章 / 荧光笔 / 脉冲 / 波形全部是死代码。
- 主画卷选图会选错姿态，缺图仍报成功并写出空白 MP4。
- 多句混音按句数衰减；幕尾 `tail_pad` 没有真正垫静音。
- Windows 上渲染存在 stderr 管道死锁风险；中文路径拼接可能失败。

六条工程红线在引擎里**大体守住**（没有逐句 `atempo`、没有人物正弦晃、没有文字区羽化）。真正的缺口是：**效果没接上、混音接反、选图不可靠、文档已过期。**

### 1.2 修复后（同日）

原审查 35 条 Issue **全部 closed**（代码或文档已改，契约测试锁住）。`studio` 可以按故事板做恒定语速配音、同底定格、已知 FX、风格化字幕、QA 帧、正确方向的 BGM 侧链。

它仍然**不能 1:1 复现**早期手搓的话术私教成片，也没有做五幕 1080p 重渲。未做清单见 [第 13 节](#13-做了的和没做的)。

---

## 2. 审查范围与方法

### 2.1 范围

| 区域 | 路径 | 是否深读 |
| :--- | :--- | :--- |
| 核心引擎 | `studio/engine/`（渲染、定格、字幕、转场、镜头、fx） | 是 |
| 声音 / CLI / 拼接 | `studio/cli.py`、`studio/audio/`、`studio/assembly/`、`studio/core/`、`studio/prompt/` | 是 |
| 风格 | `studio/styles/` | 是 |
| 模板与案例 | `templates/default_project/`、`examples/01_sales_coach_template/`、`examples/02_builder_efficiency_template/` | 是 |
| 规范文档 | `README.md`、`docs/`、`AI_VIDEO_PRODUCTION_SOP.md`、`UNIVERSAL_AI_VIDEO_BATCH_SOP.md`、`LESSONS_LEARNED_AND_RED_LINES.md`、`DEVELOPMENT_LOG.md`、Skill | 是 |
| 测试 | `tests/smoke_test.py`、`tests/setup_benchmark.py`、`tests/compare_benchmark.py` | 是 |
| 仓库卫生 | `.gitignore`、`git ls-files`、远程与体积 | 是 |
| 已忽略的本地大目录 | `素材/`、`output/`、`archive/`、`projects/` | 只核对职责，不把成片当引擎实现 |

`video_tools_ecosystem/` 作为配套军火库收录，本次不逐文件审 Remotion / 白板动画源码，只评估它对主仓库体积、宣传承诺和 gitignore 的影响。

### 2.2 方法

- 通读上述 Python / YAML / Markdown，按调用链核对「故事板 → TTS → manifest → 渲染 → 拼接 → ducking」。
- 对照六条工程红线（见 [`ENGINEERING_RED_LINES.md`](ENGINEERING_RED_LINES.md)）。
- 在本机运行 `python tests/smoke_test.py`（通过，约 2.9s）。
- 核对已跟踪文件数量与体积、远程地址、案例 manifest 是否与现行剧本同文。
- **没有**重新渲染 1080p 成片，也没有实机跑完整 `audio build` / `assemble`（避免改动工作区、消耗 TTS）。下列 FFmpeg 滤镜与 Windows 管道问题来自代码审阅，不是本次实机复现。

### 2.3 仓库快照

- 分支：`main`（与 `origin/main` 对齐，工作区干净）。
- 最近提交：`8fff48c feat: harden engine robustness, enforce privacy isolation, and deliver full smoke tests`。
- 远程：`https://github.com/Bruceqiu67/human-ai-video-director.git`。
- 已跟踪：1375 个文件，约 87.7 MB。
- 冒烟环境：`edge-tts 7.2.8`、`pillow 12.3.0`、`numpy 2.5.3`、`pyyaml 6.0.3`，本机 `ffmpeg` / `ffprobe` 在 PATH 中。

---

## 3. 项目实际在做什么

这是一套人机协同短视频流水线，主张：**骨骼与节奏用确定性工程锁死，灵魂与神态交给外部生图模型。**

默认规格：`1080×1920`、`30fps`、H.264 + AAC。默认美学：杂志折页手账风（米白 `#FAF7F2`、思源粗黑、荧光橙、朱红印章、纸片人白边定格）。

设计中的五步：

```text
storyboard.yaml
  → Edge-TTS 恒定语速 + timestamps_manifest.json
  → 导出四段式 Prompt，外部模型同底直出画卷
  → 单幕定格渲染 + QA 抽帧 + 末帧锚点
  → 无损拼接 + BGM 侧链闪避
```

对应 CLI：

```bash
python -m studio init my_project
python -m studio audio build --project my_project
python -m studio prompt generate --project my_project
python -m studio render --project my_project --scene 1
python -m studio assemble --project my_project
```

话术私教终版成片（本地、未进 git）：

- `output/video/好帮手AI话术私教_终极宣传大片_1080P.mp4`（云健版，约 57.5s）
- `output/video/好帮手AI话术私教_终极宣传大片_云希合规版.mp4`（云希版，约 68s，当前终版）

**不要默认「用现在的 `studio render` 能复现上述成片」。** 成片时代的印章坐标、荧光笔 bbox、合规补丁画卷，大量写在已归档的按幕脚本和私有 `素材/` 里。修复后通用引擎会画默认位置的 FX，**仍不是**那条片子的逐像素复刻（见 13.2）。

---

## 4. 工程红线核对

依据 [`ENGINEERING_RED_LINES.md`](ENGINEERING_RED_LINES.md) 与 [`LESSONS_LEARNED_AND_RED_LINES.md`](../LESSONS_LEARNED_AND_RED_LINES.md)。

| 红线 | 引擎现状（审查当时） | 判定（当时） | 修复后 |
| :--- | :--- | :--- |
| 1 绝不擅自合并总片 | 引擎只渲单幕；`assemble` 是独立命令，不做 QA 门禁 | 工序形式上成立，无强制验收闸 | 未改：CLI 仍不做人工 QA 闸 |
| 2 绝不逐句 `atempo` | `studio/audio/`、`studio/assembly/` 无 `atempo`；全局只有 Edge-TTS `rate` | 通过 | 仍通过 |
| 3 绝不切文字区羽化 | 翻页是硬裁切 + 折痕阴影，不是两张文字带 Alpha 融合 | 通过 | 仍通过 |
| 4 绝不人物正弦微晃 | `StopMotionSequencer` 只有离散跳切；波形/印章正弦未接到人物 | 通过（特效本身也没接到画面上） | FX 已接到画面，但不晃人物；徽章微转不算人物 |
| 5 字音同源 | 渲染字幕取自 manifest 的 `text`/`start`/`end` | **部分通过**：改 yaml 不重建音频时，不会对账，会静默用旧稿 | **已修**：渲染前对账，不一致则失败 |
| 6 必须输出 QA 帧 | 每幕写 `output/qa_frames/{scene_id}/` | **部分通过**：部分结束帧索引越界，长句中间帧未抽 | **已修**：夹紧索引 + 长句中点 |

SOP / README 里另外承诺的「讲话 12%、气口 25% 侧链闪避」「印章砸落 / 荧光笔扫」在**审查当时**代码做不到；修复后侧链与 FX 已接通，见第 13 节。翻页仍不是真 3D 卷边。

---

## 5. 问题清单（按严重度）

严重度约定：

- **bug**：正确性 / 安全 / 会直接做错片错声，或 CLI 静默改错项目。
- **suggestion**：可维护性、文档过期、测试缺口、体验，不修也能出片但会踩坑。
- **nit**：风格、未用导入、类型注解。

行号对应审查当时的 `main`（`8fff48c`）。每条末尾的 **状态 / 落地** 是同日修复后的结果（35/35 `closed`）。未做事项不在 Issue 编号里，见第 13.2 节。

### 5.1 Bug

#### Issue 1 — BGM 侧链把人声压掉了

- 文件：`studio/assembly/ducking_mixer.py:16-27`
- 现象：`idle_volume` 从 CLI 传入，滤镜图里从未引用。BGM 被写死 `volume={ducked_volume}`（默认 0.12）。
- 原因：FFmpeg `sidechaincompress` 第一路是被压的流、第二路是检测器。现图是 `[0:a][sc]sidechaincompress`，即用人声当被压流、BGM 当检测器。
- 后果：成片里人声被 BGM 压，BGM 永远约 12%，气口不会回弹到 25%。文档与 Skill 中的侧链描述全部不成立。
- 建议：BGM 先 `volume={idle_volume}`，再 `[bgm][0:a]sidechaincompress` 压 BGM；人声保持干声后 `amix`。人声也应 `aresample=44100`。测例应断言滤镜字符串里 `idle_volume` 出现，且 compress 的主输入是 BGM。
- **状态：closed（已修）**
- **落地：** `DuckingMixer.build_filter_complex` 使用 `[bgm][voice]sidechaincompress`，BGM `volume={idle_volume}`；契约测试 `test_ducking_filter_order`。

#### Issue 2 — 故事板 FX 全部未绘制

- 文件：`studio/engine/renderer.py:13-16`、`:216-236`
- 现象：导入了 `StampFX` / `MarkerFX` / `PulseFX` / `WaveformFX`；`AudioBuilder` 把 `seg["fx"]` 写入 manifest；模板声明了 `stamp_impact`、`score_stamp_impact`、`highlighter_sweep`、`click_pulse`、`waveform_equalizer`、`warning_badge_shake`、`camera_push`、`gold_light_sweep`。渲染循环从不读 `fx`，也从不调用 FX 类。
- 连带：`KenBurnsZoom.apply` 对每一幕每一帧都跑（`:225`），`camera_push` 无法做分段触发。
- 后果：CLI 重渲得到「跳切 + 字幕 + 全程缓推」，没有印章、荧光笔、波形、脉冲。与 SOP / 案例故事板合同不符。
- 建议：在定格层之后分发已知 `fx` 名；未知标签应报错。要么只在 `camera_push` 时缓推，要么删掉该标签并写明「全片 3% 呼吸推镜」。
- **状态：closed（已修，有意保留全幕缓推）**
- **落地：** 渲染循环分发 highlighter / pulse / waveform / stamp / badge / gold sweep；未知标签报错。`camera_push` 是已知标签，缓推仍按原 SOP 做全幕 1.00x→1.03x，**没有**改成按句开关（见 13.2）。

#### Issue 3 — 姿态选图会选错

- 文件：`studio/engine/renderer.py:107-116`
- 现象：对每个文件先看 `pose_name in fname`，否则看 `pose{idx+1}` / `pose_{idx+1}`，命中即 `break`。文件名含 `pose1` 但不含中文姿态名时，会抢在真正匹配的文件之前胜出。`os.listdir` 不排序。
- 实资产风险（`素材/04_分幕原生画卷/`，本地有、未进 git）：
  - Scene 02 姿态 `主管没空教` 可能先命中 `Scene02_破局重塑_Pose1_摆手安慰.jpg`，而不是 `Scene02A_破局共鸣_主管没空教.jpg`。
  - Scene 04 `耸肩错愕` 会同时命中原图和 `*_合规修补版.jpg`，先到先得，可能用未合规版。
  - 姿态字符串完全不在文件名里时，退回 `loaded_images[min(idx, len-1)]`，可能吃到「结尾最后一帧 / 底板 / 早期拼贴参考」。
- 建议：先全量按姿态名匹配；没有再匹配有边界的 `pose_N`；合规修补版优先；禁止把参考/结尾/底板当姿态；仍无匹配则失败，不要静默回退。
- **状态：closed（已修）**
- **落地：** `studio/engine/assets.py`；`test_pose_matching_scene_numbers`。

#### Issue 4 — 场景号子串会误吃其它幕

- 文件：`studio/engine/renderer.py:77`
- 现象：`scene_01` 抽出 `num_int="1"`，用 `"scene1" in filename`。`Scene10_*.jpg` 会被 Scene 1 收走。搜索目录还包括整个 `素材/04_分幕原生画卷/`（所有幕的图在同一层）。
- 建议：解析文件名开头的 `SceneNN` / `scene_NN`，数字必须相等。素材回退目录也按幕号过滤。排除文件名含「参考」「结尾」「底板」的条目，除非故事板显式指定。
- **状态：closed（已修）**
- **落地：** `filename_belongs_to_scene` 用 `scene[_-]?0*{n}(?!\d)`；排除参考/结尾/底板。

#### Issue 5 — 缺主画卷仍写出「成功」MP4

- 文件：`studio/engine/renderer.py:122-130`
- 现象：一张图都打不开时，打印 Notice，用风格底色铺满，继续写 `{scene_id}.mp4` 和锚点。损坏文件只 Warning（`:95`），最后同样走占位画布。
- 后果：CLI 报成功；`assemble` 把空白幕拼进总片。
- 建议：`loaded_images` 为空则 `FileNotFoundError`（或明确失败码）。不要对无法 QA 的占位图出片。
- **状态：closed（已修）**
- **落地：** 缺图 `FileNotFoundError`；`test_missing_masterframe_raises`。

#### Issue 6 — 渲染 FFmpeg stderr 管道可能死锁

- 文件：`studio/engine/renderer.py:202-262`
- 现象：`Popen(..., stdin=PIPE, stderr=PIPE)`，循环里只往 stdin 写 RGBA，直到 `finally` 才 `communicate()`。FFmpeg 默认把配置横幅和进度打到 stderr。Windows 匿名管道默认约 4KB。stderr 一满，FFmpeg 阻塞写日志，Python 阻塞写帧。
- 连带：`BrokenPipeError` 分支里已经 `communicate()`，`finally` 再调一次。
- 建议：`stderr=subprocess.DEVNULL` 或后台线程抽干 stderr；加 `-loglevel error`；`stdout=DEVNULL`；`communicate()` 只留一处。
- **状态：closed（已修）**
- **落地：** stderr 写 `ffmpeg_stderr.log`（文件不是 PIPE）；失败时读回日志。未在长片上压测死锁，64×64 实渲已通过。

#### Issue 7 — 多句人声按句数变轻

- 文件：`studio/audio/audio_builder.py:75-81`
- 现象：多段混音 `amix=inputs=N:dropout_transition=0`，默认 `normalize=1`。句子时间上并不重叠，FFmpeg 仍按 1/N 衰减。单句幕走另一支（无 amix，只 `volume=2.0dB`），比 3 句幕大约响 9.5dB（在同样 +2dB 补偿之前）。
- 建议：`amix=...:normalize=0`（FFmpeg 4.1+），或改 concat / acrossfade。保留 limiter。
- **状态：closed（已修）**
- **落地：** `AudioBuilder.build_mix_filter` 含 `normalize=0`；`test_amix_and_tail_pad_filter`。

#### Issue 8 — `tail_pad` 从未真正垫上

- 文件：`studio/audio/audio_builder.py:69-92`
- 现象：每句之后（包括最后一句）都 `cur_time = end_time + pause_between`，再 `scene_total_dur = cur_time + tail_pad`。混音命令用 `-t {scene_total_dur}` 且没有 `apad`。`-t` 只截不补；`adelay` 只垫开头。滤镜输出在最后一音素结束。manifest 写入的是 ffprobe 实测时长，渲染时钟跟这份时长走。
- 后果：yaml 里的幕尾留白、最后一次多余的句间停顿，都不会出现在 wav / MP4 里，末姿态在最后一个音素处被切掉。
- 建议：`pause_between` 只加在句子之间。滤镜末尾 `apad=pad_dur={tail_pad}`，再用 `-t` 锁住。manifest 存垫静音后的时长。
- **状态：closed（已修）**
- **落地：** 句间才加 pause；`apad=pad_dur`；manifest 用目标时长。未用真实 TTS 听感验收尾白。

#### Issue 9 — 字幕可能溢出画面

- 文件：`studio/engine/subtitles.py:53-70`
- 现象：字号降到 24 后最多对半拆一行。没有标点落在中间 30% 时，半行仍可能宽于 920px，`cap_x` 变负，画出画外。拆完不再二次测量、不再继续降号。逐字 `getlength` 之和也不等于整行 `getlength`。
- 建议：拆行后循环降号或贪心折行，直到每行 `getlength(line) <= max_width`。胶囊夹紧到 `[0, w) × [0, h)`。
- **状态：closed（已修）**
- **落地：** `AdaptiveCapsuleSubtitle` 贪心折行 + 夹紧；`test_subtitle_fits_and_uses_style_color`。

#### Issue 10 — `modern_tech` 字幕颜色未生效

- 文件：`studio/engine/subtitles.py:86-97`，`studio/engine/renderer.py:44-47`
- 现象：胶囊填色 `(24,24,27,205)`、文字白色写死。渲染器只把 `subtitle_font_size` / `subtitle_max_width` 传进去。`StyleProfile.subtitle_bg` / `subtitle_text` 以及科技风的海军蓝玻璃值从未使用。
- 后果：`style_preset: modern_tech` 的字幕仍是手账黑底白字。
- 建议：从 `self.style` 传入底色、字色、可选字体路径。
- **状态：closed（已修）**
- **落地：** 渲染器传入 `subtitle_bg` / `subtitle_text`。

#### Issue 11 — `-shortest` 让末帧锚点对不齐成片

- 文件：`studio/engine/renderer.py:149`、`:198`、`:264-266`
- 现象：视频帧数 `round(duration * fps)`，FFmpeg 加 `-shortest` 不加 `-t`。manifest 时长是 ffprobe 浮点，不必等于 `nframes/fps`。音频更短时，后几帧视频被丢掉，但 Python 仍把循环里的 `last_frame` 存成下一幕翻页锚点。QA JPEG 也可能含成片里没有的帧。
- 建议：音视频共用一个 `-t`；丢掉 `-shortest`。`total_frames` 与写 wav 时的 `-t` 同源，不要二次 ffprobe 再换算。
- **状态：closed（已修）**
- **落地：** 输出 `-t {duration}`，去掉 `-shortest`。

#### Issue 12 — 翻页锚点带缓推和字幕

- 文件：`studio/engine/renderer.py:264`
- 现象：锚点是 KenBurns 推到约 1.03×、且可能仍叠着字幕的合成帧。下一幕把它当 `prev_anchor_img`，自己的 KenBurns 从 1.0× 起。翻页时「翻出去的那页」已经放大，翻进来的页还没有。
- 建议：锚点只存定格层（未推镜、无字幕）。或明确让下一幕从 1.03× 接着推。
- **状态：closed（已修）**
- **落地：** 锚点 = 姿态 + FX，无 KenBurns、无字幕。

#### Issue 13 — `--project` 找不到时静默改用 cwd

- 文件：`studio/cli.py:26-48`
- 现象：`--project` 只是候选前缀；找不到就把 `cwd/storyboard.yaml` 追加进去。指到错误目录、或目录存在但没有 yaml 时，会加载**当前工作目录**的故事板，并改那个树。
- 建议：用户一旦写了 `--project`，只在该路径下找；找不到就 `FileNotFoundError`，禁止回退 cwd。
- **状态：closed（已修）**
- **落地：** `find_config_path`；`test_find_config_path_no_cwd_fallback`。

#### Issue 14 — 相对 BGM 路径相对的是 CWD

- 文件：`studio/cli.py:162-169`，`studio/core/config.py:31`
- 现象：`audio.bgm_file` 原样保存，`os.path.exists` 相对进程 CWD。yaml 写 `assets/bgm/track.mp3` 只在 cwd 恰好是项目根时有效。若字段非空但文件不存在，会跳过 `assets/bgm` 扫描，打印「No BGM」，出无配乐成片。
- 建议：相对路径一律 `join(project_dir, ...)`。配置了却找不到应报错，不要静默丢掉。目录扫描仅在字段为空时启用。
- **状态：closed（已修）**
- **落地：** `resolve_project_path`；配了找不到则报错；多 BGM 列出候选项。

#### Issue 15 — render 参数与退出码不符合文档

- 文件：`studio/cli.py:123-138`、`:213-216`
- 现象：
  1. `python -m studio render` 不带 `--scene` 打印提示后 **exit 0**。
  2. 位置参数只能是 `scene|all`，`render 1` / `render scene 1` 会被 argparse 拒绝。
  3. `--all` 优先于 `--scene`，`render --scene 2 --all` 仍渲全片。
- 建议：`-s` / `-a` 互斥且必填其一；缺参数 `sys.exit(1)`；允许把多余位置参数当成幕号。
- **状态：closed（已修）**
- **落地：** 缺幕号 exit 1；`--all` 与 `--scene` 互斥；`python -m studio render 1` 可用。

#### Issue 16 — Windows concat 列表可能读不出中文路径

- 文件：`studio/assembly/concatenator.py:15-19`
- 现象：concat demuxer 列表以 UTF-8 **无 BOM** 写入，路径写成 `file 'D:/video/视频3/...'`。FFmpeg 在 Windows 上常按系统 ANSI 代码页读这份列表。本仓库就在中文目录下。路径中的单引号也未按 demuxer 规则转义为 `'\''`。
- 建议：`encoding="utf-8-sig"`，或改 concat filter、输入走 argv。保留 `-safe 0`。
- **状态：closed（已修代码；未在中文路径上实跑 assemble）**
- **落地：** concat 列表 `utf-8-sig` + 单引号转义；`test_concat_list_bom_and_quotes`。**没做：** 用 `D:\video\视频3` 实跑一次 `assemble`。

#### Issue 17 — 空 yaml / 坏 json 抛出含糊异常

- 文件：`studio/core/config.py:47-57`，`studio/core/manifest.py:14-15`
- 现象：`yaml.safe_load` 结果不检查是否为 dict。空文件或 `scenes: null` 会在 `data.get` / `len(config.scenes)` 上变成 `AttributeError` / `TypeError`。无扩展名时先吞掉 YAML 异常再抛 JSON 异常，掩盖根因。
- 建议：加载后断言 dict；`scenes` 缺省才 `[]`，出现但不是 list 则报错。异常信息带上文件路径。
- **状态：closed（已修）**
- **落地：** `StoryboardConfig` 校验 mapping / 幕 id；`test_yaml_none_and_missing_id`。

#### Issue 18 — 字音同源只在「刚 build 完」时成立

- 文件：`studio/engine/renderer.py:143-147`，`studio/audio/audio_builder.py:53-61`、`:98-107`
- 现象：渲染只读 manifest，不和当前 yaml 的 `dialogue_segments` 对 `text` / `pose` / id。改剧本但不重建音频，字幕和姿态仍是旧快照。`build_all` 从空 dict 开始，**全部幕成功才 `save()`**：第 3 幕失败时，第 1–2 幕 wav 已是新的，json 仍是旧文件或缺失。
- 建议：渲染（及 assemble）断言 manifest 文本与 yaml 一致。每幕成功后立刻写 json。考虑 `audio build --scene`。
- **状态：closed（已修）**
- **落地：** `assert_matches_storyboard`；每幕音频成功即写 json；`audio build --scene`。

### 5.2 Suggestion

#### Issue 19 — QA 帧索引会丢掉句尾

- 文件：`studio/engine/renderer.py:204-207`
- 说明：`int(seg["end"] * fps)` 截断，最后一句结束帧常等于 `total_frames`，落在 `range` 外被跳过。翻页被跳过时仍插入翻页时刻。长句中间帧未抽（红线 6 要求动作切换 + 长句）。
- 建议：夹紧到 `[0, total_frames-1]`；与 `total_frames` 同一套取整；时长超过阈值时加中点帧。
- **状态：closed（已修）**
- **落地：** QA 索引夹紧；长句抽中点；无翻页不抽翻页帧。

#### Issue 20 — 字幕坐标写死 1080×1920

- 文件：`studio/styles/base.py:19-20`
- 说明：`subtitle_max_width=920`、`subtitle_y=1680`。故事板允许改 `resolution`。720×1280 时字幕会画到画外。
- 建议：默认用分辨率比例（例如 `y = 0.875h`，`max_width = 0.85w`）。
- **状态：closed（已修）**
- **落地：** `StyleProfile.subtitle_layout`。

#### Issue 21 — 翻页阴影在末期会涂到下一页

- 文件：`studio/engine/transitions.py:32-42`
- 说明：折痕阴影带宽 `min(48, 5%w)`，`fold_x` 小于带宽时 `shadow_x` 夹到 0，渐变仍按 48px 画到新页上。`ImageFilter` 导入未使用。硬裁切本身不违反红线 3。
- 建议：阴影宽度取 `min(shadow_w, fold_x)`。删未用导入。
- **状态：closed（已修）**
- **落地：** 阴影宽 `min(..., fold_x)`；去掉未用 `ImageFilter`。翻页仍不是 3D 卷边（13.2）。

#### Issue 22 — 定格区间闭区间、未排序

- 文件：`studio/engine/stopmotion.py:19-27`
- 说明：`start <= t <= end`，先命中先得。正常有 `pause_between` 时句间保持上一姿态、无字幕，这是对的。手改 manifest 重叠时，前一句会一直占着。`preceding[-1]` 依赖列表顺序而不是 `max(end)`。
- 建议：用 `[start, end)`；取最后一个 `start <= t` 的片段；缺键要防护；初始化时按 `start` 排序。
- **状态：closed（已修）**
- **落地：** `[start, end)`；按 `start` 排序；`test_stopmotion_half_open_interval`。

#### Issue 23 — KenBurns 偶像素与奇数分辨率

- 文件：`studio/engine/camera.py:18-27`，`studio/engine/renderer.py:195`
- 说明：`crop_w = int(w/scale)` 后居中可能偏 1px。`progress<=0` 原样返回不 copy，若调用方漏了 `.copy()`，后续字幕 `paste` 会改缓存姿态。奇数分辨率会让 `yuv420p` 在帧写完后才被 FFmpeg 拒绝。
- 建议：early-return 也 copy；奇数边长在 Popen 前拒绝。
- **状态：closed（已修）**
- **落地：** KenBurns 始终 copy；奇数分辨率直接失败。

#### Issue 24 — FX 模块就地 mutate，且尚未被调用

- 文件：`studio/engine/fx/stamp.py:44` 及 marker / pulse / waveform
- 说明：`canvas.paste` 改传入对象。bbox 颠倒时 marker 半径为负。Pulse 导入 `math` 未用。Waveform 的 sin/cos 是均衡器，不是人物晃（不触发红线 4）。Issue 2 修好后，若渲染器漏 copy，会污染共享姿态图。
- 建议：合成到副本上；校验 bbox；删未用导入。
- **状态：closed（已修）**
- **落地：** 各 FX `canvas.copy()`；颠倒 bbox 会交换坐标。

#### Issue 25 — 未知风格名静默变手账风

- 文件：`studio/styles/__init__.py:11`
- 说明：`journal-scrapbook`、拼写错误会落到 `JournalScrapbookStyle`。yaml `style_preset: null` 会在 `.lower()` 上炸。
- 建议：未知名 `ValueError` 并列出注册表；`None` 显式当默认。
- **状态：closed（已修）**
- **落地：** 未知风格报错；`journal-scrapbook` 可解析。

#### Issue 26 — Prompt 写死嘉彬外形与手账纸底

- 文件：`studio/prompt/prompt_builder.py:40-51`
- 说明：无论 `style_preset` 是什么，提示词都是米白网格纸 +「黑框眼镜、黑色圆领 T 的东亚青年」。通用脚手架无法为其它产品换角色或换科技风。
- 建议：角色描述与纸底/科技底从风格配置和故事板读取，不要写死第一部片子的出镜人。
- **状态：closed（已修）**
- **落地：** `project.character.prompt` + 风格背景段；`test_prompt_not_locked_to_black_tshirt`。案例目录里已生成的 `MASTER_PROMPTS.md` 未重导（13.2）。

#### Issue 27 — `init` 脚手架不完整

- 文件：`studio/cli.py:50-110`
- 说明：只复制 `storyboard.yaml`，不复制 `templates/default_project/README.md`。内嵌 fallback yaml 缺少 ducking 字段和完整 5 幕。没有 ffmpeg/ffprobe 预检，下一步 `audio build` 会甩原始 `FileNotFoundError`。
- 建议：整树复制模板；fallback 与模板键对齐；`init` 时探测 ffmpeg。
- **状态：closed（已修）**
- **落地：** `shutil.copytree` 复制 `templates/default_project`；缺 ffmpeg 时 Warning。

#### Issue 28 — 空台词仍会送进 TTS

- 文件：`studio/audio/tts_engine.py:11`，`studio/audio/audio_builder.py:40`
- 说明：空白 `text` 仍合成；`silenceremove` 可能得到 ~0s 片段，混音仍成功，manifest 记零时长字幕。
- 建议：空文本直接失败；trim 后拒绝过短 duration。
- **状态：closed（已修）**
- **落地：** `TTSEngine` 拒绝空白；trim 后过短失败；`test_empty_tts_text`。

#### Issue 29 — ffmpeg 子进程未关 stdin

- 文件：`studio/audio/audio_builder.py:89` 等
- 说明：除渲染管线外，其它 ffmpeg 调用未 `stdin=DEVNULL` / `-nostdin`。CLI 一旦被管道喂数据，FFmpeg 可能偷走 stdin。缺二进制时是 `FileNotFoundError`，与其它路径的 `RuntimeError` 形状不一致。
- 建议：统一 `stdin=DEVNULL`；PATH 预检；错误信息带 stderr。
- **状态：closed（已修）**
- **落地：** `studio/core/proc.py` 默认 `stdin=DEVNULL`；`require_ffmpeg()`。

#### Issue 30 — 引擎几乎没有行为测试

- 文件：`tests/smoke_test.py`
- 说明：只测依赖、import、加载模板、Prompt 字符串、`--help`。不测选图、缺资产、ducking 方向、`tail_pad`、concat 编码、`--project` 回退、yaml 与 manifest 同文。`packaging` 被 import 但未写入 `requirements.txt`。
- 建议：用极小 RGBA 夹具测选图与缺图失败；对滤镜字符串做单测（不必真跑 ffmpeg）；`requirements.txt` 加上 `packaging`（若保留 pytest 入口则加上 pytest）。
- **状态：closed（已修）**
- **落地：** `tests/test_pipeline_contracts.py` 14 项，挂进冒烟 Phase 6；`packaging` 写入 requirements。未把 pytest 本身列入 requirements（本机可用 `python tests/smoke_test.py`）。

#### Issue 31 — 基准脚本写死本机绝对路径

- 文件：`tests/setup_benchmark.py`、`tests/compare_benchmark.py`
- 说明：路径写死 `d:\video\视频3\...`。`setup_benchmark` 把 `output/audio/manifest_yunxi.json`（列表结构）转成 studio 的 dict 结构，并把 `素材/04` 全部图拷进同一 `masterframes/`，会放大 Issue 3/4 的选图错误。
- 建议：改相对仓库根路径；或标明「仅本机对照，不作为 CI」。
- **状态：closed（已修）**
- **落地：** 相对仓库根；缺本地成片时明确报错。仍是本机对照工具，不是 CI。

#### Issue 32 — numpy 未使用

- 文件：`requirements.txt:4`
- 说明：`studio/` 没有任何 `import numpy`。依赖声明与引擎不符。
- 建议：从核心 requirements 移除，或真的用到再留。
- **状态：closed（已修）**
- **落地：** 已从 `requirements.txt` 去掉 numpy。

### 5.3 Nit

#### Issue 33 — 未用导入与锚点缩放不一致

- 文件：`studio/engine/renderer.py:2`、`:173`
- 说明：`import glob` 未用。上一幕锚点 resize 用 PIL 默认滤镜，主画卷用 LANCZOS。`scene_id` 若含 `..` 或绝对路径，输出路径可以逃出 `output/video/`（本地可信 yaml，不是网络入口）。
- 建议：删 `glob`；锚点也 LANCZOS；`scene_id` 限制为 `[\w\-]+`。
- **状态：closed（已修）**
- **落地：** 去掉 glob；锚点 LANCZOS；id 禁止 `..` / 路径分隔符。

#### Issue 34 — 缺 id 的幕 wav 与 manifest 键不一致

- 文件：`studio/audio/audio_builder.py:22` vs `:101`
- 说明：`build_scene_audio` 缺 id 时默认 `scene_01`，`build_all` 用 `sc.get("id", "")` 当 manifest 键。渲染按 `scene_01` 去找，对不上。两个无 id 幕会覆盖同一 wav。
- 建议：配置加载时强制非空 `id`。
- **状态：closed（已修）**
- **落地：** 加载期强制非空 `id`。

#### Issue 35 — concat 失败时临时列表已被删

- 文件：`studio/assembly/concatenator.py:31-34`
- 说明：先删 `concat_list.tmp.txt` 再看 returncode，失败无法打开列表排查。多首 BGM 时 `os.listdir` 先到先用。
- 建议：`finally` 里删；失败先打出路径。多 BGM 且未指定时列出候选项并报错。
- **状态：closed（已修）**
- **落地：** concat 失败保留 tmp 列表；多 BGM 未指定则报错列出。

---

## 6. 文档、合规与宣传承诺

### 6.1 SOP 已过期，且含合规风险文案

审查当时 [`AI_VIDEO_PRODUCTION_SOP.md`](../AI_VIDEO_PRODUCTION_SOP.md) 自称「新对话只需读本文即可 100% 无损继承」，与终版冲突。

| 审查时 SOP 仍写 | 终版 / 现行模板 | 修复后 |
| :--- | :--- | :--- |
| 开篇 `atempo=1.15~1.20` | 后文与红线禁止逐句 `atempo` | **已改**开篇为全局 `rate`，禁止逐句 atempo |
| 声线仅 `zh-CN-YunjianNeural` | 终版与 `examples/01` 为 Yunxi | **已改**默认 Yunxi，Yunjian 作备选 |
| 第四幕「800元续保补贴」 | 数据支撑 / 90%同到期车主 | **已改** SOP 台词；开发日志阶段十一的事故记录**故意保留** |

### 6.2 宣传了但引擎没有的能力

| 承诺 | 审查当时 | 修复后 |
| :--- | :--- | :--- |
| BGM 讲话 12%、气口回弹 25% | 滤镜接反（Issue 1） | **已修**滤镜方向；未用成片听感验收 |
| 印章 / 荧光笔 / 波形 / 脉冲 | 模块在，渲染未调用（Issue 2） | **已接通**默认 bbox；未对齐私有画卷坐标 |
| 2.5D 物理卷边翻书 | 硬擦除 + 折痕阴影 | **没做**真 3D 卷边 |
| 剪映 / CapCut 草稿双交付 | CLI 不生成工程 | **已改文档**承认 CLI 不导出；**没做**剪映导出 |
| 7 步交互式向导 | Skill 有，CLI 无状态机 | **没做**对话状态机 |
| HyperFrames 无缝集成 | 仅文档示例 | **没做**封装 |
| README 克隆 `your-username/...` | 与远程不符 | **已改**为 `Bruceqiu67/human-ai-video-director` |

### 6.3 案例与模板内部不一致

- 案例 README rate `+20%` vs yaml `+18%`：**已改** README 为 `+18%`。
- 已跟踪的过期 `examples/01/.../audio/timestamps_manifest.json`：**已删文件**。
- Prompt 写死嘉彬：**生成器已改**为 `character.prompt`；案例里现成的 `MASTER_PROMPTS.md` **未重导**。

### 6.4 本地第二项目

`projects/builder_efficiency/` 按通用 SOP 脚手架建过：音频母带齐，`04_Video_Scenes/` 空。整个 `projects/` 被 gitignore，克隆仓库的人看不见。这是本地草稿，不是开源案例。

---

## 7. 测试现状

### 7.1 审查当时

`python tests/smoke_test.py` **全部通过**（约 2.9s）：依赖、import、模板 yaml、Prompt、CLI `--help`。第 5 节多数 bug **测不到**。`packaging` 未写入 requirements。

### 7.2 修复后

`python tests/smoke_test.py` **全部通过**（约 5.15s）：

1. 依赖：`edge-tts` / `pillow` / `pyyaml` / `packaging`（已写入 requirements，去掉未用 numpy）。
2. 全模块 import，0 警告。
3. 模板 yaml 与 PromptBuilder 4 幕截断。
4. CLI `--help` 六条退出码 0。
5. **Phase 6 契约 14/14**：选图、Scene10 误伤、缺图失败、ducking 方向、`apad`/`normalize=0`、concat BOM、`--project` 回退、yaml 空根、风格色、manifest 对账、字幕折行、定格区间、空 TTS、**64×64 FFmpeg 实渲**。

**修复后仍未跑：** 完整 Edge-TTS 五幕、1080p 话术私教重渲、中文路径上实机 `assemble`。

---

## 8. 仓库卫生与隐私

### 8.1 gitignore 做对的部分

下列目录/类型被忽略，克隆方拿不到企业成片和真人底图：

- `素材/`、`output/`、`BGM/`、`projects/`、`archive/`
- `*.mp4` / `*.wav` / `*.mp3` 等音视频
- `*剧本*.md`、`*旁白*.md`

这与 README「物理级隔离私有音视频」一致。

### 8.2 仍偏大的已跟踪内容

已跟踪约 **87.7 MB / 1375 文件**，大头在 `video_tools_ecosystem/companion_skills/`：

- `anything2explainer/template/public/fonts/NotoSansSC.ttf` ≈ 17.4 MB
- 多份 cut-director / 白板动画 GIF、示例 png
- 至少一份已跟踪 mp4（gitignore 的 `*.mp4` 管不住**已经入库**的文件）

`examples/01/.../audio/timestamps_manifest.json` 审查时属于「规则会忽略、但已经在索引里」；**修复时已删除该文件**。`video_tools_ecosystem/` 大二进制 **本轮未减肥**。

### 8.3 README 目录树

根 README 审查时未列 `tests/`、真实 GitHub 用户名。**修复后**已补 `tests/` 与克隆地址；剪映双交付改成「CLI 不生成工程」。

---

## 9. 经核对、不作为缺陷的项

- `studio/audio` 与 `studio/assembly` **没有**逐句 `atempo`。全局 `rate="+18%"~"+20%"` 不算红线 2 违规。
- 子进程均为 argv 列表，无 `shell=True`。残留风险是 concat 引号（Issue 16）和未消毒的 `scene_id` 文件名（Issue 33）。
- 第一幕 `transition: none`、缺上一幕锚点：打印 Notice 并跳过翻页，不崩溃。
- 空 `segments` 时定格器退回 `default_img`（但缺图出片仍是 Issue 5）。
- 默认 1080×1920 为偶数，满足 `yuv420p`。
- 句间 `pause_between`：画面保持上一姿态、字幕关闭，符合「声音驱动画面」。
- `studio/__main__.py` 与各包 `__init__.py` 无循环导入；CLI UTF-8 reconfigure 对 Windows 控制台是对的。
- 红线 1 的「用户确认后再 assemble」是流程约定，CLI 无法代替人工 QA；不单独开 bug，只要求不要在 Agent 向导里跳过单幕验收。

---

## 10. 建议修复顺序（审查当时的计划）

审查当时只排序、不改代码。**同日已按 1–7 执行**（对应 Issue 1–35 全部 closed）。第 8 项仓库减肥 **没做**，见 13.2。

1. **声音能听**：Issue 1 → 7 → 8。**已做。**
2. **画面选对**：Issue 5 → 3、4 → 18。**已做。**
3. **效果真做**：Issue 2 → 6 → 11、12。**已做**（FX 用默认坐标，不是成片逐像素）。
4. **CLI 别改错项目**：Issue 13、14、15、16。**已做**（16 未实机 assemble）。
5. **字幕与风格**：Issue 9、10、20、26。**已做。**
6. **文档与合规**：SOP 声线/800 元、README 克隆、剪映承诺、过期 manifest。**已做。**
7. **测试**：契约测试覆盖 1–8、13、18 等。**已做。**
8. **仓库减肥**（可选）：companion_skills 改 submodule / LFS。**没做。**

---

## 11. 与其它文档的关系

| 文档 | 关系 |
| :--- | :--- |
| [`ONBOARDING_GUIDE.md`](ONBOARDING_GUIDE.md) | 7 步操作。ducking 数值审查时未兑现，**修复后滤镜已接通**；阶段 7 已改为「CLI 不生成剪映工程」。 |
| [`ENGINEERING_RED_LINES.md`](ENGINEERING_RED_LINES.md) | 红线原文。符合度见表第 4 节（含修复后列）。 |
| [`../LESSONS_LEARNED_AND_RED_LINES.md`](../LESSONS_LEARNED_AND_RED_LINES.md) | 第一幕复盘。引擎仍无人物正弦晃和文字羽化。 |
| [`../AI_VIDEO_PRODUCTION_SOP.md`](../AI_VIDEO_PRODUCTION_SOP.md) | 开篇声线/atempo/800 元**已改**；分幕过程表里若仍写 Yunjian，以 `examples/01` yaml 为准。 |
| [`../DEVELOPMENT_LOG.md`](../DEVELOPMENT_LOG.md) | 演进史。阶段十一合规事故记录保留；阶段十三为本次修复。 |

---

## 12. 审查当日未做的事（修复前快照）

审查写文档时：

- 未改任何源代码、yaml、gitignore 或成片。
- 未重新 TTS、未重新渲染、未重新 assemble。
- 未在干净虚拟环境里复现「缺 packaging 则冒烟失败」。
- 未用本机 `D:\video\视频3` 实跑 concat。
- 未逐文件审查 `video_tools_ecosystem/companion_skills/` 内部实现。

同日后续会话已改代码并复查。对照以第 13 节为准。

---

## 13. 做了的和没做的

### 13.1 做了的

**引擎 / 声音 / CLI（对应 Issue 1–35，均为 closed）**

- 侧链改为压 BGM、人声干声；`idle_volume` 进滤镜；`amix normalize=0`；`apad` 落实 `tail_pad`；句间才加 pause。
- 选图按幕号锚定、姿态名优先、合规修补版优先；缺主画卷失败；Scene1 不再误吃 Scene10。
- 渲染分发已知 FX；stderr 改写日志文件；输出 `-t` 对齐时长；锚点不带缓推/字幕。
- 字幕折行夹紧、吃风格色、随分辨率缩放；科技风不再画手账黑胶囊。
- `--project` 禁止回退 cwd；BGM 相对项目根；`render` 缺参数 exit 1；concat UTF-8 BOM。
- yaml/manifest 对账；每幕音频成功即写 json；`audio build --scene`。
- Prompt 不再写死嘉彬黑 T；`init` 整树复制模板；空台词拒绝 TTS；ffmpeg PATH 预检。

**测试**

- 新增 `tests/test_pipeline_contracts.py`（14 项），挂进冒烟 Phase 6。
- `packaging` 写入 requirements，去掉未用 numpy。
- 基准脚本改为相对仓库根。
- `python tests/smoke_test.py` 全绿，约 5.15s，含 64×64 FFmpeg 实渲。

**文档**

- SOP：禁止逐句 atempo、默认 Yunxi、第四幕去掉 800 元续保补贴。
- README：真实克隆地址、声明 CLI 不导出剪映、目录树补 `tests/`。
- Onboarding 阶段 7、案例 README 语速、删除过期 `timestamps_manifest.json`。
- 开发日志阶段十三。

### 13.2 没做的

这些**有意没做**，或只改了文档/默认实现、没有验收到成片级：

| 未做 | 说明 |
| :--- | :--- |
| 话术私教五幕 1080p 重渲 | 没有跑完整 Edge-TTS，没有用私有 `素材/` 重出成片。契约测试用静音 wav + 色块 PNG。 |
| 成片逐像素复刻 | FX 的印章/荧光笔/徽章是 1080×1920 通用默认坐标，没有吃分层切片的真实 bbox。 |
| `camera_push` 按句开关 | 标签识别了，缓推仍是全幕呼吸（跟原 SOP 1.00x→1.03x）。 |
| 真 3D 卷边翻书 | 仍是硬裁切 + 折痕阴影。 |
| 剪映 / CapCut 工程导出 | 只改了文档，CLI 仍然不生成草稿。 |
| 7 步对话向导状态机 | Skill 文本还在，没有做成 CLI 向导。 |
| HyperFrames 封装 | 仍只有文档命令示例。 |
| Windows 中文路径实机 `assemble` | 列表已写 BOM，没有在 `D:\video\视频3` 上跑通拼接。 |
| 成片听感验收 ducking | 滤镜字符串测过，没有听完整带 BGM 的终片。 |
| 干净 venv 验证 packaging | 本机已有 packaging；没重建空白环境。 |
| 重导案例 `MASTER_PROMPTS.md` | 生成器改了，examples 里那份旧提示词文件没重新导出。 |
| `video_tools_ecosystem/` 减肥 | 约 87MB 字体/GIF 仍在 git 里。 |
| 开发日志里的「800元」字样 | 阶段十一事故记录**故意保留**，不是现行台词。 |
| `projects/builder_efficiency/` | 仍是本地 gitignore 草稿，视频目录仍空。 |
| companion_skills 逐文件审查 | 审查范围本来就排除。 |

### 13.3 若继续做，建议顺序

1. 故事板 FX 增加可选 `bbox` / `pos`，对齐真实画卷。
2. 在本机中文路径上实跑 `assemble`。
3. 需要时再 TTS + 1080p 重渲做听感/画面验收。
4. companion_skills 大二进制改 submodule 或 Git LFS。
