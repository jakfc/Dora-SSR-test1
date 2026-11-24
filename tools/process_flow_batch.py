import os
import glob
from collections import deque
from PIL import Image, ImageDraw
import numpy as np

DOWNLOADS = r"C:\Users\jakfc\Downloads"
ASSETS = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\assets"
B_DIR = os.path.join(ASSETS, "buildings")
BG_DIR = os.path.join(ASSETS, "bg")

def remove_white_bg_floodfill(im, threshold=232):
    arr = np.array(im.convert("RGBA"))
    h, w = arr.shape[:2]
    visited = np.zeros((h, w), dtype=bool)
    q = deque()
    for y in range(h):
        for x in (0, w - 1):
            if not visited[y, x] and np.all(arr[y, x, :3] >= threshold):
                visited[y, x] = True
                q.append((y, x))
    for x in range(w):
        for y in (0, h - 1):
            if not visited[y, x] and np.all(arr[y, x, :3] >= threshold):
                visited[y, x] = True
                q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                if np.all(arr[ny, nx, :3] >= threshold):
                    visited[ny, nx] = True
                    q.append((ny, nx))
    arr[visited, 3] = 0
    return Image.fromarray(arr)

def fit_bc(img, size, pad_x=4, pad_top=4):
    tw, th = size
    scale = min((tw - pad_x * 2) / img.width, (th - pad_top) / img.height)
    nw = max(1, int(round(img.width * scale)))
    nh = max(1, int(round(img.height * scale)))
    res = img.resize((nw, nh), Image.Resampling.LANCZOS)
    c = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    c.paste(res, ((tw - nw) // 2, th - nh), res)
    return c

def process_b07():
    src = os.path.join(DOWNLOADS, "Fortress_watchtower_game_sprite_2faec418.jpg")
    if not os.path.exists(src):
        print("B07 source not found:", src)
        return
    im_clean = remove_white_bg_floodfill(Image.open(src))
    cropped = im_clean.crop(im_clean.getbbox())
    out_1x = fit_bc(cropped, (112, 210), pad_x=2, pad_top=2)
    out_2x = fit_bc(cropped, (224, 420), pad_x=4, pad_top=4)
    out_1x.save(os.path.join(B_DIR, "b07_tower_arrow.png"), "PNG")
    out_2x.save(os.path.join(B_DIR, "b07_tower_arrow@2x.png"), "PNG")

    lv2 = Image.new("RGBA", (288, 480), (0, 0, 0, 0))
    b2 = fit_bc(cropped, (240, 420), pad_x=4, pad_top=4)
    lv2.paste(b2, (24, 60), b2)
    dl = ImageDraw.Draw(lv2)
    dl.line([(144, 14), (144, 92)], fill=(140, 109, 70, 255), width=4)
    dl.polygon([(144, 18), (206, 28), (194, 48), (144, 52)], fill=(155, 44, 44, 255), outline=(26, 32, 44, 255), width=3)
    lv2.resize((144, 240), Image.Resampling.LANCZOS).save(os.path.join(B_DIR, "b07_tower_arrow_lv2.png"), "PNG")
    print("Processed b07_tower_arrow.png, @2x, and lv2!")

def process_ground(src_pattern, dst_name):
    matches = glob.glob(os.path.join(DOWNLOADS, src_pattern))
    if not matches:
        print("Ground source not found:", src_pattern)
        return
    src = sorted(matches, key=os.path.getmtime, reverse=True)[0]
    im_g = Image.open(src).convert("RGBA")
    g_arr = np.array(im_g)
    row_means = np.mean(g_arr[:, :, :3], axis=(1, 2))
    content_rows = np.where(row_means < 235)[0]
    top_y = int(content_rows[0]) if len(content_rows) > 0 else 0
    im_g_crop = im_g.crop((0, top_y, im_g.width, im_g.height))
    im_g_crop.resize((640, 160), Image.Resampling.LANCZOS).save(os.path.join(BG_DIR, dst_name), "PNG")
    print(f"Processed {dst_name} (cropped top {top_y}px -> 640x160)")

def process_bg_16_9(src_pattern, dst_name):
    matches = glob.glob(os.path.join(DOWNLOADS, src_pattern))
    if not matches:
        print("BG source not found:", src_pattern)
        return
    src = sorted(matches, key=os.path.getmtime, reverse=True)[0]
    im_t = Image.open(src).convert("RGBA").resize((1280, 720), Image.Resampling.LANCZOS)
    im_t.save(os.path.join(BG_DIR, dst_name), "PNG")
    print(f"Processed {dst_name} (1280x720)")

if __name__ == "__main__":
    process_b07()
    process_ground("Ming_dynasty_fortress_ground_tile*.jpg", "d04_ground_fortress.png")
    process_bg_16_9("Yongchang_Fortress_night_landsca*.jpg", "d09_title_bg.png")
