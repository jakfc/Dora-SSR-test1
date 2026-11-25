import os
import subprocess
from collections import deque
from PIL import Image
import numpy as np

RAW_BG_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\raw_assets\gflow_bg"
BG_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\assets\bg"
os.makedirs(RAW_BG_DIR, exist_ok=True)
os.makedirs(BG_DIR, exist_ok=True)

JOBS = [
    (
        "b09_daluo_mountain.jpg", "9:16",
        "A 2D game background layer of distant southern Zhejiang coastal mountains (Daluo Mountain in Wenzhou), towering misty peaks on the left sloping gently down toward the right, painted in flat Chinese guofeng ink-wash silhouette style (#2C3E50, #2F4F4F) with subtle layered mountain ridges. No foreground trees, NO text, NO sky gradient, isolated cleanly on a pure solid white background."
    ),
    (
        "b10_outer_salt_flat.jpg", "16:9",
        "A 2D side-scrolling game ground strip, seamlessly horizontally tileable Ming dynasty coastal salt evaporation pans and mudflats outside Yongchang Fortress: neat shallow square water-filled salt beds bordered by low earth bunds (#B79F78) and small conical piles of gleaming white sea salt (#E2E8F0) along the middle horizon. Strict orthographic side view, flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), NO text, NO sky, isolated on a pure solid white background."
    ),
    (
        "b11_coast.jpg", "16:9",
        "A 2D side-scrolling game coastal terrain strip: sandy tidal beach (#B79F78) and rugged dark coastal rocks (#4A5568) on the left sloping into churning deep blue-teal East China Sea waves (#1E4E79) with stylized white guofeng sea foam on the right. Strict orthographic side view, flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), NO text, NO sky, isolated on a pure solid white background."
    ),
    (
        "d01_sky_day.jpg", "16:9",
        "A 2D game sky backdrop of a clear Ming dynasty coastal daytime sky: smooth vertical gradient from muted steel-blue (#4A6FA5) at the top to pale misty cream-blue (#E2E8F0) at the bottom, decorated with elegant flat hand-painted Chinese guofeng layered clouds. No mountains, no buildings, NO text, seamless horizontal composition."
    ),
    (
        "d02_sky_dusk.jpg", "16:9",
        "A 2D game sky backdrop of a dramatic Ming dynasty coastal dusk sunset sky: smooth vertical gradient from muted twilight brown-violet (#7A5C3E) at the top to warm burnt orange and pale amber (#F6AD55) at the bottom, with stylized flat hand-painted Chinese guofeng evening clouds lit from below. No mountains, no buildings, NO text, seamless horizontal composition."
    ),
    (
        "d03_sky_night.jpg", "16:9",
        "A 2D game sky backdrop of a solemn Ming dynasty coastal night sky: deep indigo-navy (#101829) fading to dark midnight blue (#0B1426), with delicate fine stars and faint ink-blue drifting night clouds. No moon, no mountains, no buildings, NO text, seamless horizontal composition."
    ),
    (
        "d08_mid_houses.jpg", "16:9",
        "A 2D parallax midground layer of historic Ming dynasty southern Zhejiang (Wenzhou) riverfront village houses and stepped horsehead-gable walls (matouqiang) with a small stone arch bridge, rendered in flat muted ink-slate silhouette (#3B4A59, #2D3748) with subtle tile roof details. Strict orthographic side elevation aligned along a flat bottom baseline, seamlessly horizontally tileable, NO text, NO sky, isolated on a pure solid white background."
    ),
    (
        "d06_horizon_silhouette.jpg", "16:9",
        "A 2D parallax distant horizon silhouette layer of a long Ming dynasty stone fortress wall with crenellated battlements and spaced watchtower roofs, rendered in flat muted slate-blue silhouette (#3B4A59) aligned along a flat bottom baseline. Strict orthographic side view, seamlessly horizontally tileable, NO text, NO sky, isolated on a pure solid white background."
    ),
]

def remove_white_bg_floodfill(im, threshold=230):
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

def postprocess_all():
    # 1. Skies (1280x720)
    for fname in ["d01_sky_day.jpg", "d02_sky_dusk.jpg", "d03_sky_night.jpg"]:
        p = os.path.join(RAW_BG_DIR, fname)
        if os.path.exists(p):
            out = os.path.join(BG_DIR, fname.replace(".jpg", ".png"))
            Image.open(p).convert("RGBA").resize((1280, 720), Image.Resampling.LANCZOS).save(out, "PNG")
            print(f"Saved {out} (1280x720)")

    # 2. Daluo Mountain (320x760, transparent bg, bottom-aligned)
    p_mtn = os.path.join(RAW_BG_DIR, "b09_daluo_mountain.jpg")
    if os.path.exists(p_mtn):
        im = remove_white_bg_floodfill(Image.open(p_mtn), threshold=230)
        bbox = im.getbbox()
        if bbox:
            im = im.crop(bbox)
        im = im.resize((320, 760), Image.Resampling.LANCZOS)
        im.save(os.path.join(BG_DIR, "b09_daluo_mountain.png"), "PNG")
        print("Saved b09_daluo_mountain.png (320x760)")

    # 3. Horizontal transparent strips (salt flat, coast, mid_houses, horizon)
    strips = [
        ("b10_outer_salt_flat.jpg", "b10_outer_salt_flat.png", (1120, 120)),
        ("b11_coast.jpg", "b11_coast.png", (520, 160)),
        ("d08_mid_houses.jpg", "d08_mid_houses.png", (1280, 160)),
        ("d06_horizon_silhouette.jpg", "d06_horizon_silhouette.png", (1280, 160)),
    ]
    for src_n, dst_n, sz in strips:
        p = os.path.join(RAW_BG_DIR, src_n)
        if os.path.exists(p):
            im = remove_white_bg_floodfill(Image.open(p), threshold=230)
            bbox = im.getbbox()
            if bbox:
                # Crop vertically to content, keep full width
                im = im.crop((bbox[0], bbox[1], bbox[2], bbox[3]))
            im = im.resize(sz, Image.Resampling.LANCZOS)
            im.save(os.path.join(BG_DIR, dst_n), "PNG")
            print(f"Saved {dst_n} ({sz[0]}x{sz[1]})")

def main():
    for fname, aspect, prompt in JOBS:
        out_path = os.path.join(RAW_BG_DIR, fname)
        if not os.path.exists(out_path):
            print(f"Generating {fname}...", flush=True)
            cmd = [
                "gflow", "image", "t2i", prompt,
                "--model", "nano2.1",
                "--aspect", aspect,
                "--out-file", out_path,
            ]
            subprocess.run(cmd, capture_output=False)
    postprocess_all()
    print("ALL AI BACKGROUNDS GENERATED & PROCESSED!", flush=True)

if __name__ == "__main__":
    main()
