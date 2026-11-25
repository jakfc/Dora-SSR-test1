import os
import subprocess
import sys
from collections import deque

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

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

def despill_white_edge(im, white=215):
    """把「紧贴透明区、颜色又接近纯白」的一圈像素也挖掉。

    AI 生的白底在 JPEG 里是渐变的，单纯靠阈值抠图会在轮廓上留一圈半白像素，
    贴到深色天空上就是一道发亮的白边。这里只处理边界那一圈，不动内部（盐堆等）。
    """
    arr = np.array(im.convert('RGBA'))
    opaque = arr[:, :, 3] > 0
    trans = ~opaque
    neigh = np.zeros_like(opaque)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        neigh |= np.roll(np.roll(trans, dy, axis=0), dx, axis=1)
    near_white = (arr[:, :, :3] >= white).all(axis=2)
    arr[opaque & neigh & near_white, 3] = 0
    return Image.fromarray(arr)


def bleed_edges(im):
    """把透明区的 RGB 用最近的不透明像素颜色填满（alpha 不变）。

    否则缩放时（Lanczos）透明区的白色会渗进轮廓，边缘发白发虚 —— 实测不加这一步，
    轮廓半透明像素里有三成是近白色的白晕。
    """
    arr = np.array(im.convert('RGBA'))
    opaque = arr[:, :, 3] > 0
    if opaque.all() or not opaque.any():
        return im
    idx = distance_transform_edt(~opaque, return_distances=False, return_indices=True)
    arr[:, :, :3] = arr[idx[0], idx[1], :3]
    return Image.fromarray(arr)


def keyed(fname):
    """抠白底（去白边 → 边缘补色）→ 裁到 alpha 内容范围。"""
    p = os.path.join(RAW_BG_DIR, fname)
    if not os.path.exists(p):
        return None
    im = remove_white_bg_floodfill(Image.open(p), threshold=230)
    im = bleed_edges(despill_white_edge(im))
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def cover_crop(im, tw, th, vanchor='top', hanchor='center'):
    """等比缩放到**刚好盖住** tw x th，再裁掉多余的一边。

    绝不拉伸（`max` 而不是分别缩放）——对条带类素材（盐场 / 远景墙 / 中景村舍）来说，
    竖着压扁会把盐堆、房屋、垭口压成一片糊，所以宁可裁。
    """
    w, h = im.size
    s = max(tw / float(w), th / float(h))
    nw, nh = max(tw, int(round(w * s))), max(th, int(round(h * s)))
    im2 = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = 0 if hanchor == 'left' else ((nw - tw) // 2 if hanchor == 'center' else nw - tw)
    y = 0 if vanchor == 'top' else nh - th
    return im2.crop((x, y, x + tw, y + th))


def portrait_window(im, aspect, min_alpha=8):
    """在内容里找一块宽高比 = aspect 的竖窗口，取山体最厚的一列。

    大罗山是「左侧高耸、向右缓降」的横构图，但游戏里它是个 160x380 的竖地标，
    所以取左边主峰那一块，而不是把整条山脉挤成竖的。
    """
    a = np.array(im)[:, :, 3]
    H, W = a.shape
    win = max(1, int(round(H * aspect)))
    if win >= W:
        return im
    col = (a > min_alpha).sum(axis=0).astype(np.float64)
    cs = np.concatenate([[0.0], np.cumsum(col)])
    sums = cs[win:] - cs[:-win]
    x0 = int(np.argmax(sums))
    return im.crop((x0, 0, x0 + win, H))


def emit(im2x, name, w1, h1):
    """写 1x（设计尺寸）+ @2x（2 倍主稿）。

    先按 2 倍尺寸加工，1x 再由它降采样——两张是同一构图，@2x 里的细节是真的，
    不是 1x 放大。引擎（`Assets.ts` 的 `hiPathOf`）优先读 @2x，缺了才退回 1x。
    """
    im2x.save(os.path.join(BG_DIR, name + '@2x.png'), 'PNG')
    im2x.resize((w1, h1), Image.Resampling.LANCZOS).save(
        os.path.join(BG_DIR, name + '.png'), 'PNG')
    print('  Saved %-26s 1x %dx%d  @2x %dx%d' % (name, w1, h1, w1 * 2, h1 * 2))


def postprocess_all():
    # 1. 天空（全幅画面，1280x720；宽高比只差 0.8%，直接缩）
    for fname in ["d01_sky_day.jpg", "d02_sky_dusk.jpg", "d03_sky_night.jpg"]:
        p = os.path.join(RAW_BG_DIR, fname)
        if os.path.exists(p):
            im = Image.open(p).convert("RGBA")
            emit(im.resize((2560, 1440), Image.Resampling.LANCZOS),
                 fname.replace(".jpg", ""), 1280, 720)

    # 2. 大罗山（竖地标，显示 160x380）：取左边主峰那一竖条，等比缩，不压扁
    im = keyed("b09_daluo_mountain.jpg")
    if im is not None:
        im = portrait_window(im, 160.0 / 380.0)
        emit(im.resize((320, 760), Image.Resampling.LANCZOS), 'b09_daluo_mountain', 160, 380)

    # 3. 条带（显示尺寸见 Assets.ts）：等比缩到刚好盖住 -> 裁，绝不拉伸
    strips = [
        # 盐堆 / 地面在下方 -> 锚底
        ("b10_outer_salt_flat.jpg", "b10_outer_salt_flat", (1120, 120), 'bottom'),
        ("b11_coast.jpg", "b11_coast", (520, 160), 'bottom'),
        # 远景城垣 / 中景村舍：要留住垭口雉堞和屋脊天际线 -> 锚顶
        ("d06_horizon_silhouette.jpg", "d06_horizon_silhouette", (1280, 160), 'top'),
        ("d08_mid_houses.jpg", "d08_mid_houses", (1280, 160), 'top'),
    ]
    for src_n, dst_n, (w1, h1), vanchor in strips:
        im = keyed(src_n)
        if im is not None:
            emit(cover_crop(im, w1 * 2, h1 * 2, vanchor), dst_n, w1, h1)


def main():
    only_post = "--post" in sys.argv or "--only-post" in sys.argv
    if not only_post:
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
