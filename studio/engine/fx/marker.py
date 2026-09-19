import math
from PIL import Image, ImageDraw

class MarkerFX:
    """
    Renders a vibrant fluorescent highlighter stroke sweeping across key text.
    Simulates rough marker edges and semi-transparent ink overlay.
    """
    
    @staticmethod
    def apply(
        canvas: Image.Image,
        bbox: tuple[int, int, int, int], # (x1, y1, x2, y2)
        progress: float,
        color: tuple[int, int, int, int] = (255, 107, 0, 110) # Neon orange translucent
    ) -> Image.Image:
        if progress <= 0.0:
            return canvas
            
        p = min(1.0, progress)
        x1, y1, x2, y2 = bbox
        current_x2 = int(x1 + (x2 - x1) * p)
        
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw soft rounded highlighter stroke
        draw.rounded_rectangle([x1, y1, current_x2, y2], radius=(y2 - y1) // 3, fill=color)
        
        canvas.paste(overlay, (0, 0), overlay)
        return canvas
