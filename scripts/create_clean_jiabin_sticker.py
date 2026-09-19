import os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

def generate_clean_jiabin_thumbs_up():
    src_path = r"d:\video\视频3\素材\01_真人底图库\点赞.jpg"
    out_path = r"d:\video\视频3\素材\02_透明纸片人贴纸\贴纸_点赞_clean.png"
    
    src = Image.open(src_path).convert("RGBA")
    w, h = src.size
    arr = np.array(src)
    
    r = arr[:, :, 0].astype(int)
    g = arr[:, :, 1].astype(int)
    b = arr[:, :, 2].astype(int)
    
    # In 点赞.jpg:
    # Background is gray-white studio wall (high r, g, b, low color difference)
    # Jiabin's body has:
    # - Dark clothes/hair/shoes (r < 110, g < 110, b < 110)
    # - Skin (r - b > 35, r > 150)
    # Background pixels have r > 200, g > 200, b > 200 and abs(r-g)<15 and abs(r-b)<15 and abs(g-b)<15
    is_bg_seed = (r > 205) & (g > 205) & (b > 205) & (np.abs(r - g) < 18) & (np.abs(r - b) < 18) & (np.abs(g - b) < 18)
    
    # Create mask: 0 for background, 255 for foreground
    # We flood fill the background from the corners/edges
    bg_mask = Image.new("L", (w, h), 0)
    draw_bg = ImageDraw.Draw(bg_mask)
    
    # Seed binary image for floodfill
    seed_img = Image.fromarray((is_bg_seed * 255).astype(np.uint8))
    
    # Let's use BFS from image edges to find all connected background pixels
    import collections
    q = collections.deque()
    visited = np.zeros((h, w), dtype=bool)
    
    # Add top, left, right edges where is_bg_seed is true
    for x in range(w):
        if is_bg_seed[0, x]:
            q.append((0, x))
            visited[0, x] = True
        if is_bg_seed[h-1, x] and (x < 350 or x > 800): # ground around feet
            q.append((h-1, x))
            visited[h-1, x] = True
    for y in range(h):
        if is_bg_seed[y, 0]:
            q.append((y, 0))
            visited[y, 0] = True
        if is_bg_seed[y, w-1]:
            q.append((y, w-1))
            visited[y, w-1] = True
            
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w:
                if not visited[ny, nx] and is_bg_seed[ny, nx]:
                    visited[ny, nx] = True
                    q.append((ny, nx))
                    
    # The person mask is where background is NOT visited
    person_mask = (~visited).astype(np.uint8) * 255
    mask_im = Image.fromarray(person_mask, mode="L")
    
    # Fill small holes inside the person (e.g. skin highlights) by inverting, floodfilling outside, and inverting back
    inverted = Image.fromarray(visited.astype(np.uint8) * 255, mode="L")
    # Clean noise with MinFilter/MaxFilter
    # Erode then dilate (Closing)
    mask_im = mask_im.filter(ImageFilter.MaxFilter(5))
    mask_im = mask_im.filter(ImageFilter.MinFilter(5))
    mask_im = mask_im.filter(ImageFilter.GaussianBlur(1.0))
    
    # Apply mask to src
    cutout = src.copy()
    cutout.putalpha(mask_im)
    
    # Crop to bounding box
    bbox = cutout.getbbox()
    if bbox:
        # Pad bottom slightly for feet
        cutout = cutout.crop(bbox)
        mask_im = mask_im.crop(bbox)
        
    cw, ch = cutout.size
    border_width = 16
    shadow_blur = 16
    pad = border_width + shadow_blur * 2 + 15
    out_w, out_h = cw + pad * 2, ch + pad * 2
    
    # Expand mask for white border
    expanded_mask = mask_im.copy()
    for _ in range(border_width // 2):
        expanded_mask = expanded_mask.filter(ImageFilter.MaxFilter(5))
    expanded_mask = expanded_mask.filter(ImageFilter.GaussianBlur(1.0))
    
    # Create shadow
    shadow_layer = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    shadow_mask = expanded_mask.filter(ImageFilter.GaussianBlur(shadow_blur))
    shadow_color = Image.new("RGBA", (cw, ch), (15, 12, 10, 85))
    shadow_layer.paste(shadow_color, (pad + 6, pad + 14), mask=shadow_mask)
    
    # Create white die-cut border
    border_layer = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    white_fill = Image.new("RGBA", (cw, ch), (255, 255, 255, 255))
    border_layer.paste(white_fill, (pad, pad), mask=expanded_mask)
    
    # Paste person
    border_layer.paste(cutout, (pad, pad), mask=cutout)
    
    # Composite final sticker
    final_sticker = Image.alpha_composite(shadow_layer, border_layer)
    final_sticker.save(out_path, "PNG")
    print(f"Generated clean sticker: {out_path} ({out_w}x{out_h})")
    
    # Save a preview on gray background
    prev_bg = Image.new("RGBA", (out_w, out_h), (220, 220, 220, 255))
    prev_comp = Image.alpha_composite(prev_bg, final_sticker)
    prev_comp.thumbnail((500, 800))
    os.makedirs(r"d:\video\视频3\output\qa_frames\scene_05", exist_ok=True)
    prev_comp.save(r"d:\video\视频3\output\qa_frames\scene_05\qa_jiabin_sticker.png")
    print("Saved preview to output/qa_frames/scene_05/qa_jiabin_sticker.png")

if __name__ == "__main__":
    generate_clean_jiabin_thumbs_up()
