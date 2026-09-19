# FFmpeg Filter Reference

Complete reference for commonly used FFmpeg video and audio filters.
Apply with `-vf "filter"` (video), `-af "filter"` (audio), or `-filter_complex "..."` (multi-stream).

---

## Video Filters

### scale — Resize Video

```
scale=width:height[:flags]
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `width` / `height` | pixels or `-1` / `-2` | `-2` = auto (divisible by 2) |
| `force_original_aspect_ratio` | `disable`, `decrease`, `increase` | Letterbox/pillarbox mode |
| `flags` | `bilinear`, `bicubic`, `lanczos` | Scaling algorithm |

```bash
# Scale to 1280 wide, auto height (div by 2)
ffmpeg -i in.mp4 -vf "scale=1280:-2" out.mp4

# Letterbox to 1920×1080
ffmpeg -i in.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,\
pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black" out.mp4

# Scale using expression
ffmpeg -i in.mp4 -vf "scale=iw/2:ih/2" out.mp4
```

---

### crop — Crop Video

```
crop=width:height:x:y
```

```bash
# Crop 640×360 at offset (100, 50)
ffmpeg -i in.mp4 -vf "crop=640:360:100:50" out.mp4

# Center crop to square
ffmpeg -i in.mp4 -vf "crop=min(iw\,ih):min(iw\,ih)" out.mp4

# Crop to 16:9 from 4:3
ffmpeg -i in.mp4 -vf "crop=ih*16/9:ih" out.mp4

# Crop bottom 20%
ffmpeg -i in.mp4 -vf "crop=iw:ih*0.8:0:0" out.mp4
```

---

### pad — Add Padding / Letterbox

```
pad=width:height:x:y[:color]
```

```bash
# Pillarbox 4:3 → 16:9
ffmpeg -i in.mp4 -vf "pad=iw*16/9:ih:(ow-iw)/2:0:black" out.mp4

# Add 10px white border
ffmpeg -i in.mp4 -vf "pad=iw+20:ih+20:10:10:white" out.mp4
```

---

### overlay — Composite Two Videos

```
overlay=x:y[:format][:eval]
```

```bash
# Watermark bottom-right, 10px margin
ffmpeg -i video.mp4 -i logo.png \
  -filter_complex "[0:v][1:v]overlay=W-w-10:H-h-10" out.mp4

# Semi-transparent overlay
ffmpeg -i bg.mp4 -i fg.png \
  -filter_complex "[1:v]format=rgba,colorchannelmixer=aa=0.5[fg];\
[0:v][fg]overlay=0:0" out.mp4

# Time-limited overlay (show logo 5–15s)
ffmpeg -i video.mp4 -i logo.png \
  -filter_complex "[0:v][1:v]overlay=10:10:enable='between(t,5,15)'" out.mp4
```

---

### drawtext — Render Text on Video

```
drawtext=text='...':fontfile=...:fontsize=...:fontcolor=...:x=...:y=...
```

| Parameter | Description |
|-----------|-------------|
| `text` | Static text string |
| `textfile` | Read text from file |
| `fontfile` | Path to TTF/OTF font |
| `fontsize` | Font size in pixels |
| `fontcolor` | Color name or `0xRRGGBB[@alpha]` |
| `x`, `y` | Position (supports expressions) |
| `shadowx/y` | Drop shadow offset |
| `borderw` | Stroke width |
| `bordercolor` | Stroke color |
| `box=1` | Enable background box |
| `boxcolor` | Background box color |
| `enable` | Time expression |

```bash
# Centered white title
ffmpeg -i in.mp4 -vf \
  "drawtext=text='Hello World':fontsize=72:fontcolor=white:\
x=(w-text_w)/2:y=(h-text_h)/2:shadowx=3:shadowy=3" out.mp4

# Scrolling ticker bottom
ffmpeg -i in.mp4 -vf \
  "drawtext=text='Breaking News':fontsize=36:fontcolor=yellow:\
x=w-mod(t*200\,w+text_w):y=h-50:box=1:boxcolor=red@0.8" out.mp4

# Timecode overlay
ffmpeg -i in.mp4 -vf \
  "drawtext=text='%{pts\\:hms}':fontsize=24:fontcolor=white:\
x=10:y=10:box=1:boxcolor=black@0.5" out.mp4
```

---

### subtitles — Burn SRT/ASS Subtitles

```
subtitles=filename[,:stream_index=N]
ass=filename
```

```bash
# Burn SRT subtitles
ffmpeg -i video.mp4 -vf "subtitles=subs.srt" out.mp4

# Burn SRT with custom style
ffmpeg -i video.mp4 -vf \
  "subtitles=subs.srt:force_style='FontSize=24,PrimaryColour=&H00FFFFFF'" out.mp4

# Burn ASS/SSA (preserves styling)
ffmpeg -i video.mp4 -vf "ass=subs.ass" out.mp4

# Select subtitle track from container
ffmpeg -i video.mkv -vf "subtitles=video.mkv:si=0" out.mp4
```

---

### setpts — Change Presentation Timestamps (Speed)

```
setpts=expression*PTS
```

```bash
# 2× speed (half timestamps → faster playback)
ffmpeg -i in.mp4 -vf "setpts=0.5*PTS" out.mp4

# 0.5× speed (double timestamps → slower)
ffmpeg -i in.mp4 -vf "setpts=2.0*PTS" out.mp4
```

---

### reverse — Reverse Video

```
reverse
```

```bash
# Reverse entire clip (loads all frames into memory)
ffmpeg -i in.mp4 -vf "reverse" -af "areverse" out.mp4

# Reverse a short segment only
ffmpeg -i in.mp4 -ss 5 -t 3 -vf "reverse" -af "areverse" reversed_clip.mp4
```

---

### fps — Force Frame Rate

```
fps=rate[:round]
```

```bash
ffmpeg -i in.mp4 -vf "fps=30" out.mp4
ffmpeg -i in.mp4 -vf "fps=24000/1001" out.mp4   # 23.976 fps
ffmpeg -i in.mp4 -vf "fps=60,setpts=PTS" out.mp4  # 60fps with pts correction
```

---

### trim — Trim Video Stream

```
trim=start=...:end=...:duration=...
```

```bash
# Trim to 5–10 seconds then reset timestamps
ffmpeg -i in.mp4 -vf "trim=start=5:end=10,setpts=PTS-STARTPTS" out.mp4
```

---

### eq — Brightness, Contrast, Saturation, Gamma

```
eq=brightness=...:contrast=...:saturation=...:gamma=...
```

| Parameter | Range | Default |
|-----------|-------|---------|
| `brightness` | -1.0 to 1.0 | 0 |
| `contrast` | -1000 to 1000 | 1 |
| `saturation` | 0 to 3 | 1 |
| `gamma` | 0.1 to 10.0 | 1 |
| `gamma_r/g/b` | 0.1 to 10.0 | 1 |

```bash
ffmpeg -i in.mp4 -vf "eq=brightness=0.05:contrast=1.2:saturation=1.3:gamma=1.1" out.mp4
```

---

### hue — Hue/Saturation Shift

```
hue=h=degrees:s=saturation
```

```bash
# Shift hue 30°, boost saturation
ffmpeg -i in.mp4 -vf "hue=h=30:s=1.2" out.mp4

# Desaturate to grayscale
ffmpeg -i in.mp4 -vf "hue=s=0" out.mp4
```

---

### colorkey — Remove Solid Color (Keying)

```
colorkey=color:similarity:blend
```

```bash
# Remove green background
ffmpeg -i in.mp4 -vf "colorkey=green:0.3:0.2" out.mp4
ffmpeg -i in.mp4 -vf "colorkey=0x00FF00:0.35:0.15" out.mp4
```

---

### chromakey — Green/Blue Screen Removal

```
chromakey=color:similarity:blend[:yuv=1]
```

More accurate than `colorkey` for chroma keying.

```bash
# Composite: green-screen foreground over background
ffmpeg -i fg.mp4 -i bg.mp4 \
  -filter_complex "[0:v]chromakey=0x00FF00:0.3:0.2[fg];\
[1:v][fg]overlay" out.mp4

# Blue screen
ffmpeg -i fg.mp4 -i bg.mp4 \
  -filter_complex "[0:v]chromakey=0x0000FF:0.15:0.1[fg];\
[1:v][fg]overlay" out.mp4
```

---

### lut3d — Apply 3D LUT File (.cube, .3dl, .m3d)

```
lut3d=file=filename[:interp=mode]
```

| `interp` | Description |
|----------|-------------|
| `nearest` | Nearest neighbor (fast) |
| `trilinear` | Trilinear interpolation |
| `tetrahedral` | Tetrahedral (highest quality, default) |

```bash
ffmpeg -i in.mp4 -vf "lut3d=file=grade.cube" out.mp4
ffmpeg -i in.mp4 -vf "lut3d=file=film_emulation.3dl:interp=tetrahedral" out.mp4
```

---

### haldclut — Apply Hald CLUT Image

```
haldclut
```

Takes two inputs: video and CLUT image.

```bash
ffmpeg -i video.mp4 -i hald_clut.png \
  -filter_complex "[0:v][1:v]haldclut" out.mp4
```

---

### xfade — Video Transition Between Two Clips

```
xfade=transition=type:duration=secs:offset=secs
```

```bash
# Dissolve, 1s overlap, starting at t=5 of first clip
ffmpeg -i a.mp4 -i b.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=dissolve:duration=1:offset=5[v];\
[0:a][1:a]acrossfade=d=1[a]" \
  -map "[v]" -map "[a]" out.mp4
```

See `TRANSITIONS.md` for all transition types.

---

### minterpolate — Frame Interpolation (Motion Blur/Slow-Mo)

```
minterpolate=fps=N:mi_mode=mci[:mc_mode=aobmc]
```

```bash
# Smooth 24fps → 60fps with motion compensation
ffmpeg -i in.mp4 -vf "minterpolate=fps=60:mi_mode=mci" out.mp4
```

---

### hstack / vstack / xstack — Grid Layouts

```bash
# Side by side
ffmpeg -i a.mp4 -i b.mp4 -filter_complex "[0:v][1:v]hstack=inputs=2" out.mp4

# Top-bottom
ffmpeg -i a.mp4 -i b.mp4 -filter_complex "[0:v][1:v]vstack=inputs=2" out.mp4

# 2×2 grid
ffmpeg -i a.mp4 -i b.mp4 -i c.mp4 -i d.mp4 \
  -filter_complex "[0:v][1:v][2:v][3:v]xstack=inputs=4:\
layout=0_0|w0_0|0_h0|w0_h0[v]" \
  -map "[v]" out.mp4
```

---

## Audio Filters

### volume — Adjust Audio Volume

```
volume=value[:eval=frame]
```

```bash
ffmpeg -i in.mp4 -af "volume=1.5" out.mp4       # +50%
ffmpeg -i in.mp4 -af "volume=0.5" out.mp4       # -50%
ffmpeg -i in.mp4 -af "volume=6dB" out.mp4       # +6 dB
ffmpeg -i in.mp4 -af "volume=-3dB" out.mp4      # -3 dB
```

---

### loudnorm — EBU R128 Loudness Normalization

```
loudnorm=I=target:TP=true_peak:LRA=range[:measured_I=...:linear=true]
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `I` | -24 | Integrated loudness target (LUFS) |
| `TP` | -2 | Max true peak (dBTP) |
| `LRA` | 7 | Loudness range target (LU) |
| `linear` | false | Linear mode (use with pass 2 values) |
| `print_format` | `none` | `summary` or `json` for measurements |

```bash
# One-pass (dynamic mode)
ffmpeg -i in.mp4 -af "loudnorm=I=-16:TP=-1.5:LRA=11" out.mp4

# Pass 1 — measure
ffmpeg -i in.mp4 -af "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" -f null -

# Pass 2 — apply linear normalization
ffmpeg -i in.mp4 -af \
  "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=-23.5:measured_TP=-2.0:\
measured_LRA=8.1:measured_thresh=-34.1:linear=true" out.mp4
```

Use `scripts/normalize-audio.sh` for automated two-pass normalization.

---

### atempo — Change Audio Speed (Pitch-Preserving)

```
atempo=rate    (range: 0.5–2.0 per filter instance)
```

```bash
ffmpeg -i in.mp4 -af "atempo=1.5" out.mp4          # 1.5× speed
ffmpeg -i in.mp4 -af "atempo=2.0,atempo=2.0" out.mp4  # 4× speed
ffmpeg -i in.mp4 -af "atempo=0.5" out.mp4          # 0.5× speed
```

---

### areverse — Reverse Audio Stream

```bash
ffmpeg -i in.mp4 -af "areverse" out.mp4
```

---

### afade — Fade Audio In/Out

```
afade=t=in|out:st=start_time:d=duration
```

```bash
# Fade in 2s at start
ffmpeg -i in.mp4 -af "afade=t=in:st=0:d=2" out.mp4

# Fade out last 3s of a 60s clip
ffmpeg -i in.mp4 -af "afade=t=out:st=57:d=3" out.mp4

# Both
ffmpeg -i in.mp4 -af "afade=t=in:d=2,afade=t=out:st=57:d=3" out.mp4
```

---

### amix — Mix Multiple Audio Streams

```
amix=inputs=N[:duration=longest|shortest|first][:weights=w1 w2 ...]
```

```bash
# Mix two audio tracks (video at full vol, music at 30%)
ffmpeg -i video.mp4 -i music.mp3 \
  -filter_complex "[0:a][1:a]amix=inputs=2:duration=first:weights=1 0.3[a]" \
  -map 0:v -map "[a]" -c:v copy out.mp4
```

---

### acrossfade — Crossfade Between Two Audio Clips

```
acrossfade=d=duration[:c1=curve][:c2=curve]
```

```bash
ffmpeg -i a.mp4 -i b.mp4 \
  -filter_complex "[0:a][1:a]acrossfade=d=1[a]" \
  -map "[a]" out.aac
```

---

### sidechaincompress — Sidechain Compression (Ducking)

```
sidechaincompress=threshold:ratio:attack:release:level_sc=N
```

```bash
# Duck music when voice is present
ffmpeg -i music.mp3 -i voice.mp3 \
  -filter_complex "[1:a]asplit=2[sc][ref];\
[0:a][sc]sidechaincompress=threshold=0.02:ratio=4:attack=200:release=1000[compressed];\
[compressed][ref]amix=inputs=2[a]" \
  -map "[a]" out.mp3
```

---

### equalizer — Parametric EQ

```
equalizer=f=frequency:width_type=type:width=value:g=gain
```

```bash
# Boost 8kHz by 6dB (presence boost)
ffmpeg -i in.mp4 -af "equalizer=f=8000:width_type=o:width=2:g=6" out.mp4

# Cut 200Hz (muddy bass reduction)
ffmpeg -i in.mp4 -af "equalizer=f=200:width_type=o:width=1:g=-6" out.mp4
```

---

### highpass / lowpass — High/Low-Pass Filters

```bash
# Remove rumble below 80Hz
ffmpeg -i in.mp4 -af "highpass=f=80" out.mp4

# Telephone effect (bandpass 300–3400Hz)
ffmpeg -i in.mp4 -af "highpass=f=300,lowpass=f=3400" out.mp4
```

---

### agate — Noise Gate

```
agate=threshold:range:attack:release
```

```bash
# Gate background noise below -40dB
ffmpeg -i in.mp4 -af "agate=threshold=0.01:range=0.06:attack=10:release=200" out.mp4
```

---

### dynaudnorm — Dynamic Audio Normalizer

```
dynaudnorm=f=frame_len:p=peak_value
```

```bash
# Normalize frame-by-frame (good for spoken word)
ffmpeg -i in.mp4 -af "dynaudnorm=f=500:p=0.9" out.mp4
```

---

### aecho — Echo / Reverb

```
aecho=in_gain:out_gain:delays:decays
```

```bash
# Short room reverb
ffmpeg -i in.mp4 -af "aecho=0.8:0.88:60:0.4" out.mp4

# Long cave echo
ffmpeg -i in.mp4 -af "aecho=0.8:0.5:1000|1800:0.4|0.25" out.mp4
```

---

### aresample — Resample Audio

```bash
ffmpeg -i in.mp4 -af "aresample=48000" out.mp4
```

---

### channelmap / pan — Channel Remapping

```bash
# Extract left channel as mono
ffmpeg -i stereo.mp4 -af "channelmap=0|0:mono" out.mp4

# Mix stereo to mono
ffmpeg -i stereo.mp4 -af "pan=mono|c0=0.5*c0+0.5*c1" out.mp4

# Create stereo from two mono files
ffmpeg -i left.wav -i right.wav \
  -filter_complex "[0:a][1:a]join=inputs=2:channel_layout=stereo[a]" \
  -map "[a]" out.wav
```
