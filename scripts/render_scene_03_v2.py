import os
import sys
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"d:\video\视频3"
DEMO_DIR = os.path.join(BASE_DIR, "素材", "04_分幕原生画卷")
AUDIO_FILE = os.path.join(BASE_DIR, "output", "audio", "scene3_v3_master_audio.wav")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "video", "scene_03_animated_v2.mp4")
QA_DIR = os.path.join(BASE_DIR, "output", "qa_frames", "scene_03")

os.makedirs(QA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

FONT_HEAVY = r"C:\Windows\Fonts\msyhbd.ttc"
if not os.path.exists(FONT_HEAVY):
    FONT_HEAVY = r"C:\Windows\Fonts\msyh.ttc"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_FRAMES = 414  # 13.800 seconds @ 30fps

def get_subtitle(f):
    # 0 - 15: 翻书过渡
    # 15 - 96 (0.50s - 3.20s): 点击挑战，你的对手比真实客户更挑剔！
    # 96 - 108: 气口空白
    # 108 - 220 (3.60s - 7.35s): AI 瞬间化身各种刁钻性格的客户，逼真模拟高压通话。
    # 220 - 234: 气口空白
    # 234 - 276 (7.80s - 9.20s): 在零风险的安全屋里，
    # 276 - 285: 气口空白
    # 285 - 396 (9.50s - 13.20s): 把所有怯场和大脑空白，在正式开单前全部排雷！
    # 396 - 414: 收尾留白
    if f < 15:
        return ""
    elif f <= 96:
        return "点击挑战，你的对手比真实客户更挑剔！"
    elif f < 108:
        return ""
    elif f <= 220:
        return "AI 瞬间化身各种刁钻性格的客户，逼真模拟高压通话。"
    elif f < 234:
        return ""
    elif f <= 276:
        return "在零风险的安全屋里，"
    elif f < 285:
        return ""
    elif f <= 396:
        return "把所有怯场和大脑空白，在正式开单前全部排雷！"
    else:
        return ""

def draw_subtitle_pill(canvas, text):
    if not text:
        return
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT_HEAVY, 36)
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

def draw_stamp_badge(canvas, text, cx, cy, color, border_color, scale=1.0):
    if scale <= 0.05:
        return
    font_size = int(28 * scale)
    if font_size < 10:
        return
    font = ImageFont.truetype(FONT_HEAVY, font_size)
    dummy = ImageDraw.Draw(canvas)
    bbox = dummy.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    pad_x = int(22 * scale)
    pad_y = int(10 * scale)
    bw = tw + pad_x * 2
    bh = th + pad_y * 2
    
    stamp_layer = Image.new('RGBA', (bw + 20, bh + 20), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(stamp_layer)
    
    s_draw.rounded_rectangle([(4, 4), (bw + 16, bh + 16)], radius=int(10*scale), outline=border_color, width=max(1, int(3*scale)))
    s_draw.rounded_rectangle([(8, 8), (bw + 12, bh + 12)], radius=int(7*scale), outline=border_color, width=max(1, int(1*scale)))
    s_draw.rounded_rectangle([(10, 10), (bw + 10, bh + 10)], radius=int(6*scale), fill=(255, 255, 255, int(225*scale)))
    s_draw.text((10 + pad_x, 10 + pad_y), text, font=font, fill=color)
    
    rot_stamp = stamp_layer.rotate(-4, resample=Image.Resampling.BICUBIC, expand=True)
    rw, rh = rot_stamp.size
    canvas.alpha_composite(rot_stamp, (cx - rw // 2, cy - rh // 2))

def draw_click_pulse(canvas, cx, cy, progress):
    if progress <= 0 or progress >= 1.0:
        return
    radius = int(30 + 80 * progress)
    alpha = int(220 * (1.0 - progress))
    pulse_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(pulse_layer)
    d.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], outline=(255, 140, 56, alpha), width=5)
    inner_r = max(5, radius - 12)
    d.ellipse([(cx - inner_r, cy - inner_r), (cx + inner_r, cy + inner_r)], outline=(255, 255, 255, int(alpha * 0.8)), width=3)
    canvas.alpha_composite(pulse_layer)

def main():
    print("=== 开始渲染全新第三幕 (Scene 03 v2 · 恒定自然语速 + 完美衔接第二幕片尾) ===")
    print(f"规格: {WIDTH}x{HEIGHT} @ {FPS}fps, 总帧数: {TOTAL_FRAMES} (严格 13.800s)")
    print(f"音频: {AUDIO_FILE}")
    print(f"成片输出: {OUTPUT_VIDEO}")
    
    # 1. 载入画卷资产
    # 核心要点：严格使用第二幕的最终帧作为起始翻页底板，确保 100% 无缝衔接！
    p0_path = os.path.join(DEMO_DIR, "Scene02_结尾最后一帧.png")
    if not os.path.exists(p0_path):
        # 兜底
        p0_path = os.path.join(DEMO_DIR, "Scene02_破局重塑_Pose5_握拳打满.jpg")
        
    p1_path = os.path.join(DEMO_DIR, "Scene03_拟真对攻_Pose1_食指指向.jpg")
    p2_path = os.path.join(DEMO_DIR, "Scene03_拟真对攻_Pose2_扶眼镜吃惊.jpg")
    p3_path = os.path.join(DEMO_DIR, "Scene03_拟真对攻_Pose3_双手抱胸自信.jpg")
    
    p0_img = Image.open(p0_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
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
    
    qa_frames_to_save = {10, 40, 150, 255, 340, 405}
    
    for f in range(TOTAL_FRAMES):
        # 1. 翻书转场与动作定格瞬切
        if f < 21:
            # 0.0s - 0.70s: 从上一幕(Scene 02)片尾最后一帧翻入 Scene 03
            p_turn = f / 21.0
            frame_base = create_page_turn(p0_img, p1_img, p_turn)
        else:
            if f < 108:
                # 0.70s - 3.60s: Pose 1 (食指平指，点击挑战，对手更挑剔)
                frame_base = p1_img.copy()
            elif f < 234:
                # 3.60s - 7.80s: Pose 2 (扶眼镜吃惊，刁钻性格高压通话)
                frame_base = p2_img.copy()
            else:
                # 7.80s - 13.80s: Pose 3 (双手抱胸自信微笑，零风险安全屋全部排雷)
                frame_base = p3_img.copy()
                
        frame_canvas = frame_base.convert("RGBA")
        
        # 2. 点击挑战光环脉冲动效 (24 ~ 46 帧, 0.8s ~ 1.5s)
        if 24 <= f <= 46:
            p_pulse = (f - 24) / 22.0
            draw_click_pulse(frame_canvas, 376, 1440, p_pulse)
            
        # 3. 复古手账印章微动效
        # 3.1 零风险实战安全屋印章 (234 ~ 290 帧)
        if f >= 234:
            if f < 246:
                t = (f - 234) / 12.0
                scale_badge1 = 1.0 + 0.35 * math.sin(t * math.pi)
            else:
                scale_badge1 = 1.0
            draw_stamp_badge(frame_canvas, "★ 零风险实战安全屋 ★", 380, 535, (26, 92, 56, 255), (26, 92, 56, 200), scale_badge1)
            
        # 3.2 高压全部排雷 PASS 印章 (290 ~ 414 帧)
        if f >= 290:
            if f < 302:
                t2 = (f - 290) / 12.0
                scale_badge2 = 1.0 + 0.40 * math.sin(t2 * math.pi)
            else:
                scale_badge2 = 1.0
            draw_stamp_badge(frame_canvas, "★ 全部排雷 PASS ★", 290, 1140, (217, 56, 58, 255), (217, 56, 58, 200), scale_badge2)
            
        # 4. 镜头平滑慢推 (Slow Push-in: 1.000x -> 1.035x)，彻底去除伪正弦微晃 (0 wiggle)
        scale = 1.000 + 0.035 * (f / TOTAL_FRAMES)
        new_w = int(WIDTH * scale)
        new_h = int(HEIGHT * scale)
        
        crop_x = int((new_w - WIDTH) * 0.5)
        crop_y = int((new_h - HEIGHT) * 0.5)
        
        scaled_frame = frame_canvas.resize((new_w, new_h), Image.Resampling.BILINEAR)
        frame_final = scaled_frame.crop((crop_x, crop_y, crop_x + WIDTH, crop_y + HEIGHT)).convert("RGBA")
        
        # 5. 居中圆角胶囊字幕
        sub_text = get_subtitle(f)
        draw_subtitle_pill(frame_final, sub_text)
        
        # 6. 提取 QA 验收关键帧
        if f in qa_frames_to_save:
            qa_path = os.path.join(QA_DIR, f"frame_{f:03d}.png")
            frame_final.save(qa_path)
            print(f"[QA] 提取关键帧 {f} -> {qa_path}")
            
        proc.stdin.write(frame_final.tobytes())
        
        if (f + 1) % 50 == 0 or f == TOTAL_FRAMES - 1:
            print(f"渲染进度: {f + 1}/{TOTAL_FRAMES} 帧 ({(f + 1) / TOTAL_FRAMES * 100:.1f}%)")
            
    proc.stdin.close()
    proc.wait()
    print(f"\n[SUCCESS] Scene 03 Master Render Completed! Saved to: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
