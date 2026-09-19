# -*- coding: utf-8 -*-
import os
import sys
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = 'd:/video/视频3'
AUDIO_FILE = os.path.join(BASE_DIR, 'output', 'audio', 'scene4_master_audio.wav')
OUTPUT_VIDEO = os.path.join(BASE_DIR, 'output', 'video', 'scene_04_animated.mp4')
QA_DIR = os.path.join(BASE_DIR, 'output', 'qa_frames', 'scene_04')
DEMO_DIR = os.path.join(BASE_DIR, '素材', '04_分幕原生画卷')

FONT_HEAVY = 'C:/Windows/Fonts/msyhbd.ttc'
if not os.path.exists(FONT_HEAVY):
    FONT_HEAVY = 'C:/Windows/Fonts/msyh.ttc'

WIDTH = 1080
HEIGHT = 1920
FPS = 30
TOTAL_FRAMES = 360

def get_subtitle(f):
    if f < 15:
        return ''
    elif f < 75:
        return '一通练完，AI立刻输出深度体检单！'
    elif f < 112:
        return '第一次只有45分？'
    elif f < 195:
        return '别慌，它给的可不是泛泛的加油，而是指骨到肉的解法：开场白太冗长？直接教你‘利益前置’——'
    elif f < 271:
        return '第一句话抛出‘为您预留了800元续保补贴’，'
    else:
        return '一秒锁死客户注意力！'

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
    print('=== 开始渲染 Scene 04 (深度诊断 · 45分体检与利益前置) 原生画卷升级版 ===')
    os.makedirs(QA_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)
    
    prev_scene_path = os.path.join(QA_DIR, '..', 'scene_03', 'frame_310.png')
    if not os.path.exists(prev_scene_path):
        prev_scene_path = os.path.join(DEMO_DIR, 'Scene03_拟真对攻_Pose3_双手抱胸自信.jpg')
    prev_scene_img = Image.open(prev_scene_path).convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    p1_path = os.path.join(DEMO_DIR, 'Scene04_深度诊断_Pose1_耸肩错愕.jpg')
    p2_path = os.path.join(DEMO_DIR, 'Scene04_深度诊断_Pose2_托腮思考.jpg')
    p3_path = os.path.join(DEMO_DIR, 'Scene04_深度诊断_Pose3_OK自信.jpg')
    
    p1_img = Image.open(p1_path).convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    p2_img = Image.open(p2_path).convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    p3_img = Image.open(p3_path).convert('RGB').resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', str(WIDTH) + 'x' + str(HEIGHT),
        '-pix_fmt', 'rgba',
        '-r', str(FPS),
        '-i', '-',
        '-i', AUDIO_FILE,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'fast',
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '320k',
        '-shortest',
        OUTPUT_VIDEO
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    
    for f in range(TOTAL_FRAMES):
        if f < 21:
            p_turn = f / 21.0
            frame_bg = create_page_turn(prev_scene_img, p1_img, p_turn).convert('RGBA')
        else:
            if f < 112:
                frame_bg = p1_img.copy().convert('RGBA')
            elif f < 195:
                frame_bg = p2_img.copy().convert('RGBA')
            else:
                frame_bg = p3_img.copy().convert('RGBA')
            
        shake_offset_x = 0
        shake_offset_y = 0
        
        if 75 <= f <= 95:
            decay = math.exp(-(f - 75) * 0.18)
            shake_offset_x = int(math.sin((f - 75) * 1.5) * 10 * decay)
            shake_offset_y = int(math.cos((f - 75) * 1.2) * 8 * decay)
            
        scale = 1.000 + 0.045 * (f / TOTAL_FRAMES)
        new_w = int(WIDTH * scale)
        new_h = int(HEIGHT * scale)
        
        crop_x = int((new_w - WIDTH) * 0.5) + shake_offset_x
        crop_y = int((new_h - HEIGHT) * 0.5) + shake_offset_y
        
        scaled = frame_bg.resize((new_w, new_h), Image.Resampling.BILINEAR)
        crop_x = max(0, min(new_w - WIDTH, crop_x))
        crop_y = max(0, min(new_h - HEIGHT, crop_y))
        frame_final = scaled.crop((crop_x, crop_y, crop_x + WIDTH, crop_y + HEIGHT)).convert('RGBA')
        
        sub_text = get_subtitle(f)
        draw_subtitle_pill(frame_final, sub_text)
        
        if f in [15, 75, 115, 160, 220, 310]:
            qa_out = os.path.join(QA_DIR, 'frame_' + str(f).zfill(3) + '.png')
            frame_final.save(qa_out)
            print('[QA] 提取关键帧 ' + str(f) + ' -> ' + qa_out)
            
        proc.stdin.write(frame_final.tobytes())
        
        if f % 60 == 0 or f == TOTAL_FRAMES - 1:
            pct = (f + 1) / TOTAL_FRAMES * 100
            print('渲染进度: ' + str(f + 1) + '/' + str(TOTAL_FRAMES) + ' 帧 (' + '{:.1f}'.format(pct) + '%)')
            
    proc.stdin.close()
    proc.wait()
    print('渲染完成！Scene 04 原生画卷升级版成片已就绪: ' + OUTPUT_VIDEO)

if __name__ == '__main__':
    main()
