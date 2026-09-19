import os
import sys
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"d:\video\视频3"
ASSET_DIR = os.path.join(BASE_DIR, "素材", "05_分层动画切片")
DEMO_DIR = os.path.join(BASE_DIR, "素材", "04_分幕原生画卷")
AUDIO_FILE = os.path.join(BASE_DIR, "output", "audio", "scene2_master_audio.wav")
OUTPUT_VIDEO = os.path.join(BASE_DIR, "output", "video", "scene_02_animated.mp4")

FONT_HEAVY = r"C:\Windows\Fonts\msyhbd.ttc"
if not os.path.exists(FONT_HEAVY):
    FONT_HEAVY = r"C:\Windows\Fonts\msyh.ttc"

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_FRAMES = 360  # 12.00 seconds @ 30fps

def get_subtitle(frame):
    # 0 - 54 (0.0s - 1.8s): 别担心，只是你练少了！
    # 54 - 96 (1.8s - 3.2s): 主管忙、没空教？
    # 96 - 186 (3.2s - 6.2s): 好帮手 AI 学习助手重磅上线——话术私教！
    # 186 - 270 (6.2s - 9.0s): 从开场白、报价到促成，24 关实战异议地图
    # 270 - 360 (9.0s - 12.0s): 随时随地像打游戏一样刷满肌肉记忆。
    if frame < 54:
        return "别担心，只是你练少了！"
    elif frame < 96:
        return "主管忙、没空教？"
    elif frame < 186:
        return "好帮手 AI 学习助手重磅上线——话术私教！"
    elif frame < 270:
        return "从开场白、报价到促成，24 关实战异议地图"
    else:
        return "随时随地像打游戏一样刷满肌肉记忆。"

def draw_subtitle_pill(canvas, text):
    if not text:
        return
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT_HEAVY, 36)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    pad_x = 32
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
        
        # 阴影层 (投影到下一页 img_b 上)
        shadow_img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow_img)
        
        shadow_dist = int(curl_w * 1.6)
        for s in range(shadow_dist):
            ratio = s / max(1, shadow_dist)
            alpha = int(160 * ((1.0 - ratio) ** 2.0) * math.sin(math.pi * progress))
            s_draw.line([(top_x + s, 0), (bot_x + s, HEIGHT)], fill=(20, 15, 10, alpha), width=2)
            
        # 卷边圆柱高光与背面暗角
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

def apply_orange_sweep(img, progress, y_top, y_bot, x_start=125, x_end=420):
    """
    荧光橙扫掠划线高光动效 (Fluorescent Marker Sweep)
    """
    if progress <= 0.0:
        return img
    
    sweep_x = int(x_start + (x_end - x_start) * min(1.0, progress))
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    
    # 荧光黄色/橙色扫光条
    h = y_bot - y_top
    d.rounded_rectangle([(x_start, y_top), (sweep_x, y_bot)], radius=8, fill=(255, 215, 50, 75))
    
    # 扫掠光晕边缘 (White hot sweep leading edge)
    if sweep_x < x_end:
        edge_w = 20
        d.rectangle([(max(x_start, sweep_x - edge_w), y_top), (sweep_x, y_bot)], fill=(255, 255, 255, 120))
        
    return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')

def main():
    print("=== 开始渲染第二幕高能手账定格成片 (Scene 2 Master) ===")
    print(f"规格: {WIDTH}x{HEIGHT} @ {FPS}fps, 总帧数: {TOTAL_FRAMES} (12.00s)")
    print(f"音频: {AUDIO_FILE}")
    print(f"输出: {OUTPUT_VIDEO}")
    
    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)
    
    # 1. 载入核心画卷
    # 上一幕收尾画卷 (用于起始 20 帧翻书页转场)
    prev_scene_plate = Image.open(os.path.join(DEMO_DIR, "Scene01B_危机清单_挠后脑勺.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    # 本幕动作 1 (食指平指卡片)
    pose1_img = Image.open(os.path.join(DEMO_DIR, "Scene02_破局重塑_24关地图.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    # 本幕动作 2 (手托上挑引导，同底直出)
    pose2_img = Image.open(os.path.join(DEMO_DIR, "Scene02_破局重塑_24关地图_手托引导.jpg")).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    # 启动 FFmpeg 写入管道
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
    
    for f in range(TOTAL_FRAMES):
        if f < 20:
            # ================= 阶段 1：上一幕翻入本幕 (0.0s - 0.67s / 20 帧) =================
            p_turn = f / 20.0
            frame_base = create_page_turn(prev_scene_plate, pose2_img, p_turn)
            cur_pose = pose2_img
        else:
            # ================= 阶段 2：破局重塑 · 24关地图内容主段 (0.67s - 12.0s) =================
            # 姿态根据台词与节奏卡点智能抽帧瞬切：
            # 20 - 96 (0.67s - 3.2s) "别担心，只是你练少了！主管忙、没空教？" -> Pose 2 (热情手托)
            # 96 - 140 (3.2s - 4.67s) "好帮手 AI 学习助手重磅上线" -> Pose 1 (食指平指)
            # 140 - 186 (4.67s - 6.2s) "话术私教！" -> Pose 2 (热情手托)
            # 186 - 235 (6.2s - 7.83s) "从开场白、报价到促成" -> Pose 1 (食指平指点地图)
            # 235 - 270 (7.83s - 9.0s) "24 关实战异议地图" -> Pose 2 (热情手托)
            # 270 - 315 (9.0s - 10.5s) "随时随地像打游戏一样" -> Pose 1 (食指平指)
            # 315 - 360 (10.5s - 12.0s) "刷满肌肉记忆。" -> Pose 2 (热情手托收尾)
            if f < 96:
                cur_pose = pose2_img
            elif f < 140:
                cur_pose = pose1_img
            elif f < 186:
                cur_pose = pose2_img
            elif f < 235:
                cur_pose = pose1_img
            elif f < 270:
                cur_pose = pose2_img
            elif f < 315:
                cur_pose = pose1_img
            else:
                cur_pose = pose2_img
                
            frame_base = cur_pose.copy()
            
            # 荧光橙马克笔动态扫掠动效：
            # 在 190 - 240 帧 (6.3s - 8.0s) 念到 "从开场白、报价到促成" 时扫过
            if 190 <= f <= 250:
                # 扫过 "开场白训练" (Y: 674~723)
                prog_high1 = (f - 190) / 25.0
                frame_base = apply_orange_sweep(frame_base, prog_high1, 674, 723, 125, 416)
                
                # 扫过 "促成" (Y: 1258~1306)
                prog_high2 = (f - 210) / 25.0
                frame_base = apply_orange_sweep(frame_base, prog_high2, 1258, 1306, 125, 416)
            elif f > 250:
                # 扫过后的常驻亮显
                frame_base = apply_orange_sweep(frame_base, 1.0, 674, 723, 125, 416)
                frame_base = apply_orange_sweep(frame_base, 1.0, 1258, 1306, 125, 416)
                
        # 纸偶常驻微晃 (Zero-Static Idle Wiggle) 与镜头推进 (Slow Push-in)
        # 镜头缩放 (1.00x -> 1.045x)
        scale = 1.000 + 0.045 * (f / TOTAL_FRAMES)
        new_w = int(WIDTH * scale)
        new_h = int(HEIGHT * scale)
        
        # 微呼吸摇摆偏移 (±1.2° 等效位移与上下呼吸)
        wiggle_x = int(math.sin(f * 0.13) * 4.0)
        wiggle_y = int(math.sin(f * 0.09) * 2.5)
        
        crop_x = int((new_w - WIDTH) * 0.5) + wiggle_x
        crop_y = int((new_h - HEIGHT) * 0.5) + wiggle_y
        
        scaled_frame = frame_base.resize((new_w, new_h), Image.Resampling.BILINEAR)
        frame_img = scaled_frame.crop((crop_x, crop_y, crop_x + WIDTH, crop_y + HEIGHT)).convert("RGBA")
        
        # 绘制底部字幕胶囊
        sub_text = get_subtitle(f)
        draw_subtitle_pill(frame_img, sub_text)
        
        # 写入 FFmpeg 管道
        proc.stdin.write(frame_img.tobytes())
        
        if f % 45 == 0 or f == TOTAL_FRAMES - 1:
            print(f"渲染进度: {f + 1}/{TOTAL_FRAMES} 帧 ({(f + 1) / TOTAL_FRAMES * 100:.1f}%)")
            
    proc.stdin.close()
    proc.wait()
    print(f"渲染完成！Scene 02 成片保存在: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    main()
