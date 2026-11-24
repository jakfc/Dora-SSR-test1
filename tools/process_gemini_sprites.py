import os
from collections import deque
from PIL import Image, ImageOps
import numpy as np

GEMINI_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\assets\gemini"
ASSETS_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\assets"

def remove_white_bg_floodfill(img, threshold=232):
    """Floodfill from image borders to remove outer white background without hollowing inner highlights."""
    arr = np.array(img.convert("RGBA"))
    h, w = arr.shape[:2]
    visited = np.zeros((h, w), dtype=bool)
    queue = deque()

    # Seed from all 4 borders
    for y in range(h):
        for x in (0, w - 1):
            if not visited[y, x] and np.all(arr[y, x, :3] >= threshold):
                visited[y, x] = True
                queue.append((y, x))
    for x in range(w):
        for y in (0, h - 1):
            if not visited[y, x] and np.all(arr[y, x, :3] >= threshold):
                visited[y, x] = True
                queue.append((y, x))

    while queue:
        cy, cx = queue.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                if np.all(arr[ny, nx, :3] >= threshold):
                    visited[ny, nx] = True
                    queue.append((ny, nx))

    arr[visited, 3] = 0
    return Image.fromarray(arr)

def keep_largest_component(img):
    """Keep only the largest connected opaque component (removes detached ground props like floating buckets)."""
    arr = np.array(img)
    alpha = arr[:, :, 3] > 0
    h, w = alpha.shape
    comp_id = np.zeros((h, w), dtype=np.int32)
    current_id = 0
    best_id = 0
    best_size = 0

    for y in range(h):
        for x in range(w):
            if alpha[y, x] and comp_id[y, x] == 0:
                current_id += 1
                size = 0
                q = deque([(y, x)])
                comp_id[y, x] = current_id
                while q:
                    cy, cx = q.popleft()
                    size += 1
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and alpha[ny, nx] and comp_id[ny, nx] == 0:
                            comp_id[ny, nx] = current_id
                            q.append((ny, nx))
                if size > best_size:
                    best_size = size
                    best_id = current_id

    if best_id > 0:
        arr[comp_id != best_id, 3] = 0
    return Image.fromarray(arr)

def fit_and_align(img, target_size, padding_bottom=6, padding_side=6, padding_top=6):
    """Crop to content bounding box, scale proportionally, and align bottom-center."""
    bbox = img.getbbox()
    if not bbox:
        raise ValueError("Empty image after background removal")
    cropped = img.crop(bbox)

    tw, th = target_size
    avail_w = tw - padding_side * 2
    avail_h = th - padding_bottom - padding_top

    scale = min(avail_w / cropped.width, avail_h / cropped.height)
    new_w = max(1, int(round(cropped.width * scale)))
    new_h = max(1, int(round(cropped.height * scale)))

    resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    pos_x = (tw - new_w) // 2
    pos_y = th - padding_bottom - new_h
    canvas.paste(resized, (pos_x, pos_y), resized)
    return canvas

JOBS = [
    ("Gemini_Generated_Image_idnr1tidnr1tidnr.jpg", "sprites/villagers/villager_idle_01.png", (128, 192), False, False),
    ("Gemini_Generated_Image_i0w9qai0w9qai0w9.jpg", "sprites/villagers/villager_farmer_01.png", (128, 192), False, False),
    ("Gemini_Generated_Image_z82ikcz82ikcz82i.jpg", "sprites/villagers/villager_salt_worker_01.png", (128, 192), False, True),
    ("Gemini_Generated_Image_xxio9zxxio9zxxio.jpg", "sprites/villagers/villager_builder_01.png", (128, 192), False, False),
    ("Gemini_Generated_Image_4vsiij4vsiij4vsi.jpg", "sprites/villagers/villager_militia_01.png", (128, 192), False, False),
    ("Gemini_Generated_Image_anc3smanc3smanc3.jpg", "sprites/villagers/villager_kung_fu_01.png", (128, 192), False, False),
    ("Gemini_Generated_Image_wnei1qwnei1qwnei.jpg", "sprites/enemies/enemy_samurai_01.png", (128, 192), False, False),
    ("Gemini_Generated_Image_k42vr0k42vr0k42v.jpg", "sprites/enemies/enemy_scout_01.png", (128, 192), True, False),
    ("Gemini_Generated_Image_r0cjzer0cjzer0cj.jpg", "sprites/enemies/enemy_boss_01.png", (192, 256), True, False),
]

def main():
    for src_name, dst_rel, size, flip_h, largest_only in JOBS:
        src_path = os.path.join(GEMINI_DIR, src_name)
        dst_path = os.path.join(ASSETS_DIR, dst_rel)
        dst_2x_path = dst_path.replace(".png", "@2x.png")

        img = Image.open(src_path)
        img = remove_white_bg_floodfill(img)
        if largest_only:
            img = keep_largest_component(img)
        if flip_h:
            img = ImageOps.mirror(img)

        out_1x = fit_and_align(img, size, padding_bottom=6, padding_side=6, padding_top=6)
        out_2x = fit_and_align(img, (size[0] * 2, size[1] * 2), padding_bottom=12, padding_side=12, padding_top=12)

        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        out_1x.save(dst_path, "PNG")
        out_2x.save(dst_2x_path, "PNG")
        print(f"Processed {src_name} -> {dst_rel} ({size[0]}x{size[1]}) & @2x")

if __name__ == "__main__":
    main()
