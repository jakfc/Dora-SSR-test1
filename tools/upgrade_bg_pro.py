import os
import subprocess
from collections import deque
from PIL import Image
import numpy as np

RAW_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\raw_assets\gflow_bg_pro"
BG_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\assets\bg"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(BG_DIR, exist_ok=True)

JOBS = [
    (
        "d01_sky_day.jpg", "16:9",
        "Exquisite 2D Chinese guofeng hand-painted game sky background, clear Ming dynasty coastal daytime sky: smooth luminous vertical gradient from steel-azure (#4A6FA5) at top to warm misty ivory-blue (#E2E8F0) near bottom, adorned with finely detailed flat-shaded traditional Chinese auspicious drifting clouds with crisp clean linework. Ultra-refined painterly illustration, no mountains, no buildings, NO text."
    ),
    (
        "d02_sky_dusk.jpg", "16:9",
        "Exquisite 2D Chinese guofeng hand-painted game sky background, dramatic Ming dynasty coastal sunset dusk sky: smooth gradient from deep twilight plum-brown (#7A5C3E) at top to glowing burnt-amber and pale gold (#F6AD55) below, adorned with finely detailed traditional Chinese layered evening clouds rim-lit in warm gold. Ultra-refined illustration, no mountains, no buildings, NO text."
    ),
    (
        "d03_sky_night.jpg", "16:9",
        "Exquisite 2D Chinese guofeng hand-painted game sky background, solemn Ming dynasty coastal midnight sky: smooth deep indigo-navy (#101829) to dark midnight blue (#0B1426), adorned with delicate fine twinkling stars and refined flat-shaded dark slate-blue (#2C3E50) traditional Chinese night clouds. NO horizon ground, NO moon, NO mountains, NO buildings, NO text."
    ),
    (
        "b09_daluo_mountain.jpg", "9:16",
        "Exquisite 2D Chinese guofeng game background asset of Daluo Mountain in Wenzhou: tall majestic layered mountain peaks on the left sloping gracefully down toward the right, painted in refined flat-shaded slate-blue and pine-teal (#2C3E50, #2F4F4F) with crisp ink-drawn mountain ridges and cliff facets. Sharp clean edges, NO soft blurry fog against the white background, no foreground trees, NO text, isolated on a pure solid white background."
    ),
    (
        "b10_outer_salt_flat.jpg", "16:9",
        "A very wide, low-profile 2D side-scrolling game ground strip occupying only the bottom 25% of the frame, seamlessly horizontally tileable Ming dynasty coastal salt evaporation pans outside Yongchang Fortress: neat low earth bunds (#B79F78), shallow reflective water pans, and small conical piles of gleaming white sea salt (#E2E8F0) in strict orthographic side view. Ultra-refined flat Chinese guofeng game art, clean 1.5px dark outline (#1A202C), top 75% of image is completely pure solid white background, NO text, NO sky."
    ),
    (
        "b11_coast.jpg", "16:9",
        "A wide, low-profile 2D side-scrolling game coastal terrain strip occupying only the bottom 35% of the frame: warm sandy tidal mudflat (#B79F78) and sharp dark coastal rocks (#4A5568) on the left transitioning into crisp stylized Chinese guofeng deep blue-teal East China Sea waves (#1E4E79) with white curling sea foam on the right. Strict orthographic side view, clean 1.5px dark outline (#1A202C), top 65% is completely pure solid white background, NO text, NO sky."
    ),
    (
        "d08_mid_houses.jpg", "16:9",
        "A wide, low-profile 2D parallax midground skyline strip occupying only the bottom 25% of the frame, seamlessly horizontally tileable Ming dynasty southern Zhejiang (Wenzhou) riverfront village houses, stepped horsehead-gable walls (matouqiang), tiled roofs, and a small stone arch bridge in refined flat muted slate-blue (#3B4A59, #2D3748) with crisp architectural silhouettes and subtle roof-tile linework. Strict orthographic side elevation along a flat bottom edge, top 75% is pure solid white background, NO text."
    ),
    (
        "d06_horizon_silhouette.jpg", "16:9",
        "A wide, low-profile 2D parallax distant horizon skyline strip occupying only the bottom 25% of the frame, seamlessly horizontally tileable Ming dynasty stone fortress wall with neat crenellated battlements and spaced traditional watchtower roofs in flat muted slate-blue silhouette (#3B4A59) along a flat bottom edge. Strict orthographic side elevation, top 75% is pure solid white background, NO text."
    ),
]

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

def fit_strip_no_squish(im_rgba, target_w, target_h):
    """Scale proportionally to target_w (never squishing vertically!), then bottom-align into (target_w, target_h)."""
    bbox = im_rgba.getbbox()
    if bbox:
        im_rgba = im_rgba.crop((0, bbox[1], im_rgba.width, bbox[3]))
    # Scale proportionally so height <= target_h or width == target_w
    scale_w = target_w / im_rgba.width
    nh = int(round(im_rgba.height * scale_w))
    if nh <= target_h:
        res = im_rgba.resize((target_w, nh), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        canvas.paste(res, (0, target_h - nh), res)
        return canvas
    else:
        # Preserve aspect ratio by fitting height = target_h and tiling/centering, OR cropping top slightly if close
        res = im_rgba.resize((target_w, nh), Image.Resampling.LANCZOS)
        # If nh is within 1.5x of target_h, crop from bottom-up? Better: scale to fit height if strip is taller, then horizontally tile!
        scale_h = target_h / im_rgba.height
        nw = max(1, int(round(im_rgba.width * scale_h)))
        res_h = im_rgba.resize((nw, target_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        if nw >= target_w:
            canvas.paste(res_h.crop((0, 0, target_w, target_h)), (0, 0), res_h.crop((0, 0, target_w, target_h)))
        else:
            # Tile horizontally with mirrored alternating seam so there is ZERO squishing!
            x = 0
            flip = False
            while x < target_w:
                tile = res_h.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else res_h
                canvas.paste(tile, (x, 0), tile)
                x += nw
                flip = not flip
        return canvas

def postprocess_all():
    for fname in ["d01_sky_day.jpg", "d02_sky_dusk.jpg", "d03_sky_night.jpg"]:
        p = os.path.join(RAW_DIR, fname)
        if os.path.exists(p):
            out = os.path.join(BG_DIR, fname.replace(".jpg", ".png"))
            Image.open(p).convert("RGBA").resize((1280, 720), Image.Resampling.LANCZOS).save(out, "PNG")
            print(f"Saved {out} (1280x720)")

    # Daluo Mountain (320x760, proportional fit bottom-aligned, no horizontal squishing)
    p_mtn = os.path.join(RAW_DIR, "b09_daluo_mountain.jpg")
    if os.path.exists(p_mtn):
        im = remove_white_bg_floodfill(Image.open(p_mtn), threshold=232)
        bbox = im.getbbox()
        if bbox:
            im = im.crop(bbox)
        # Fit proportionally into 320x760 (or crop width cleanly from left peak)
        sc = 760 / im.height
        nw = int(round(im.width * sc))
        res = im.resize((nw, 760), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (320, 760), (0, 0, 0, 0))
        if nw >= 320:
            canvas.paste(res.crop((0, 0, 320, 760)), (0, 0))
        else:
            canvas.paste(res, (0, 0))
        canvas.save(os.path.join(BG_DIR, "b09_daluo_mountain.png"), "PNG")
        print("Saved b09_daluo_mountain.png (320x760)")

    strips = [
        ("b10_outer_salt_flat.jpg", "b10_outer_salt_flat.png", 1120, 120),
        ("b11_coast.jpg", "b11_coast.png", 520, 160),
        ("d08_mid_houses.jpg", "d08_mid_houses.png", 1280, 160),
        ("d06_horizon_silhouette.jpg", "d06_horizon_silhouette.png", 1280, 160),
    ]
    for src_n, dst_n, tw, th in strips:
        p = os.path.join(RAW_DIR, src_n)
        if os.path.exists(p):
            im = remove_white_bg_floodfill(Image.open(p), threshold=232)
            out_im = fit_strip_no_squish(im, tw, th)
            out_im.save(os.path.join(BG_DIR, dst_n), "PNG")
            print(f"Saved {dst_n} ({tw}x{th})")

def main():
    for fname, aspect, prompt in JOBS:
        out_path = os.path.join(RAW_DIR, fname)
        if not os.path.exists(out_path):
            print(f"Generating {fname} with nano-pro...", flush=True)
            cmd = [
                "gflow", "image", "t2i", prompt,
                "--model", "nano-pro",
                "--aspect", aspect,
                "--out-file", out_path,
            ]
            res = subprocess.run(cmd, capture_output=False)
            if res.returncode != 0:
                print(f"WARN: nano-pro failed for {fname}, falling back to nano2.1...", flush=True)
                cmd[cmd.index("nano-pro")] = "nano2.1"
                subprocess.run(cmd, capture_output=False)
    postprocess_all()
    print("ALL PRO BACKGROUNDS UPGRADED!", flush=True)

if __name__ == "__main__":
    main()
