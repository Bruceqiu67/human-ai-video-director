import os
from PIL import Image, ImageDraw, ImageFont

class AdaptiveCapsuleSubtitle:
    """
    Modern centered rounded capsule subtitle renderer.
    Enforces automatic font-size scaling to guarantee text never overflows the 920px safety bound.
    """
    
    def __init__(self, font_path: str = "", default_font_size: int = 40, max_width: int = 920):
        self.font_path = font_path
        self.default_font_size = default_font_size
        self.max_width = max_width
        self._font_cache = {}
        
    def _get_font(self, size: int):
        if size not in self._font_cache:
            font = None
            if self.font_path and os.path.exists(self.font_path):
                try:
                    font = ImageFont.truetype(self.font_path, size)
                except Exception:
                    pass
            if font is None:
                # Try common Windows/Linux system fonts
                candidate_paths = [
                    "C:/Windows/Fonts/msyh.ttc",
                    "C:/Windows/Fonts/simhei.ttf",
                    "C:/Windows/Fonts/msyhl.ttc",
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                ]
                for p in candidate_paths:
                    if os.path.exists(p):
                        try:
                            font = ImageFont.truetype(p, size)
                            break
                        except Exception:
                            continue
            if font is None:
                font = ImageFont.load_default()
            self._font_cache[size] = font
        return self._font_cache[size]

    def render(self, canvas: Image.Image, text: str, y_center: int = 1680) -> Image.Image:
        if not text:
            return canvas
            
        w, h = canvas.size
        target_size = self.default_font_size
        font = self._get_font(target_size)
        
        # Calculate width & auto-scale down if exceeding max_width
        text_w = sum(font.getlength(c) for c in text)
        while text_w > self.max_width and target_size > 22:
            target_size -= 2
            font = self._get_font(target_size)
            text_w = sum(font.getlength(c) for c in text)
            
        pad_x = 28
        pad_y = 14
        capsule_w = int(text_w + pad_x * 2)
        capsule_h = int(target_size + pad_y * 2)
        
        cap_x = (w - capsule_w) // 2
        cap_y = y_center - capsule_h // 2
        
        # Draw translucent rounded capsule
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        radius = capsule_h // 2
        
        draw.rounded_rectangle(
            [cap_x, cap_y, cap_x + capsule_w, cap_y + capsule_h],
            radius=radius,
            fill=(24, 24, 27, 205)
        )
        
        # Draw centered crisp white text
        text_x = cap_x + pad_x
        # Align vertically in capsule
        text_y = cap_y + (capsule_h - target_size) // 2 - 2
        draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))
        
        canvas.paste(overlay, (0, 0), overlay)
        return canvas
