import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = r"d:\video\视频3"
ASSET_DIR = os.path.join(BASE_DIR, "素材")
SLICE_DIR = os.path.join(ASSET_DIR, "05_分层动画切片")
STICKER_DIR = os.path.join(ASSET_DIR, "02_透明纸片人贴纸")
UI_DIR = os.path.join(ASSET_DIR, "03_业务界面与UI")
DEMO_DIR = os.path.join(ASSET_DIR, "04_分幕原生画卷")
QA_DIR = os.path.join(BASE_DIR, "output", "qa_frames", "scene_05")
os.makedirs(QA_DIR, exist_ok=True)

WIDTH = 1080
HEIGHT = 1920

FONT_HEAVY = r"C:\Windows\Fonts\msyhbd.ttc"
if not os.path.exists(FONT_HEAVY):
    FONT_HEAVY = r"C:\Windows\Fonts\msyh.ttc"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"

def create_card(w, h, bg_color=(248, 245, 240, 255), border_color=(218, 212, 204, 255), radius=22, shadow_blur=16):
    """Create a textured rounded paper card with soft ambient drop shadow"""
    pad = shadow_blur * 2 + 10
    total_w = w + pad * 2
    total_h = h + pad * 2
    
    # Shadow
    shadow = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([(pad + 4, pad + 10), (pad + w + 4, pad + h + 10)], radius=radius, fill=(20, 16, 12, 50))
    shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
    
    # Card
    card = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    c_draw = ImageDraw.Draw(card)
    c_draw.rounded_rectangle([(pad, pad), (pad + w, pad + h)], radius=radius, fill=bg_color, outline=border_color, width=2)
    
    res = Image.alpha_composite(shadow, card)
    return res, pad

def create_retry_stamp():
    """Create a vintage retro stamp / button for '再练一次'"""
    w, h = 340, 110
    pad = 25
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    
    # Soft shadow
    s_draw = ImageDraw.Draw(img)
    s_draw.rounded_rectangle([(pad + 3, pad + 8), (pad + w + 3, pad + h + 8)], radius=18, fill=(20, 15, 10, 60))
    img = img.filter(ImageFilter.GaussianBlur(10))
    
    # Stamp layer
    stamp = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(stamp)
    
    # Warm cream background with cinnabar red double border
    d.rounded_rectangle([(pad, pad), (pad + w, pad + h)], radius=18, fill=(255, 252, 248, 255), outline=(217, 56, 58, 255), width=3)
    d.rounded_rectangle([(pad + 6, pad + 6), (pad + w - 6, pad + h - 6)], radius=14, outline=(217, 56, 58, 140), width=1)
    
    # Text: 再练一次
    font = ImageFont.truetype(FONT_HEAVY, 44)
    text = "再 练 一 次"
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = pad + (w - tw) // 2
    ty = pad + (h - th) // 2 - 4
    d.text((tx, ty), text, font=font, fill=(217, 56, 58, 255))
    
    # Draw simple clean replay arc on the left
    arc_cx = tx - 30
    arc_cy = ty + th // 2 + 2
    r_arc = 12
    d.arc([(arc_cx - r_arc, arc_cy - r_arc), (arc_cx + r_arc, arc_cy + r_arc)], start=40, end=310, fill=(217, 56, 58, 255), width=3)
    # Arrow head
    d.polygon([(arc_cx + 8, arc_cy - 12), (arc_cx + 16, arc_cy - 6), (arc_cx + 14, arc_cy - 16)], fill=(217, 56, 58, 255))
        
    return Image.alpha_composite(img, stamp)

def create_app_icon_badge():
    """Create official app icon with rounded die-cut white border and shadow"""
    raw_icon = Image.open(os.path.join(UI_DIR, "好帮手APP图标.png")).convert("RGBA")
    raw_icon = raw_icon.resize((150, 150), Image.Resampling.LANCZOS)
    
    # Apply rounded mask
    mask = Image.new("L", (150, 150), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.rounded_rectangle([(0, 0), (150, 150)], radius=32, fill=255)
    
    icon_rounded = Image.new("RGBA", (150, 150), (0, 0, 0, 0))
    icon_rounded.paste(raw_icon, (0, 0), mask=mask)
    
    # White border + shadow
    pad = 30
    w, h = 150 + pad * 2, 150 + pad * 2
    res = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    
    # Shadow
    s_draw = ImageDraw.Draw(res)
    s_draw.rounded_rectangle([(pad + 3, pad + 10), (pad + 150 + 3, pad + 150 + 10)], radius=34, fill=(20, 15, 10, 70))
    res = res.filter(ImageFilter.GaussianBlur(12))
    
    # White border
    border_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(border_layer)
    b_draw.rounded_rectangle([(pad - 5, pad - 5), (pad + 150 + 5, pad + 150 + 5)], radius=36, fill=(255, 255, 255, 255))
    border_layer.paste(icon_rounded, (pad, pad), mask=icon_rounded)
    
    return Image.alpha_composite(res, border_layer)

def build_base_background():
    """Build a completely clean magazine scrapbook base plate for Scene 05"""
    # Load raw magazine paper bg with fold crease and grid
    bg_paper = Image.open(os.path.join(SLICE_DIR, "magazine_paper_bg_1080x1920.png")).convert("RGBA")
    
    # Overlay the pencil from scene1_clean_background at bottom left
    clean_ref = Image.open(os.path.join(SLICE_DIR, "scene1_clean_background.png")).convert("RGBA")
    # Pencil is in the bottom left area: X: 0~350, Y: 1400~1920
    pencil_crop = clean_ref.crop((0, 1400, 360, 1920))
    bg_paper.paste(pencil_crop, (0, 1400), mask=pencil_crop)
    
    # Left margin text: CASE STUDY 05
    d = ImageDraw.Draw(bg_paper)
    font_margin = ImageFont.truetype(FONT_MONO, 24)
    # Create vertical text image
    margin_img = Image.new("RGBA", (300, 40), (0, 0, 0, 0))
    md = ImageDraw.Draw(margin_img)
    md.text((0, 5), "CASE STUDY 05 // FINALE", font=font_margin, fill=(150, 145, 140, 220))
    margin_rot = margin_img.rotate(90, expand=True)
    bg_paper.paste(margin_rot, (25, 620), mask=margin_rot)
    
    # Stage 05 Header
    font_mono = ImageFont.truetype(FONT_MONO, 28)
    d.text((95, 95), "STAGE 05 // MASTERY & ACTION", font=font_mono, fill=(110, 105, 100, 255))
    
    font_title = ImageFont.truetype(FONT_HEAVY, 66)
    d.text((90, 138), "通关升华 · 开启销冠之旅", font=font_title, fill=(32, 30, 28, 255))
    
    # Hand-drawn underlines
    d.line([(90, 220), (840, 220)], fill=(32, 30, 28, 180), width=4)
    d.line([(95, 225), (830, 225)], fill=(32, 30, 28, 90), width=2)
    
    return bg_paper

def build_test_frame_v2():
    canvas = build_base_background()
    draw = ImageDraw.Draw(canvas)
    
    # Jiabin thumbs up sticker
    jiabin = Image.open(os.path.join(STICKER_DIR, "贴纸_点赞_clean.png")).convert("RGBA")
    
    # 1. Card 1: 肌肉记忆 · 再练一次
    card1, pad1 = create_card(460, 460, radius=22)
    c1_x, c1_y = 75, 270
    canvas.paste(card1, (c1_x - pad1, c1_y - pad1), mask=card1)
    
    # Card 1 Content
    font_c1_tag = ImageFont.truetype(FONT_HEAVY, 24)
    draw.rounded_rectangle([(c1_x + 28, c1_y + 28), (c1_x + 190, c1_y + 68)], radius=8, fill=(255, 140, 56, 255))
    draw.text((c1_x + 40, c1_y + 34), "智能纠偏排雷", font=font_c1_tag, fill=(255, 255, 255, 255))
    
    font_c1_h = ImageFont.truetype(FONT_HEAVY, 40)
    draw.text((c1_x + 28, c1_y + 85), "哪里卡壳，一键重练", font=font_c1_h, fill=(32, 30, 28, 255))
    
    font_c1_body = ImageFont.truetype(FONT_REG, 26)
    draw.text((c1_x + 28, c1_y + 145), "模拟实战高压对攻", font=font_c1_body, fill=(90, 85, 80, 255))
    draw.text((c1_x + 28, c1_y + 185), "在零风险安全屋反复排雷", font=font_c1_body, fill=(90, 85, 80, 255))
    
    # Highlight bar for '金牌话术 -> 本能应变'
    draw.rounded_rectangle([(c1_x + 28, c1_y + 240), (c1_x + 430, c1_y + 295)], radius=8, fill=(255, 220, 60, 95))
    font_c1_bold = ImageFont.truetype(FONT_HEAVY, 30)
    draw.text((c1_x + 40, c1_y + 250), "金牌话术  ➔  本能应变", font=font_c1_bold, fill=(217, 56, 58, 255))
    
    # Retry Stamp Button
    retry_stamp = create_retry_stamp()
    retry_stamp = retry_stamp.resize((int(retry_stamp.width * 0.95), int(retry_stamp.height * 0.95)), Image.Resampling.LANCZOS)
    canvas.paste(retry_stamp, (c1_x + 35, c1_y + 315), mask=retry_stamp)
    
    # 2. Card 2: 立即行动 · 好帮手 APP
    card2, pad2 = create_card(460, 560, radius=22)
    c2_x, c2_y = 790, 800
    # Wait, c2_x should be 75
    c2_x, c2_y = 75, 780
    canvas.paste(card2, (c2_x - pad2, c2_y - pad2), mask=card2)
    
    # Card 2 Content
    app_badge = create_app_icon_badge()
    app_badge = app_badge.resize((int(app_badge.width * 0.85), int(app_badge.height * 0.85)), Image.Resampling.LANCZOS)
    canvas.paste(app_badge, (c2_x + 15, c2_y + 20), mask=app_badge)
    
    font_app_title = ImageFont.truetype(FONT_HEAVY, 42)
    draw.text((c2_x + 200, c2_y + 40), "好帮手 APP", font=font_app_title, fill=(32, 30, 28, 255))
    
    font_app_sub = ImageFont.truetype(FONT_REG, 24)
    draw.text((c2_x + 200, c2_y + 95), "官方学习助手", font=font_app_sub, fill=(120, 115, 110, 255))
    
    # Action guide box
    draw.rounded_rectangle([(c2_x + 28, c2_y + 195), (c2_x + 430, c2_y + 280)], radius=12, fill=(255, 244, 235, 255), outline=(255, 140, 56, 200), width=2)
    font_step = ImageFont.truetype(FONT_HEAVY, 32)
    draw.text((c2_x + 48, c2_y + 218), "进入【话术私教】", font=font_step, fill=(235, 100, 20, 255))
    
    # Arrow doodle
    draw.polygon([(c2_x + 220, c2_y + 300), (c2_x + 240, c2_y + 300), (c2_x + 230, c2_y + 318)], fill=(255, 140, 56, 255))
    
    # Final goal banner
    draw.rounded_rectangle([(c2_x + 28, c2_y + 340), (c2_x + 430, c2_y + 500)], radius=16, fill=(32, 30, 28, 255))
    font_goal_top = ImageFont.truetype(FONT_REG, 26)
    draw.text((c2_x + 50, c2_y + 368), "随时随地 · 刷满肌肉记忆", font=font_goal_top, fill=(220, 215, 205, 255))
    font_goal_bot = ImageFont.truetype(FONT_HEAVY, 34)
    draw.text((c2_x + 50, c2_y + 420), "开启你的销冠通关之旅！", font=font_goal_bot, fill=(255, 215, 50, 255))
    
    # 3. Jiabin thumbs-up sticker on the right
    scale_j = 1530 / jiabin.height
    jw = int(jiabin.width * scale_j)
    jh = int(jiabin.height * scale_j)
    jiabin_scaled = jiabin.resize((jw, jh), Image.Resampling.LANCZOS)
    
    jx = WIDTH - jw - 15
    jy = HEIGHT - jh - 40
    canvas.paste(jiabin_scaled, (jx, jy), mask=jiabin_scaled)
    
    # 4. Draw Subtitle pill
    draw_subtitle_pill(canvas, "开启你的销冠通关之旅吧！")
    
    out_test = os.path.join(QA_DIR, "test_composite_v2.png")
    canvas.save(out_test)
    print(f"Saved test composite v2 to {out_test}")

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

if __name__ == "__main__":
    build_test_frame_v2()
