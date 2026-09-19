import numpy as np
from PIL import Image, ImageFilter

def make_clean_pencil():
    src = Image.open('素材/05_分层动画切片/scene1_clean_background.png').convert("RGBA")
    # Pencil is in area (0, 1400, 360, 1920)
    pencil_box = (0, 1450, 360, 1920)
    pencil_crop = src.crop(pencil_box)
    
    # In this crop, the paper is warm white (r>235, g>230, b>220), the pencil is metallic silver/black (r<180 or dark)
    # and shadow has r < 210.
    arr = np.array(pencil_crop)
    r = arr[:, :, 0].astype(int)
    g = arr[:, :, 1].astype(int)
    b = arr[:, :, 2].astype(int)
    
    # Paper background is roughly r>232, g>228, b>218
    is_paper = (r > 230) & (g > 225) & (b > 215) & (np.abs(r - g) < 12) & (np.abs(r - b) < 20)
    
    # We create alpha: 0 for paper, 255 for pencil
    mask = (~is_paper).astype(np.uint8) * 255
    mask_im = Image.fromarray(mask, mode="L")
    mask_im = mask_im.filter(ImageFilter.GaussianBlur(1.0))
    
    pencil_crop.putalpha(mask_im)
    pencil_crop.save('素材/05_分层动画切片/crop_pencil_transparent.png')
    print("Saved crop_pencil_transparent.png")

if __name__ == "__main__":
    make_clean_pencil()
