import os
import subprocess
from collections import deque
from PIL import Image
import numpy as np

RAW_MOD_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\raw_assets\gflow_bg_modular"
BG_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\assets\bg"
os.makedirs(RAW_MOD_DIR, exist_ok=True)
os.makedirs(BG_DIR, exist_ok=True)

MODULES = [
    # 4 distinct Wenzhou Ming village modules for d08_mid_houses
    ("tile_house_matou.jpg", "1:1",
     "Single isolated Ming dynasty Wenzhou stepped horsehead-gable mansion (matouqiang) with blue-gray tiled roof and clean architectural silhouette in muted slate-blue (#3B4A59, #2D3748) with crisp 1.5px dark outline (#1A202C). Strict 90-degree orthographic side view, flat bottom edge, NO sky, NO ground below base, NO text, isolated on pure solid white background."),
    ("tile_house_cottage.jpg", "1:1",
     "Single isolated Ming dynasty southern Zhejiang riverfront timber-and-brick house with upturned eaves and dark tiled roof in muted slate-blue (#3B4A59, #2D3748) with crisp 1.5px dark outline (#1A202C). Strict 90-degree orthographic side view, flat bottom edge, NO sky, NO text, isolated on pure solid white background."),
    ("tile_bridge_canal.jpg", "1:1",
     "Single isolated Ming dynasty traditional Chinese curved stone arch bridge with carved stone railings in muted slate-blue (#3B4A59, #2D3748) with crisp 1.5px dark outline (#1A202C). Strict 90-degree orthographic side view, flat bottom edge, NO water splash, NO sky, NO text, isolated on pure solid white background."),
    ("tile_pavilion_tree.jpg", "1:1",
     "Single isolated Ming dynasty courtyard archway gatehouse beside a windswept coastal pine tree in muted slate-blue silhouette (#3B4A59, #2D3748) with crisp 1.5px dark outline (#1A202C). Strict 90-degree orthographic side view, flat bottom edge, NO sky, NO text, isolated on pure solid white background."),

    # 2 distant wall modules for d06_horizon_silhouette
    ("tile_wall_segment.jpg", "1:1",
     "Single isolated flat-view Ming dynasty stone fortress curtain wall segment with neat crenellated battlements on top, in flat muted slate-blue silhouette (#3B4A59) with crisp 1.5px dark outline (#1A202C). Strict 90-degree orthographic side view, flat bottom edge, reaching left-to-right cleanly, NO sky, NO text, isolated on pure solid white background."),
    ("tile_wall_tower.jpg", "1:1",
     "Single isolated Ming dynasty coastal fortress watchtower with upturned eaves atop a stone wall bastion, in flat muted slate-blue silhouette (#3B4A59, #2D3748) with crisp 1.5px dark outline (#1A202C). Strict 90-degree orthographic side view, flat bottom edge, NO sky, NO text, isolated on pure solid white background."),

    # 3 modular salt-flat pieces for b10_outer_salt_flat
    ("tile_salt_pan.jpg", "1:1",
     "Single isolated 2D side-view Ming dynasty coastal salt evaporation pan: low rammed-earth bund (#B79F78) enclosing shallow pale-blue brine water with a neat conical mound of gleaming white sea salt (#E2E8F0) in the center. Flat semi-shaded Chinese guofeng style, crisp 1.5px dark outline (#1A202C), NO sky, NO text, isolated on pure solid white background."),
    ("tile_salt_shed.jpg", "1:1",
     "Single isolated 2D side-view Ming dynasty open-sided timber salt-drying shed with thatched/tiled roof and two woven bamboo baskets piled with white sea salt (#E2E8F0). Flat semi-shaded Chinese guofeng style, crisp 1.5px dark outline (#1A202C), warm earth palette, NO sky, NO text, isolated on pure solid white background."),
    ("tile_mudflat_cart.jpg", "1:1",
     "Single isolated 2D side-view Ming dynasty wooden salt wheelbarrow cart beside a small clump of green coastal reeds (#68A357) on warm sandy mud (#B79F78). Flat semi-shaded Chinese guofeng style, crisp 1.5px dark outline (#1A202C), NO sky, NO text, isolated on pure solid white background."),
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
    bbox = Image.fromarray(arr).getbbox()
    return Image.fromarray(arr).crop(bbox) if bbox else Image.fromarray(arr)

def paste_wrap_x(canvas, tile, x, y):
    """Paste tile onto canvas with horizontal wrap-around so left/right edges tile seamlessly."""
    cw = canvas.width
    tw = tile.width
    x = x % cw
    canvas.alpha_composite(tile, (x, y))
    if x + tw > cw:
        canvas.alpha_composite(tile, (x - cw, y))

def scale_to_height(im, target_h):
    sc = target_h / im.height
    nw = max(1, int(round(im.width * sc)))
    return im.resize((nw, target_h), Image.Resampling.LANCZOS)

def compose_modular_backgrounds():
    # 1. d08_mid_houses.png (1280x160): rich non-repetitive Ming Wenzhou village skyline
    h_matou = remove_white_bg_floodfill(Image.open(os.path.join(RAW_MOD_DIR, "tile_house_matou.jpg")))
    h_cott = remove_white_bg_floodfill(Image.open(os.path.join(RAW_MOD_DIR, "tile_house_cottage.jpg")))
    h_brdg = remove_white_bg_floodfill(Image.open(os.path.join(RAW_MOD_DIR, "tile_bridge_canal.jpg")))
    h_pav = remove_white_bg_floodfill(Image.open(os.path.join(RAW_MOD_DIR, "tile_pavilion_tree.jpg")))

    c_houses = Image.new("RGBA", (1280, 160), (0, 0, 0, 0))
    placements = [
        (h_matou, 148, 20, False),
        (h_cott, 118, 175, False),
        (h_brdg, 86, 305, False),
        (h_pav, 134, 410, False),
        (h_cott, 126, 540, True),
        (h_matou, 152, 675, True),
        (h_pav, 122, 835, True),
        (h_brdg, 88, 965, True),
        (h_cott, 132, 1085, False),
    ]
    for src_im, th, px, fl in placements:
        t = scale_to_height(src_im, th)
        if fl:
            t = t.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        paste_wrap_x(c_houses, t, px, 160 - th)
    c_houses.save(os.path.join(BG_DIR, "d08_mid_houses.png"), "PNG")
    print("Composed modular d08_mid_houses.png (1280x160)")

    # 2. d06_horizon_silhouette.png (1280x160): continuous fortress wall + spaced watchtowers
    w_seg = remove_white_bg_floodfill(Image.open(os.path.join(RAW_MOD_DIR, "tile_wall_segment.jpg")))
    w_twr = remove_white_bg_floodfill(Image.open(os.path.join(RAW_MOD_DIR, "tile_wall_tower.jpg")))

    c_horiz = Image.new("RGBA", (1280, 160), (0, 0, 0, 0))
    seg_scaled = scale_to_height(w_seg, 72)
    x = 0
    while x < 1280:
        paste_wrap_x(c_horiz, seg_scaled, x, 160 - seg_scaled.height)
        x += seg_scaled.width - 8
    for tx, th, fl in [(160, 140, False), (580, 148, True), (1020, 136, False)]:
        twr = scale_to_height(w_twr, th)
        if fl:
            twr = twr.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        paste_wrap_x(c_horiz, twr, tx, 160 - th)
    c_horiz.save(os.path.join(BG_DIR, "d06_horizon_silhouette.png"), "PNG")
    print("Composed modular d06_horizon_silhouette.png (1280x160)")

    # 3. b10_outer_salt_flat.png (1120x120): seamless mudflat base + modular salt pans, sheds, carts
    s_pan = remove_white_bg_floodfill(Image.open(os.path.join(RAW_MOD_DIR, "tile_salt_pan.jpg")))
    s_shed = remove_white_bg_floodfill(Image.open(os.path.join(RAW_MOD_DIR, "tile_salt_shed.jpg")))
    s_cart = remove_white_bg_floodfill(Image.open(os.path.join(RAW_MOD_DIR, "tile_mudflat_cart.jpg")))

    c_salt = Image.new("RGBA", (1120, 120), (0, 0, 0, 0))
    # Continuous mudflat strip at bottom 52px
    from PIL import ImageDraw
    ds = ImageDraw.Draw(c_salt)
    ds.rectangle([0, 68, 1120, 120], fill=(183, 159, 120, 255))
    ds.line([(0, 68), (1120, 68)], fill=(26, 32, 44, 255), width=2)

    salt_layout = [
        (s_pan, 68, 20, False),
        (s_cart, 72, 180, False),
        (s_pan, 68, 290, True),
        (s_shed, 108, 445, False),
        (s_pan, 68, 600, False),
        (s_cart, 74, 760, True),
        (s_pan, 68, 875, True),
        (s_shed, 104, 1010, True),
    ]
    for src_im, th, px, fl in salt_layout:
        t = scale_to_height(src_im, th)
        if fl:
            t = t.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        paste_wrap_x(c_salt, t, px, 120 - th)
    c_salt.save(os.path.join(BG_DIR, "b10_outer_salt_flat.png"), "PNG")
    print("Composed modular b10_outer_salt_flat.png (1120x120)")

def main():
    for fname, aspect, prompt in MODULES:
        out_path = os.path.join(RAW_MOD_DIR, fname)
        if not os.path.exists(out_path):
            print(f"Generating module {fname}...", flush=True)
            cmd = [
                "gflow", "image", "t2i", prompt,
                "--model", "nano-pro",
                "--aspect", aspect,
                "--out-file", out_path,
            ]
            res = subprocess.run(cmd, capture_output=False)
            if res.returncode != 0:
                cmd[cmd.index("nano-pro")] = "nano2.1"
                subprocess.run(cmd, capture_output=False)
    compose_modular_backgrounds()
    print("MODULAR BACKGROUNDS COMPOSED SUCCESSFULLY!", flush=True)

if __name__ == "__main__":
    main()
