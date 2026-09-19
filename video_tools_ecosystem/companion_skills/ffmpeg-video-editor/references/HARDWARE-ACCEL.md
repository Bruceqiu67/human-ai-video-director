# FFmpeg Hardware Acceleration Guide

GPU-accelerated encoding and decoding for faster processing.

---

## Detection

### Check Available Hardware Encoders

```bash
ffmpeg -encoders 2>/dev/null | grep -E "nvenc|qsv|amf|videotoolbox|vaapi|v4l2"
```

### Check Available Hardware Decoders

```bash
ffmpeg -decoders 2>/dev/null | grep -E "cuvid|qsv|vaapi|videotoolbox"
```

### List hwaccels

```bash
ffmpeg -hwaccels
```

### Detect NVIDIA GPU

```bash
nvidia-smi -L                         # Linux/Windows
nvidia-smi --query-gpu=name,driver_version --format=csv
```

### Detect Intel QSV (Linux)

```bash
vainfo 2>/dev/null | grep -i "va_profile"
ls /dev/dri/renderD*
```

### Detect AMD GPU (Linux)

```bash
rocminfo 2>/dev/null | grep -i "Device Type"
```

### Detect Apple VideoToolbox

```bash
ffmpeg -encoders 2>/dev/null | grep videotoolbox
```

---

## NVIDIA NVENC

Requires: NVIDIA GPU (Maxwell+), CUDA drivers, FFmpeg built with `--enable-cuda-nvcc` or `--enable-nvenc`.

### H.264 NVENC

```bash
# Basic H.264 NVENC
ffmpeg -i input.mp4 -c:v h264_nvenc -preset p4 -cq 23 -c:a aac output.mp4

# With hardware decode (zero-copy GPU pipeline)
ffmpeg -hwaccel cuda -hwaccel_output_format cuda \
  -i input.mp4 \
  -c:v h264_nvenc -preset p4 -cq 23 \
  -c:a aac -b:a 128k output.mp4

# Constrained bitrate (streaming)
ffmpeg -hwaccel cuda -i input.mp4 \
  -c:v h264_nvenc -preset p4 \
  -b:v 4M -maxrate 5M -bufsize 10M \
  -c:a aac -b:a 128k output.mp4
```

### H.265 NVENC

```bash
ffmpeg -hwaccel cuda -hwaccel_output_format cuda \
  -i input.mp4 \
  -c:v hevc_nvenc -preset p4 -cq 26 \
  -tag:v hvc1 \
  -c:a aac -b:a 128k output.mp4
```

### AV1 NVENC (Ada Lovelace / RTX 40 series+)

```bash
ffmpeg -hwaccel cuda -i input.mp4 \
  -c:v av1_nvenc -preset p4 -cq 30 \
  -c:a libopus -b:a 128k output.mkv
```

### NVENC Preset Reference

| Preset | Speed | Quality | Use Case |
|--------|-------|---------|----------|
| `p1` | Fastest | Lowest | Real-time, low latency |
| `p2` | Very fast | Low | Live streaming |
| `p3` | Fast | Medium | |
| `p4` | Medium | Good | General encoding |
| `p5` | Slow | Better | |
| `p6` | Slower | High | Archive |
| `p7` | Slowest | Highest | Offline quality |

### NVENC Quality Modes

| Flag | Description |
|------|-------------|
| `-cq N` | Constant quality (0=best, 51=worst; like CRF) |
| `-b:v N` | Target bitrate |
| `-rc vbr` | Variable bitrate mode |
| `-rc cbr` | Constant bitrate (streaming) |

### GPU Scaling Filter (stays on GPU)

```bash
ffmpeg -hwaccel cuda -hwaccel_output_format cuda \
  -i input.mp4 \
  -vf "scale_cuda=1920:1080" \
  -c:v h264_nvenc -preset p4 -cq 23 output.mp4
```

### Full GPU Pipeline (decode + filter + encode)

```bash
ffmpeg \
  -hwaccel cuda -hwaccel_output_format cuda \
  -i input.mp4 \
  -vf "scale_cuda=1280:720,hwdownload,format=nv12" \
  -c:v h264_nvenc -preset p4 -cq 23 \
  -c:a aac -b:a 128k output.mp4
```

---

## Intel QuickSync (QSV)

Requires: Intel CPU with integrated GPU (Broadwell+), `intel-media-driver` or `libva-intel-driver`.

### H.264 QSV

```bash
# Software decode + QSV encode
ffmpeg -i input.mp4 -c:v h264_qsv -global_quality 23 -preset slow \
  -c:a aac -b:a 128k output.mp4

# Hardware decode + encode
ffmpeg -hwaccel qsv -c:v h264_qsv -i input.mp4 \
  -c:v h264_qsv -global_quality 23 -preset slow output.mp4
```

### H.265 QSV

```bash
ffmpeg -i input.mp4 -c:v hevc_qsv -global_quality 26 -preset slow \
  -c:a aac -b:a 128k output.mp4
```

### AV1 QSV (Intel Arc / 12th gen+)

```bash
ffmpeg -i input.mp4 -c:v av1_qsv -global_quality 35 -preset slow \
  -c:a libopus output.mkv
```

### QSV Presets

`veryfast` → `faster` → `fast` → `medium` → `slow` → `slower` → `veryslow`

### QSV Scaling

```bash
ffmpeg -hwaccel qsv -i input.mp4 \
  -vf "scale_qsv=1280:720" \
  -c:v h264_qsv -global_quality 23 output.mp4
```

---

## AMD AMF (Advanced Media Framework)

Requires: AMD GPU (GCN+), AMF SDK, Windows or Linux with AMDGPU-Pro.

### H.264 AMF

```bash
ffmpeg -i input.mp4 -c:v h264_amf -quality quality \
  -b:v 4M -c:a aac -b:a 128k output.mp4
```

### H.265 AMF

```bash
ffmpeg -i input.mp4 -c:v hevc_amf -quality quality \
  -b:v 3M -c:a aac -b:a 128k output.mp4
```

### AMF Quality Modes

| `-quality` | Description |
|-----------|-------------|
| `speed` | Fastest, lowest quality |
| `balanced` | Balanced (default) |
| `quality` | Slowest, highest quality |

---

## Apple VideoToolbox (macOS / iOS)

Requires: macOS 10.8+. Uses Apple Silicon Neural Engine or AMD GPU.

### H.264 VideoToolbox

```bash
ffmpeg -i input.mp4 -c:v h264_videotoolbox -q:v 65 \
  -c:a aac -b:a 128k output.mp4

# Constrained bitrate
ffmpeg -i input.mp4 -c:v h264_videotoolbox -b:v 4M \
  -c:a aac -b:a 128k output.mp4
```

### H.265 / HEVC VideoToolbox

```bash
ffmpeg -i input.mp4 -c:v hevc_videotoolbox -q:v 60 \
  -tag:v hvc1 -c:a aac -b:a 128k output.mp4
```

### ProRes VideoToolbox

```bash
ffmpeg -i input.mp4 -c:v prores_videotoolbox -profile:v 3 \
  -c:a pcm_s16le output.mov
```

### VideoToolbox Quality Scale

`-q:v` range: 1–100 (higher = better quality, larger file)

| Value | Approximate Quality |
|-------|---------------------|
| 40 | Low (proxy) |
| 55 | Medium |
| 65 | Good (default delivery) |
| 75 | High quality |
| 85 | Very high |
| 100 | Near-lossless |

---

## VAAPI (VA-API — Linux)

Requires: Linux, Mesa or Intel/AMD driver with VA-API support (`libva`).

### Setup Check

```bash
vainfo                             # Check VA-API support
ls /dev/dri/renderD128             # Default render device
```

### H.264 VAAPI

```bash
ffmpeg -vaapi_device /dev/dri/renderD128 \
  -i input.mp4 \
  -vf "format=nv12,hwupload" \
  -c:v h264_vaapi -qp 23 output.mp4
```

### H.265 VAAPI

```bash
ffmpeg -vaapi_device /dev/dri/renderD128 \
  -i input.mp4 \
  -vf "format=nv12,hwupload" \
  -c:v hevc_vaapi -qp 26 output.mp4
```

### VAAPI with HW Decode

```bash
ffmpeg -hwaccel vaapi -hwaccel_device /dev/dri/renderD128 \
  -hwaccel_output_format vaapi \
  -i input.mp4 \
  -vf "scale_vaapi=1280:720" \
  -c:v h264_vaapi -qp 23 output.mp4
```

### VAAPI Scaling Filter

```bash
-vf "scale_vaapi=W:H"
```

---

## V4L2 (Video4Linux — Raspberry Pi, embedded)

```bash
# Raspberry Pi H.264 hardware encoder
ffmpeg -i input.mp4 -c:v h264_v4l2m2m -b:v 4M output.mp4
```

---

## Performance Comparison

| Method | 1080p H.264 Speed | Notes |
|--------|------------------|-------|
| `libx264` slow | ~80–150 fps | Best quality/compression |
| `libx264` ultrafast | ~400–800 fps | Larger files |
| `h264_nvenc` (RTX 3080) | ~800–1500 fps | Near-realtime |
| `h264_qsv` (i7) | ~300–600 fps | Moderate quality |
| `hevc_videotoolbox` (M1) | ~600–1000 fps | Excellent for Apple |
| `h264_vaapi` | ~200–500 fps | Driver dependent |

---

## Fallback Pattern (Try HW, Fall Back to SW)

```bash
#!/usr/bin/env bash
# Try NVENC first, fall back to libx264
encode() {
  local IN="$1" OUT="$2"
  if ffmpeg -hwaccels 2>/dev/null | grep -q cuda; then
    ffmpeg -hwaccel cuda -i "$IN" -c:v h264_nvenc -preset p4 -cq 23 \
      -c:a aac -b:a 128k "$OUT" && return
  fi
  ffmpeg -i "$IN" -c:v libx264 -crf 23 -preset slow \
    -c:a aac -b:a 128k "$OUT"
}

encode input.mp4 output.mp4
```
