import os
import glob
from collections import deque
from PIL import Image
import numpy as np

DOWNLOADS = r"C:\Users\jakfc\Downloads"
ASSETS = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\assets"

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

def split_horizontal_frames(im_rgba, expected_n):
    """Split a horizontal sprite sheet into `expected_n` frames cleanly using vertical alpha projection."""
    arr = np.array(im_rgba)
    alpha = arr[:, :, 3] > 10
    col_sum = np.sum(alpha, axis=0)
    w = arr.shape[1]

    # Find contiguous non-empty horizontal segments
    segments = []
    in_seg = False
    start = 0
    for x in range(w):
        if col_sum[x] > 0 and not in_seg:
            in_seg = True
            start = x
        elif col_sum[x] == 0 and in_seg:
            in_seg = False
            if x - start > 10:
                segments.append((start, x))
    if in_seg and w - start > 10:
        segments.append((start, w))

    # Merge tiny detached gaps (< 12px) or reduce if > expected_n
    while len(segments) > expected_n:
        # Find smallest gap between adjacent segments and merge
        min_gap = 10**9
        min_idx = 0
        for i in range(len(segments) - 1):
            gap = segments[i + 1][0] - segments[i][1]
            if gap < min_gap:
                min_gap = gap
                min_idx = i
        merged = (segments[min_idx][0], segments[min_idx + 1][1])
        segments = segments[:min_idx] + [merged] + segments[min_idx + 2:]

    # If fewer than expected_n (e.g. 2 frames slightly touched), split widest segment at lowest valley
    while len(segments) < expected_n:
        widest_idx = max(range(len(segments)), key=lambda i: segments[i][1] - segments[i][0])
        sx, ex = segments[widest_idx]
        mid_start = sx + (ex - sx) // 4
        mid_end = ex - (ex - sx) // 4
        split_x = mid_start + int(np.argmin(col_sum[mid_start:mid_end]))
        segments = segments[:widest_idx] + [(sx, split_x), (split_x, ex)] + segments[widest_idx + 1:]

    frames = []
    for sx, ex in segments:
        sub = im_rgba.crop((sx, 0, ex, im_rgba.height))
        # Remove small disconnected edge fragments from neighboring frames
        s_arr = np.array(sub)
        s_alpha = s_arr[:, :, 3] > 10
        sh, sw = s_alpha.shape
        comp = np.zeros((sh, sw), dtype=np.int32)
        cid = 0
        sizes = {}
        for yy in range(sh):
            for xx in range(sw):
                if s_alpha[yy, xx] and comp[yy, xx] == 0:
                    cid += 1
                    cnt = 0
                    qq = deque([(yy, xx)])
                    comp[yy, xx] = cid
                    while qq:
                        cy, cx = qq.popleft()
                        cnt += 1
                        for dy, dx in ((-1,0),(1,0),(0,-1),(0,1)):
                            ny, nx = cy+dy, cx+dx
                            if 0 <= ny < sh and 0 <= nx < sw and s_alpha[ny, nx] and comp[ny, nx] == 0:
                                comp[ny, nx] = cid
                                qq.append((ny, nx))
                    sizes[cid] = cnt
        if sizes:
            max_sz = max(sizes.values())
            for k, sz in sizes.items():
                if sz < max_sz * 0.12:
                    # Only drop if it touches left/right cut edge
                    ys, xs = np.where(comp == k)
                    if np.min(xs) <= 2 or np.max(xs) >= sw - 3:
                        s_arr[comp == k, 3] = 0
        sub_clean = Image.fromarray(s_arr)
        bbox = sub_clean.getbbox()
        if bbox:
            frames.append(sub_clean.crop(bbox))
    return frames

def export_sheet(src_pattern, out_names, target_dir, target_size=(128, 192), flip_h=False):
    matches = glob.glob(os.path.join(DOWNLOADS, src_pattern))
    if not matches:
        print("NOT FOUND:", src_pattern)
        return
    src = sorted(matches, key=os.path.getmtime, reverse=True)[0]
    im = remove_white_bg_floodfill(Image.open(src))
    if flip_h:
        from PIL import ImageOps
        im = ImageOps.mirror(im)
    frames = split_horizontal_frames(im, len(out_names))
    if flip_h:
        # Mirroring the whole sheet reversed left-to-right frame order, so reverse back!
        frames = list(reversed(frames))

    # Compute uniform scale across all frames in this sheet so character size stays rock-steady
    tw, th = target_size
    max_fw = max(f.width for f in frames)
    max_fh = max(f.height for f in frames)
    scale_1x = min((tw - 8) / max_fw, (th - 8) / max_fh)
    scale_2x = min((tw * 2 - 16) / max_fw, (th * 2 - 16) / max_fh)

    os.makedirs(target_dir, exist_ok=True)
    for frame, name in zip(frames, out_names):
        for sc, sz, suffix in [(scale_1x, (tw, th), ""), (scale_2x, (tw * 2, th * 2), "@2x")]:
            nw = max(1, int(round(frame.width * sc)))
            nh = max(1, int(round(frame.height * sc)))
            res = frame.resize((nw, nh), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", sz, (0, 0, 0, 0))
            px = (sz[0] - nw) // 2
            py = sz[1] - (4 if suffix == "" else 8) - nh
            canvas.paste(res, (px, py), res)
            out_path = os.path.join(target_dir, f"{name}{suffix}.png")
            canvas.save(out_path, "PNG")
    print(f"Exported {len(out_names)} frames from {os.path.basename(src)} -> {target_dir}")

if __name__ == "__main__":
    p_dir = os.path.join(ASSETS, "sprites", "player")
    export_sheet("Ming_dynasty_commander_walking_c*.jpg", [f"player_walk_{i:02d}" for i in range(1, 5)], p_dir)
    export_sheet("Ming_dynasty_commander_sword_strike*.jpg", [f"player_attack_{i:02d}" for i in range(1, 4)], p_dir)
    export_sheet("Ming_dynasty_commander_sprite_sheet*.jpg", ["player_qilin_01", "player_qilin_02", "player_qilin_03", "player_hurt_01"], p_dir)
