# ffmpeg-video-editor

An [agentskills.io](https://agentskills.io) skill that gives an AI agent
complete FFmpeg video editing capabilities — trimming, transcoding,
concatenating, filtering, color grading, audio normalization, and more.

---

## Capabilities

- **Transcode** between any format: H.264, H.265, VP9, AV1, ProRes, FFV1
- **Trim & Cut** with frame-accurate or fast stream-copy modes
- **Concatenate** multiple clips with the concat demuxer helper script
- **Scale, Crop & Pad** to any resolution or aspect ratio
- **Overlay & Composite** watermarks, picture-in-picture, green-screen keying
- **Draw Text & Titles** with custom fonts, animations, and timecodes
- **Burn Subtitles** from SRT or ASS/SSA files
- **Change Speed** (setpts + atempo, any multiplier)
- **Reverse** video and audio
- **Transitions** using xfade (40+ types — see `references/TRANSITIONS.md`)
- **Color Grade** with eq, hue, LUT3D (.cube), and Hald CLUT
- **Chroma Key** green/blue screen compositing
- **Audio Normalization** via two-pass EBU R128 loudnorm
- **Audio Mixing** with amix, sidechain compression, afade
- **Hardware Acceleration** via NVENC, QSV, AMF, VideoToolbox, VAAPI
- **Frame Extraction & Slideshow** creation
- **Grid Layouts** with hstack, vstack, xstack
- **Encoding Presets** for web, social media, preview, and lossless

---

## Requirements

- **FFmpeg** >= 6.0 (with libx264, libx265, libvpx-vp9, libopus, loudnorm)
- **FFprobe** >= 6.0 (included with FFmpeg)

### Install FFmpeg

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg

# macOS (Homebrew)
brew install ffmpeg

# Windows (Scoop)
scoop install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg

# Build from source (all codecs)
# https://trac.ffmpeg.org/wiki/CompilationGuide
```

### Verify Installation

```bash
ffmpeg -version
ffprobe -version
ffmpeg -encoders | grep -E "libx264|libx265|libvpx|loudnorm"
```

---

## Install the Skill

```bash
npx skills add ffmpeg-video-editor
```

Or clone directly:

```bash
git clone https://github.com/bryanwhl/ffmpeg-video-editor
cd ffmpeg-video-editor
chmod +x scripts/*.sh
```

---

## Directory Structure

```
ffmpeg-video-editor/
├── SKILL.md                     # Agent skill definition and command reference
├── README.md                    # This file
├── LICENSE                      # MIT License
├── scripts/
│   ├── probe.sh                 # Inspect media files (ffprobe wrapper)
│   ├── concat.sh                # Concatenate video files
│   └── normalize-audio.sh       # Two-pass EBU R128 loudness normalization
├── references/
│   ├── FILTERS.md               # Complete filter reference (video + audio)
│   ├── CODECS.md                # Codec comparison and selection guide
│   ├── TRANSITIONS.md           # All 40+ xfade transition types
│   └── HARDWARE-ACCEL.md        # GPU encoding: NVENC, QSV, AMF, VT, VAAPI
└── assets/
    └── preset-profiles.json     # Encoding presets (web, social, lossless, etc.)
```

---

## Quick Start

```bash
# Inspect a media file
./scripts/probe.sh input.mp4

# Transcode to web-optimized H.264
ffmpeg -i input.mp4 -c:v libx264 -crf 23 -preset slow \
  -c:a aac -b:a 128k -movflags +faststart output.mp4

# Concatenate clips
./scripts/concat.sh output.mp4 clip1.mp4 clip2.mp4 clip3.mp4

# Normalize audio to -16 LUFS (EBU R128)
./scripts/normalize-audio.sh input.mp4 output.mp4

# Trim 1:00–2:30 (stream copy, no re-encode)
ffmpeg -ss 00:01:00 -to 00:02:30 -i input.mp4 -c copy trimmed.mp4

# Scale to 1280×720
ffmpeg -i input.mp4 -vf "scale=1280:-2" -c:v libx264 -crf 23 out.mp4

# Apply 3D LUT color grade
ffmpeg -i input.mp4 -vf "lut3d=film_look.cube" -c:v libx264 -crf 18 out.mp4
```

---

## Script Reference

### `scripts/probe.sh`

```
Usage: probe.sh [OPTIONS] <input_file>
  -j, --json        Full JSON output
  -v, --video       Video stream info only
  -a, --audio       Audio stream info only
  -f, --format      Container/format info only
  -s, --streams     All streams summary
```

### `scripts/concat.sh`

```
Usage: concat.sh [OPTIONS] <output_file> <input1> [input2 ...]
  -r, --reencode    Re-encode (default: stream copy)
  -v, --vcodec      Video codec (default: libx264)
  --crf             CRF value (default: 23)
  -k, --keep-list   Keep temp concat list file
```

### `scripts/normalize-audio.sh`

```
Usage: normalize-audio.sh [OPTIONS] <input> <output>
  -I, --integrated  Target LUFS (default: -16)
  -T, --true-peak   Max dBTP (default: -1.5)
  -L, --lra         Loudness range LU (default: 11)
  -s, --stereo      Force stereo downmix
  --acodec          Output audio codec (default: aac)
```

---

## Reference Documents

| File | Contents |
|------|----------|
| `references/FILTERS.md` | scale, crop, pad, overlay, drawtext, subtitles, setpts, reverse, fps, eq, hue, colorkey, chromakey, lut3d, haldclut, xfade, minterpolate, volume, loudnorm, atempo, areverse, afade, amix, acrossfade, sidechaincompress, equalizer, highpass, lowpass, agate, dynaudnorm, aecho, aresample, channelmap, pan |
| `references/CODECS.md` | H.264, H.265, VP9, AV1, ProRes, FFV1 comparison; audio codecs; bitrate targets |
| `references/TRANSITIONS.md` | All 40+ xfade types with descriptions and examples |
| `references/HARDWARE-ACCEL.md` | NVENC, QSV, AMF, VideoToolbox, VAAPI detection and pipelines |

---

## Encoding Presets

Defined in `assets/preset-profiles.json`:

| Profile | Codec | CRF | Use Case |
|---------|-------|-----|----------|
| `web-optimized` | H.264 | 23 | YouTube, Vimeo, web |
| `high-quality` | H.264 | 18 | Client deliverables, archive |
| `social-media-vertical` | H.264 | 23 | TikTok, Reels (9:16) |
| `social-media-square` | H.264 | 23 | Instagram feed (1:1) |
| `fast-preview` | H.264 | 28 | Proxy, review links |
| `lossless-intermediate` | FFV1 | — | Post-production, preservation |

---

## License

MIT — see [LICENSE](./LICENSE)
