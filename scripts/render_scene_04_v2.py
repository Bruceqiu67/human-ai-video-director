# -*- coding: utf-8 -*-
import os
import sys
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = r"d:\video\视频3"
AUDIO_FILE = os.path.join(BASE_DIR, "output", "audio", "scene4_v2_master_audio.wav")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "video", "scene_04_animated_v2.mp4")
QA_DIR = os.path.join(BASE_DIR, "output", "qa_frames", "scene_04")
DEMO_DIR = os.path.join(BASE_DIR, "素材", "04_分幕原生画卷")

os.makedirs(QA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

FONT_HEAVY = r"C:\Windows\Fonts\msyhbd.ttc"
if not os.path.exists(FONT_HEAVY):
    FONT_HEAVY = r"C:\Windows\Fonts\msyh.ttc"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_FRAMES = 510  # 严格 17.000 秒 @ 30fps

def get_subtitle(f):
    # 0 - 14: 翻书转场
    # 15 - 95 (0.50s - 3.17s): 一通练完，AI立刻输出深度体检单！
    # 96 - 104: 气口
    # 105 - 143 (3.50s - 4.76s): 第一次只有45分？
    # 144 - 152: 气口
    # 153 - 216 (5.10s - 7.19s): 别慌，它给的可不是泛泛的加油，
    # 217 - 223: 气口
    # 224 - 264 (7.45s - 8.80s): 而是指骨到肉的解法：
    # 265 - 272: 气口
    # 273 - 361 (9.10s - 12.04s): 开场白太冗长？直接教你‘利益前置’——
    # 362 - 371: 气口
    # 372 - 447 (12.40s - 14.91s): 第一句话抛出‘为您预留了800元续保补贴’，
    # 448 - 455: 气口
    # 456 - 496 (15.20s - 16.53s): 一秒锁死客户注意力！
    # 497 - 510: 收尾留白
    if f < 15:
        return ""
    elif f <= 95:
        return "一通练完，AI立刻输出深度体检单！"
    elif f < 105:
        return ""
    elif f <= 143:
        return "第一次只有45分？"
    elif f < 153:
        return ""
    elif f <= 216:
        return "别慌，它给的可不是泛泛的加油，"
    elif f < 224:
        return ""
    elif f <= 264:
        return "而是指骨到肉的解法："
    elif f < 273:
        return ""
    elif f <= 361:
        return "开场白太冗长？直接教你‘利益前置’——"
    elif f < 372:
        return ""
    elif f <= 447:
        return "第一句话抛出‘为您预留了800元续保补贴’，"
    elif f < 456:
        return ""
    elif f <= 496:
        return "一秒锁死客户注意力！"
    else:
        return ""

def draw_subtitle_pill(canvas, text):
    if not text:
        return
    draw = ImageDraw.Draw(canvas)
    font_size = 36
    font = ImageFont.truetype(FONT_HEAVY, font_size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    # 屏幕安全保护：如果文字总宽加上内边距超过 940px，自动降字号保证绝不出界
    while (tw + 68) > 940 and font_size > 24:
        font_size -= 2
        font = ImageFont.truetype(FONT_HEAVY, font_size)
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
    
    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=18, fill=(32, 30, 28, 230))
    draw.text((cx, cy), text, font=font, fill=(255, 255, 255, 255))

def create_page_turn(img_a, img_b, progress):
    """
    2.5D 手账折页/翻书物理动效 (Magazine Page Flip Physics)
    progress: 0.0 -> 1.0 (从 img_a 翻到 img_b)
    """
    p = progress * progress * (3.0 - 2.0 * progress)
    out = img_b.copy()
    
    curl_w = int(140 * math.sin(math.pi * progress) + 30)
    fold_x = int((1.0 - p) * (WIDTH + curl_w * 2) - curl_w)
    
    if fold_x > 0:
        mask = Image.new('L', (WIDTH, HEIGHT), 0)
        draw_mask = ImageDraw.Draw(mask)
        
        tilt = int(45 * math.sin(math.pi * progress))
        top_x = fold_x - tilt
        bot_x = fold_x + tilt
        
        pts = [(0, 0), (top_x, 0), (bot_x, HEIGHT), (0, HEIGHT)]
        draw_mask.polygon(pts, fill=255)
        out.paste(img_a, (0, 0), mask=mask)
        
        shadow_img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow_img)
        
        shadow_dist = int(curl_w * 1.6)
        for s in range(shadow_dist):
            ratio = s / max(1, shadow_dist)
            alpha = int(160 * ((1.0 - ratio) ** 2.0) * math.sin(math.pi * progress))
            s_draw.line([(top_x + s, 0), (bot_x + s, HEIGHT)], fill=(20, 15, 10, alpha), width=2)
            
        for c in range(curl_w):
            ratio = c / max(1, curl_w)
            crest = max(0.0, 1.0 - abs(ratio - 0.35) * 4.0)
            h_alpha = int(90 * crest * math.sin(math.pi * progress))
            s_alpha = int(100 * (1.0 - ratio) * math.sin(math.pi * progress))
            
            if h_alpha > 0:
                s_draw.line([(top_x - c, 0), (bot_x - c, HEIGHT)], fill=(255, 255, 255, h_alpha), width=2)
            if s_alpha > 0:
                s_draw.line([(top_x - c, 0), (bot_x - c, HEIGHT)], fill=(40, 30, 20, s_alpha), width=2)
                
        out = Image.alpha_composite(out.convert('RGBA'), shadow_img).convert('RGB')
        
    return out

def main():
    print("=== 开始渲染全新第四幕 (Scene 04 v2 · 语速从容化 + 科学分句防溢出) ===")
    print(f"规格: {WIDTH}x{HEIGHT} @ {FPS}fps, 总帧数: {TOTAL_FRAMES} (严格 17.000s)")
    print(f"音频: {AUDIO_FILE}")
    print(f"成片输出: {OUTPUT_VIDEO}")
    
    # 1. 载入画卷资产 (严格使用 Scene 03 真实末帧作为翻页起始页，确保 100% 像素级无缝衔接)
    prev_scene_path = os.path.join(DEMO_DIR, "Scene03_结尾最后一帧.png")
    if not os.path.exists(prev_scene_path):
        prev_scene_path = os.path.join(DEMO_DIR, "Scene03_拟真对攻_Pose3_双手抱胸自信.jpg")
    prev_scene_img = Image.open(prev_scene_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    p1_path = os.path.join(DEMO_DIR, "Scene04_深度诊断_Pose1_耸肩错愕.jpg")
    p2_path = os.path.join(DEMO_DIR, "Scene04_深度诊断_Pose2_托腮思考.jpg")
    p3_path = os.path.join(DEMO_DIR, "Scene04_深度诊断_Pose3_OK自信.jpg")
    
    p1_img = Image.open(p1_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    p2_img = Image.open(p2_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    p3_img = Image.open(p3_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgba",
        "-r", str(FPS),
        "-i", "-",
        "-i", AUDIO_FILE,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "320k",
        "-shortest",
        OUTPUT_VIDEO
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    
    qa_frames_to_save = {10, 60, 115, 180, 240, 310, 410, 480}
    
    for f in range(TOTAL_FRAMES):
        # 1. 翻书转场与三姿态定格瞬切
        if f < 21:
            # 0.0s - 0.70s: 从上一幕 (Scene 03) 片尾最后一帧翻入 Scene 04
            p_turn = f / 21.0
            frame_bg = create_page_turn(prev_scene_img, p1_img, p_turn).convert("RGBA")
        else:
            if f < 153:
                # 0.70s - 5.10s: Pose 1 耸肩错愕 (体检单输出，看到 45 分)
                frame_bg = p1_img.copy().convert("RGBA")
            elif f < 366:
                # 5.10s - 12.20s: Pose 2 托腮思考 (研读 AI 体检单深度解法与利益前置)
                frame_bg = p2_img.copy().convert("RGBA")
            else:
                # 12.20s - 17.00s: Pose 3 OK自信 (OK手势，一秒锁死客户注意力)
                frame_bg = p3_img.copy().convert("RGBA")
                
        # 2. 45 分印章重砸微幅衰减震颤 (106 ~ 126 帧, 3.55s ~ 4.20s)
        shake_offset_x = 0
        shake_offset_y = 0
        if 106 <= f <= 126:
            decay = math.exp(-(f - 106) * 0.18)
            shake_offset_x = int(math.sin((f - 106) * 1.5) * 8 * decay)
            shake_offset_y = int(math.cos((f - 106) * 1.2) * 6 * decay)
            
        # 3. 镜头微距平滑缓推 (1.000x -> 1.035x)
        scale = 1.000 + 0.035 * (f / TOTAL_FRAMES)
        new_w = int(WIDTH * scale)
        new_h = int(HEIGHT * scale)
        
        crop_x = int((new_w - WIDTH) * 0.5) + shake_offset_x
        crop_y = int((new_h - HEIGHT) * 0.5) + shake_offset_y
        
        scaled = frame_bg.resize((new_w, new_h), Image.Resampling.BILINEAR)
        crop_x = max(0, min(new_w - WIDTH, crop_x))
        crop_y = max(0, min(new_h - HEIGHT, crop_y))
        frame_final = scaled.crop((crop_x, crop_y, crop_x + WIDTH, crop_y + HEIGHT)).convert("RGBA")
        
        # 4. 绘制自适应居中圆角胶囊字幕
        sub_text = get_subtitle(f)
        draw_subtitle_pill(frame_final, sub_text)
        
        # 5. 提取 QA 走查关键帧
        if f in qa_frames_to_save:
            qa_out = os.path.join(QA_DIR, f"frame_{f:03d}.png")
            frame_final.save(qa_out)
            print(f"[QA] 提取关键帧 {f} -> {qa_out}")
            
        proc.stdin.write(frame_final.tobytes())
        
        if (f + 1) % 60 == 0 or f == TOTAL_FRAMES - 1:
            pct = (f + 1) / TOTAL_FRAMES * 100
            print(f"渲染进度: {f + 1}/{TOTAL_FRAMES} 帧 ({pct:.1f}%)")
            
    proc.stdin.close()
    proc.wait()
    print(f"\n[SUCCESS] Scene 04 v2 Render Completed! Saved to: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
