import math
from PIL import Image, ImageDraw, ImageFilter

class PageFlipTransition:
    """
    Simulates a 2.5D physical page curl / flip transition from right to left.
    progress: 0.0 (showing prev_img) -> 1.0 (showing next_img)
    """
    
    @staticmethod
    def render(prev_img: Image.Image, next_img: Image.Image, progress: float) -> Image.Image:
        if progress <= 0.0:
            return prev_img.copy()
        if progress >= 1.0:
            return next_img.copy()
            
        w, h = prev_img.size
        # Ease in-out cubic
        p = 0.5 - 0.5 * math.cos(progress * math.pi)
        
        # Curl fold x-coordinate moving from w down to 0
        fold_x = int(w * (1.0 - p))
        
        canvas = next_img.copy()
        
        # The remaining un-flipped portion of prev_img on the left
        if fold_x > 0:
            left_slice = prev_img.crop((0, 0, fold_x, h))
            canvas.paste(left_slice, (0, 0))
            
            # Draw fold crease shadow along the fold edge
            shadow_w = min(48, int(w * 0.05))
            shadow_x = max(0, fold_x - shadow_w)
            shadow_overlay = Image.new("RGBA", (shadow_w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(shadow_overlay)
            
            for i in range(shadow_w):
                # Gradient shadow fading to left
                alpha = int(140 * (i / shadow_w) * (1.0 - p * 0.5))
                draw.line([(i, 0), (i, h)], fill=(20, 15, 10, alpha))
                
            canvas.paste(shadow_overlay, (shadow_x, 0), shadow_overlay)
            
        return canvas
