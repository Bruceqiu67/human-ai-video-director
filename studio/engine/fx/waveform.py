import math
from PIL import Image, ImageDraw

class WaveformFX:
    """
    Renders a bouncing multi-bar audio waveform equalizer for phone call / speech simulation.
    """
    
    @staticmethod
    def apply(
        canvas: Image.Image,
        bbox: tuple[int, int, int, int], # (x, y, w, h)
        t: float,
        is_active: bool = True,
        num_bars: int = 16,
        color: tuple[int, int, int, int] = (16, 185, 129, 220) # Tech emerald green
    ) -> Image.Image:
        x, y, w, h = bbox
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        bar_w = max(2, int((w / num_bars) * 0.65))
        gap = max(1, int((w - bar_w * num_bars) / (num_bars - 1))) if num_bars > 1 else 0
        
        for i in range(num_bars):
            bx = x + i * (bar_w + gap)
            if is_active:
                # Dynamic sinusoidal height simulation with varying frequencies
                phase = i * 0.75 + t * 9.0
                bar_factor = 0.25 + 0.70 * abs(math.sin(phase) * math.cos(phase * 0.5))
            else:
                bar_factor = 0.10
                
            bar_h = max(4, int(h * bar_factor))
            by1 = y + (h - bar_h) // 2
            by2 = by1 + bar_h
            
            draw.rounded_rectangle([bx, by1, bx + bar_w, by2], radius=bar_w // 2, fill=color)
            
        canvas.paste(overlay, (0, 0), overlay)
        return canvas
