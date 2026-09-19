from PIL import Image

class KenBurnsZoom:
    """
    Applies an imperceptible, organic slow zoom (1.000x -> 1.035x)
    to give static journal pages breathing life without motion sickness.
    """
    
    @staticmethod
    def apply(frame: Image.Image, progress: float, max_scale: float = 1.030) -> Image.Image:
        if progress <= 0.0:
            return frame
            
        w, h = frame.size
        # Linear or smooth ease
        scale = 1.0 + (max_scale - 1.0) * progress
        
        crop_w = int(w / scale)
        crop_h = int(h / scale)
        
        left = (w - crop_w) // 2
        top = (h - crop_h) // 2
        right = left + crop_w
        bottom = top + crop_h
        
        cropped = frame.crop((left, top, right, bottom))
        return cropped.resize((w, h), Image.Resampling.BILINEAR)
