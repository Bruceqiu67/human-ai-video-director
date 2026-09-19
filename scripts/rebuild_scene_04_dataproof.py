import asyncio
import json
import math
import os
import subprocess
import edge_tts
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"d:\video\视频3"
AUDIO_OUT_DIR = os.path.join(BASE_DIR, "output", "audio")
DEMO_DIR = os.path.join(BASE_DIR, "素材", "04_分幕原生画卷")
MANIFEST_FILE = os.path.join(AUDIO_OUT_DIR, "manifest_yunxi.json")
OUTPUT_SCENE4_VIDEO = os.path.join(BASE_DIR, "output", "video", "scene_04_yunxi.mp4")
OUTPUT_MASTER_VIDEO = os.path.join(BASE_DIR, "output", "video", "好帮手AI话术私教_终极宣传大片_云希合规版.mp4")
QA_DIR = os.path.join(BASE_DIR, "output", "qa_frames")
BRAIN_DIR = r"C:\Users\26048\.gemini\antigravity\brain\ec192f70-8f1e-4c29-9127-763c3836bbc2"

VOICE = "zh-CN-YunxiNeural"
RATE = "+18%"
WIDTH = 1080
HEIGHT = 1920
FPS = 30

FONT_PATH = r"C:\Windows\Fonts\msyhbd.ttc"
if not os.path.exists(FONT_PATH):
    FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"

# 第四幕 7 句标准分句台词（合规数据支撑版）
SCENE_04_LINES = [
    {"id": "s4_1", "text": "一通练完，AI立刻输出深度体检单！", "pause_after": 0.30, "pose": "Pose1_体检单"},
    {"id": "s4_2", "text": "第一次只有45分？", "pause_after": 0.35, "pose": "Pose1_耸肩错愕"},
    {"id": "s4_3", "text": "别慌，它给的可不是泛泛的加油，", "pause_after": 0.25, "pose": "Pose2_托腮思考"},
    {"id": "s4_4", "text": "而是指骨到肉的解法：", "pause_after": 0.30, "pose": "Pose2_托腮思考"},
    {"id": "s4_5", "text": "开场白太冗长？直接教你‘数据支撑’——", "pause_after": 0.35, "pose": "Pose2_数据支撑"},
    {"id": "s4_6", "text": "第一句话抛出‘90%同到期车主已办理’，", "pause_after": 0.30, "pose": "Pose3_数据支撑"},
    {"id": "s4_7", "text": "一秒锁死客户注意力！", "pause_after": 0.50, "pose": "Pose3_OK自信"}
]

def get_audio_duration(file_path):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
    res = subprocess.check_output(cmd, shell=True).decode().strip()
    return float(res)

def patch_scene04_images():
    print("=== 1. 应用数据支撑版画面修补 (90%同到期车主已办理) ===")
    poses = [
        "Scene04_深度诊断_Pose1_耸肩错愕.jpg",
        "Scene04_深度诊断_Pose2_托腮思考.jpg",
        "Scene04_深度诊断_Pose3_OK自信.jpg"
    ]
    card_bg = (252, 252, 247)

    for p_name in poses:
        p_path = os.path.join(DEMO_DIR, p_name)
        img = Image.open(p_path).convert("RGB")
        d = ImageDraw.Draw(img)

        # 1. 抹除并重写标题：改进建议：数据支撑
        d.rectangle([(100, 914), (420, 952)], fill=card_bg)
        font_title = ImageFont.truetype(FONT_PATH, 30)
        d.text((105, 917), "改进建议：数据支撑", font=font_title, fill=(28, 22, 18))

        # 2. 抹除并重绘橙色荧光笔高亮：90%同到期车主已办理
        d.rectangle([(100, 954), (455, 1018)], fill=card_bg)
        d.rounded_rectangle([(108, 958), (448, 1016)], radius=8, fill=(255, 155, 65))
        font_hl = ImageFont.truetype(FONT_PATH, 27)
        d.text((118, 972), "90%同到期车主已办理", font=font_hl, fill=(28, 20, 15))

        out_name = p_name.replace(".jpg", "_合规修补版.jpg")
        out_path = os.path.join(DEMO_DIR, out_name)
        img.save(out_path, quality=95)
        print(f"  + 修补保存: {out_name}")

    # 保存走查切片
    img_qa = Image.open(os.path.join(DEMO_DIR, "Scene04_深度诊断_Pose2_托腮思考_合规修补版.jpg"))
    crop = img_qa.crop((80, 880, 600, 1050))
    crop.save(os.path.join(QA_DIR, "qa_patch_s4_dataproof.jpg"), quality=95)
    crop.save(os.path.join(BRAIN_DIR, "patch_s4.jpg"), quality=95)

async def build_scene_04_audio():
    print("=== 2. 合成第四幕云希配音 (数据支撑版) ===")
    seg_files = []
    manifest_s4 = []
    cur_time = 0.0

    for idx, item in enumerate(SCENE_04_LINES):
        raw_mp3 = os.path.join(AUDIO_OUT_DIR, f"raw_s4_dp_{idx}.mp3")
        trim_wav = os.path.join(AUDIO_OUT_DIR, f"trim_s4_dp_{idx}.wav")
        timed_wav = os.path.join(AUDIO_OUT_DIR, f"timed_s4_dp_{idx}.wav")
        text = item["text"]
        pause = item.get("pause_after", 0.3)
        pose = item.get("pose", "Pose1_体检单")

        comm = edge_tts.Communicate(text, VOICE, rate=RATE)
        await comm.save(raw_mp3)

        cmd_trim = [
            "ffmpeg", "-y", "-i", raw_mp3,
            "-af", "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB,areverse",
            trim_wav
        ]
        subprocess.run(cmd_trim, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        dur = get_audio_duration(trim_wav)

        if pause > 0.02:
            cmd_pad = [
                "ffmpeg", "-y", "-i", trim_wav,
                "-af", f"apad=pad_dur={pause}",
                "-ar", "44100", "-ac", "1", timed_wav
            ]
        else:
            cmd_pad = [
                "ffmpeg", "-y", "-i", trim_wav,
                "-ar", "44100", "-ac", "1", timed_wav
            ]
        subprocess.run(cmd_pad, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        manifest_s4.append({
            "id": item["id"],
            "text": text,
            "start": round(cur_time, 3),
            "end": round(cur_time + dur, 3),
            "duration": round(dur, 3),
            "pause_after": pause,
            "pose": pose
        })
        cur_time += dur + pause
        seg_files.append((raw_mp3, trim_wav, timed_wav))

    concat_txt = os.path.join(AUDIO_OUT_DIR, "concat_scene_04_dp.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for _, _, timed_wav in seg_files:
            abs_w = os.path.abspath(timed_wav).replace("\\", "/")
            f.write(f"file '{abs_w}'\n")

    out_master_wav = os.path.join(AUDIO_OUT_DIR, "scene_04_yunxi_master.wav")
    cmd_merge = f'ffmpeg -y -f concat -safe 0 -i "{concat_txt}" -c:a pcm_s16le -ar 44100 -ac 1 "{out_master_wav}"'
    subprocess.run(cmd_merge, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for r, t, w in seg_files:
        if os.path.exists(r): os.remove(r)
        if os.path.exists(t): os.remove(t)
        if os.path.exists(w): os.remove(w)
    if os.path.exists(concat_txt):
        os.remove(concat_txt)

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        all_m = json.load(f)
    all_m["scene_04"] = manifest_s4
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(all_m, f, ensure_ascii=False, indent=2)

    actual_dur = get_audio_duration(out_master_wav)
    print(f"[SCENE 04] 云希数据支撑母带就绪: {out_master_wav} (实际时长: {actual_dur:.3f}s)")
    return manifest_s4

def create_page_turn(img_a, img_b, progress):
    p = progress * progress * (3.0 - 2.0 * progress)
    out = img_b.copy()
    curl_w = int(140 * math.sin(math.pi * progress) + 30)
    fold_x = int((1.0 - p) * (WIDTH + curl_w * 2) - curl_w)
    if fold_x > 0:
        mask = Image.new('L', (WIDTH, HEIGHT), 0)
        draw_mask = ImageDraw.Draw(mask)
        tilt = int(45 * math.sin(math.pi * progress))
        pts = [(0, 0), (fold_x - tilt, 0), (fold_x + tilt, HEIGHT), (0, HEIGHT)]
        draw_mask.polygon(pts, fill=255)
        out.paste(img_a, (0, 0), mask=mask)
    return out

def draw_subtitle_pill(canvas, text):
    if not text:
        return
    draw = ImageDraw.Draw(canvas)
    font_size = 36
    font = ImageFont.truetype(FONT_PATH, font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    while (tw + 68) > 940 and font_size > 24:
        font_size -= 2
        font = ImageFont.truetype(FONT_PATH, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

    pad_x = 34
    pad_y = 16
    cx = (WIDTH - tw) // 2
    cy = 1675

    x1 = cx - pad_x
    y1 = cy - pad_y
    x2 = cx + tw + pad_x
    y2 = cy + th + pad_y + 4

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    d_over.rounded_rectangle([x1, y1, x2, y2], radius=18, fill=(32, 30, 28, 230))
    canvas.alpha_composite(overlay)

    d_final = ImageDraw.Draw(canvas)
    d_final.text((cx, cy), text, font=font, fill=(255, 255, 255, 255))

def render_scene_04(manifest_s4):
    print("=== 3. 渲染第四幕 Scene 04 视频 ===")
    total_dur = manifest_s4[-1]["end"] + manifest_s4[-1]["pause_after"]
    total_frames = int(math.ceil(total_dur * FPS))

    prev_plate_path = os.path.join(DEMO_DIR, "Scene03_结尾最后一帧_yunxi.png")
    if not os.path.exists(prev_plate_path):
        prev_plate_path = os.path.join(DEMO_DIR, "Scene03_拟真对攻_Pose3_双手抱胸自信.jpg")
    prev_plate = Image.open(prev_plate_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    p1 = Image.open(os.path.join(DEMO_DIR, "Scene04_深度诊断_Pose1_耸肩错愕_合规修补版.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    p2 = Image.open(os.path.join(DEMO_DIR, "Scene04_深度诊断_Pose2_托腮思考_合规修补版.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    p3 = Image.open(os.path.join(DEMO_DIR, "Scene04_深度诊断_Pose3_OK自信_合规修补版.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    audio_file = os.path.join(AUDIO_OUT_DIR, "scene_04_yunxi_master.wav")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgba",
        "-r", str(FPS),
        "-i", "-",
        "-i", audio_file,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "320k",
        "-shortest",
        OUTPUT_SCENE4_VIDEO
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    # 姿态切换点计算
    # s4_1, s4_2 -> p1 (0.0s ~ s4_3 start)
    # s4_3, s4_4, s4_5 -> p2 (s4_3 start ~ s4_6 start)
    # s4_6, s4_7 -> p3 (s4_6 start ~ end)
    t_p2 = manifest_s4[2]["start"]
    t_p3 = manifest_s4[5]["start"]
    f_p2 = int(t_p2 * FPS)
    f_p3 = int(t_p3 * FPS)

    print(f"  > 翻书进入: 0 ~ 18 帧 (0.0s ~ 0.60s)")
    print(f"  > Pose 1 (体检单+耸肩错愕): 18 ~ {f_p2} 帧 (0.60s ~ {t_p2:.2f}s)")
    print(f"  > Pose 2 (托腮思考+数据支撑): {f_p2} ~ {f_p3} 帧 ({t_p2:.2f}s ~ {t_p3:.2f}s)")
    print(f"  > Pose 3 (OK自信+90%同到期车主已办理): {f_p3} ~ {total_frames} 帧 ({t_p3:.2f}s ~ {total_dur:.2f}s)")

    for f in range(total_frames):
        t = f / float(FPS)
        if f < 18:
            p_turn = f / 18.0
            frame_bg = create_page_turn(prev_plate, p1, p_turn).convert("RGBA")
        elif f < f_p2:
            frame_bg = p1.copy().convert("RGBA")
        elif f < f_p3:
            frame_bg = p2.copy().convert("RGBA")
        else:
            frame_bg = p3.copy().convert("RGBA")

        # 微距缓推
        scale = 1.000 + 0.035 * (f / float(total_frames))
        new_w = int(WIDTH * scale)
        new_h = int(HEIGHT * scale)
        crop_x = max(0, min(new_w - WIDTH, int((new_w - WIDTH) * 0.5)))
        crop_y = max(0, min(new_h - HEIGHT, int((new_h - HEIGHT) * 0.5)))
        scaled = frame_bg.resize((new_w, new_h), Image.Resampling.BILINEAR)
        frame_final = scaled.crop((crop_x, crop_y, crop_x + WIDTH, crop_y + HEIGHT)).convert("RGBA")

        # 字幕匹配
        sub_text = ""
        for seg in manifest_s4:
            if seg["start"] <= t <= seg["end"]:
                sub_text = seg["text"]
                break
        draw_subtitle_pill(frame_final, sub_text)

        proc.stdin.write(frame_final.tobytes())

    proc.stdin.close()
    proc.wait()

    # 抽取末帧作为 Scene 05 翻书锚点
    anchor_path = os.path.join(DEMO_DIR, "Scene04_结尾最后一帧_yunxi.png")
    frame_final.convert("RGB").save(anchor_path)
    print(f"[SUCCESS] Scene 04 重渲完毕: {OUTPUT_SCENE4_VIDEO}")

def assemble_master():
    print("=== 4. 终极大片全线大合流汇编 ===")
    cmd_run = "python scripts/assemble_yunxi_master.py"
    subprocess.run(cmd_run, shell=True, check=True)

if __name__ == "__main__":
    patch_scene04_images()
    m4 = asyncio.run(build_scene_04_audio())
    render_scene_04(m4)
    assemble_master()
