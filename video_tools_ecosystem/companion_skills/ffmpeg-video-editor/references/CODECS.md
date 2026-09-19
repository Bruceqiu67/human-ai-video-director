# FFmpeg Codec Selection Guide

Reference for choosing video and audio codecs for different use cases.

---

## Video Codec Comparison

| Codec | Encoder | CRF Range | Best CRF | Presets | Rel. Speed | Browser | Use Case |
|-------|---------|-----------|----------|---------|------------|---------|----------|
| H.264 | `libx264` | 0–51 | 18–28 | ultrafast→veryslow | Baseline | All | Web, streaming, archive |
| H.265 | `libx265` | 0–51 | 24–32 | ultrafast→veryslow | ~2× slower | Safari/Edge | 4K, HDR, smaller files |
| VP9 | `libvpx-vp9` | 0–63 | 28–40 | `cpu-used` 0–5 | ~3× slower | Chrome/FF | Web video, YouTube |
| AV1 | `libaom-av1` | 0–63 | 28–45 | `cpu-used` 0–8 | ~10× slower | Modern browsers | Best compression, future-proof |
| ProRes | `prores_ks` | — | `-profile:v` | — | Fast | macOS | Post-production, editing |
| FFV1 | `ffv1` | — | lossless | `-level 3` | Moderate | — | Archiving, preservation |

> **CRF guide**: Lower = better quality, larger file. Values above are typical "sweet spots" for each codec.

---

## H.264 (`libx264`)

The most widely compatible codec. Ideal for delivery, streaming, and web.

```bash
# Standard web delivery
ffmpeg -i in.mp4 -c:v libx264 -crf 23 -preset slow \
  -c:a aac -b:a 128k -movflags +faststart out.mp4

# High quality archive
ffmpeg -i in.mp4 -c:v libx264 -crf 18 -preset veryslow \
  -c:a aac -b:a 192k -movflags +faststart out.mp4

# Fast proxy
ffmpeg -i in.mp4 -c:v libx264 -crf 28 -preset ultrafast \
  -c:a aac -b:a 96k out.mp4

# Constrained bitrate (streaming server)
ffmpeg -i in.mp4 -c:v libx264 -b:v 2M -maxrate 2.5M -bufsize 5M \
  -c:a aac -b:a 128k out.mp4
```

### Presets (speed/quality tradeoff, same CRF)

`ultrafast` → `superfast` → `veryfast` → `faster` → `fast` → `medium` → `slow` → `slower` → `veryslow`

- Faster presets = larger files at same quality
- `slow` or `slower` recommended for final delivery

### H.264 Profiles

| Profile | `-profile:v` | Max level | Compatible with |
|---------|-------------|-----------|-----------------|
| Baseline | `baseline` | 3.0 | Old mobile, HLS |
| Main | `main` | 4.0 | Most devices |
| High | `high` | 5.2 | Modern devices (default) |

```bash
# Maximum compatibility (old devices, HLS)
ffmpeg -i in.mp4 -c:v libx264 -profile:v baseline -level 3.0 \
  -crf 23 -preset slow -c:a aac -b:a 128k out.mp4
```

---

## H.265 / HEVC (`libx265`)

~40–50% smaller than H.264 at equivalent quality. Excellent for 4K and HDR.

```bash
# Standard H.265
ffmpeg -i in.mp4 -c:v libx265 -crf 28 -preset slow \
  -c:a aac -b:a 128k -tag:v hvc1 out.mp4

# 4K HDR (HDR10)
ffmpeg -i in.4k.mp4 \
  -c:v libx265 -crf 22 -preset slow \
  -x265-params "hdr-opt=1:repeat-headers=1:colorprim=bt2020:transfer=smpte2084:\
colormatrix=bt2020nc:master-display=G(13250,34500)B(7500,3000)R(34000,16000)WP(15635,16450)L(40000000,50)" \
  -c:a aac -b:a 192k out.mp4

# -tag:v hvc1 needed for Apple device compatibility
```

---

## VP9 (`libvpx-vp9`)

Royalty-free, excellent for YouTube uploads and WebM delivery.

```bash
# Two-pass VP9 (best quality/size ratio)
ffmpeg -i in.mp4 -c:v libvpx-vp9 -b:v 0 -crf 33 -pass 1 \
  -an -f webm /dev/null
ffmpeg -i in.mp4 -c:v libvpx-vp9 -b:v 0 -crf 33 -pass 2 \
  -c:a libopus -b:a 128k out.webm

# Constrained bitrate VP9
ffmpeg -i in.mp4 -c:v libvpx-vp9 -b:v 2M -maxrate 3M -bufsize 6M \
  -c:a libopus -b:a 128k out.webm

# cpu-used: 0=slowest/best, 5=fastest for real-time
ffmpeg -i in.mp4 -c:v libvpx-vp9 -crf 33 -b:v 0 -cpu-used 2 \
  -c:a libopus out.webm
```

---

## AV1 (`libaom-av1`, `libsvtav1`)

Best compression ratio. libaom is reference encoder (slow); SVT-AV1 is much faster.

```bash
# libaom-av1 (high quality, slow)
ffmpeg -i in.mp4 -c:v libaom-av1 -crf 35 -cpu-used 4 \
  -c:a libopus -b:a 128k out.mkv

# SVT-AV1 (much faster, nearly same quality)
ffmpeg -i in.mp4 -c:v libsvtav1 -crf 35 -preset 6 \
  -c:a libopus -b:a 128k out.mkv

# Two-pass SVT-AV1
ffmpeg -i in.mp4 -c:v libsvtav1 -b:v 2M -pass 1 -an -f null /dev/null
ffmpeg -i in.mp4 -c:v libsvtav1 -b:v 2M -pass 2 -c:a libopus out.mkv
```

---

## Apple ProRes (`prores_ks`)

Intermediate codec for post-production workflows. Intra-frame only (no long GOP).

```bash
# ProRes 422 HQ (editing master)
ffmpeg -i in.mp4 -c:v prores_ks -profile:v 3 \
  -c:a pcm_s16le out.mov

# ProRes 4444 (with alpha channel)
ffmpeg -i in.mp4 -c:v prores_ks -profile:v 4 \
  -c:a pcm_s24le out.mov
```

### ProRes Profiles

| Profile | `-profile:v` | Bitrate (1080p30) | Use Case |
|---------|-------------|-------------------|----------|
| ProRes 422 Proxy | 0 | ~45 Mbps | Offline editing proxy |
| ProRes 422 LT | 1 | ~102 Mbps | Light editing |
| ProRes 422 | 2 | ~147 Mbps | Standard post |
| ProRes 422 HQ | 3 | ~220 Mbps | High-quality master |
| ProRes 4444 | 4 | ~330 Mbps | With alpha, VFX |
| ProRes 4444 XQ | 5 | ~500 Mbps | Ultra quality |

---

## FFV1 (`ffv1`)

Lossless codec for archiving. Used by libraries and broadcasters.

```bash
# FFV1 lossless (level 3 = multithreaded, error detection)
ffmpeg -i in.mp4 -c:v ffv1 -level 3 -threads 8 \
  -coder 1 -context 1 -g 1 -slicecrc 1 \
  -c:a flac out.mkv
```

---

## Audio Codec Guide

| Codec | Encoder | Bitrate Range | Lossy? | Use Case |
|-------|---------|---------------|--------|----------|
| AAC | `aac` / `libfdk_aac` | 96–320k | Yes | Universal delivery |
| MP3 | `libmp3lame` | 64–320k | Yes | Legacy compatibility |
| Opus | `libopus` | 32–256k | Yes | Web, WebM, excellent at low bitrates |
| Vorbis | `libvorbis` | 80–500k | Yes | OGG containers |
| FLAC | `flac` | ~1000k | No | Lossless archive |
| PCM | `pcm_s16le` / `pcm_s24le` | ~1411k+ | No | Broadcast, editing |

```bash
# AAC (standard)
ffmpeg -i in.mp4 -c:a aac -b:a 192k out.mp4

# AAC (libfdk_aac — higher quality if available)
ffmpeg -i in.mp4 -c:a libfdk_aac -b:a 192k -vbr 4 out.mp4

# MP3
ffmpeg -i in.mp4 -c:a libmp3lame -b:a 320k -q:a 2 out.mp3

# Opus (excellent at 96k)
ffmpeg -i in.mp4 -c:a libopus -b:a 96k out.webm

# FLAC lossless
ffmpeg -i in.wav -c:a flac out.flac
```

---

## Container Format Guide

| Extension | Common Codecs | Notes |
|-----------|--------------|-------|
| `.mp4` | H.264, H.265, AAC | Universal, web-friendly |
| `.mov` | ProRes, H.264, PCM | macOS/iOS, Apple ecosystem |
| `.mkv` | Any | Open format, multiple streams |
| `.webm` | VP8/VP9/AV1, Opus/Vorbis | Web, HTML5 |
| `.ts` | H.264, AAC | Broadcast, HLS segments |
| `.mxf` | XDCAM, DNxHD | Broadcast, professional |

---

## Bitrate Target Reference (H.264)

| Resolution | Frame Rate | Streaming | Good Quality | Archive |
|-----------|------------|-----------|--------------|---------|
| 480p | 30 | 500k–1M | 1–2M | 3M |
| 720p | 30 | 1–2.5M | 2.5–4M | 6M |
| 1080p | 30 | 3–5M | 5–8M | 12M |
| 1080p | 60 | 4.5–7M | 7–12M | 16M |
| 4K | 30 | 15–25M | 25–35M | 50M |
| 4K | 60 | 20–35M | 35–50M | 70M |
