import os
import sys
import subprocess
from collections import deque
import cv2
import numpy as np
from PIL import Image

sys.path.append(r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\tools")
import slice_sprite_sheet as sss

ASSETS_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\assets\sprites"
VIDEO_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\raw_assets\gflow_videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

UNITS = [
    # (name, sub_dir, ref_file, out_prefix, target_size, direction, desc, strip_bucket)
    ("villager_idle", "villagers", "villager_idle_01@2x.png", "villager_idle_walk", (128, 192), "right",
     "Ming dynasty coastal villager walking in place facing right in a smooth natural rhythmic walking gait cycle, alternating left and right legs and swinging arms naturally", False),
    ("villager_farmer", "villagers", "villager_farmer_01@2x.png", "villager_farmer_walk", (128, 192), "right",
     "Ming dynasty peasant farmer in straw hat carrying a hoe on his shoulder, walking in place facing right in a smooth natural rhythmic walking gait cycle, alternating legs naturally", False),
    ("villager_salt_worker", "villagers", "villager_salt_worker_01@2x.png", "villager_salt_worker_walk", (128, 192), "right",
     "Ming dynasty salt worker holding a long wooden salt shovel, walking in place facing right in a smooth natural rhythmic walking gait cycle, alternating legs naturally", True),
    ("villager_builder", "villagers", "villager_builder_01@2x.png", "villager_builder_walk", (128, 192), "right",
     "Ming dynasty stonemason builder with wooden mallet and ruler, walking in place facing right in a smooth natural rhythmic walking gait cycle, alternating legs and swinging arm naturally", False),
    ("villager_militia", "villagers", "villager_militia_01@2x.png", "villager_militia_walk", (128, 192), "right",
     "Ming dynasty militia soldier in lamellar chest armor holding a long spear, marching in place facing right in a smooth natural rhythmic marching gait cycle, alternating legs naturally", False),
    ("villager_kung_fu", "villagers", "villager_kung_fu_01@2x.png", "villager_kung_fu_walk", (128, 192), "right",
     "Ming dynasty bare-chested Chinese martial artist with red wrist wraps, walking forward in place facing right in a brisk athletic martial walking gait cycle, alternating legs naturally", False),
    ("enemy_scout", "enemies", "enemy_scout_01@2x.png", "enemy_scout_walk", (128, 192), "LEFT",
     "16th-century wokou pirate scout in tattered dark cloak with katana, stalking/walking in place facing LEFT in a smooth rhythmic prowling gait cycle, alternating legs naturally", False),
    ("enemy_samurai", "enemies", "enemy_samurai_01@2x.png", "enemy_samurai_walk", (128, 192), "LEFT",
     "16th-century wokou elite samurai in crimson armor and demon mask holding an odachi katana, marching in place facing LEFT in a smooth rhythmic heavy walking gait cycle, alternating legs naturally", False),
    ("enemy_boss", "enemies", "enemy_boss_01@2x.png", "enemy_boss_walk", (192, 256), "LEFT",
     "Towering 16th-century wokou warlord boss in horned kabuto helmet and dark blood-red armor holding dual katanas, marching in place facing LEFT in a heavy intimidating walking gait cycle, alternating legs naturally", False),
]

def remove_detached_bucket(im_rgba):
    """Remove the detached wooden bucket on the bottom-left of salt_worker if present."""
    arr = np.array(im_rgba)
    alpha = arr[:, :, 3] > 10
    h, w = alpha.shape
    comp = np.zeros((h, w), dtype=np.int32)
    cid = 0
    sizes = {}
    for y in range(h):
        for x in range(w):
            if alpha[y, x] and comp[y, x] == 0:
                cid += 1
                cnt = 0
                q = deque([(y, x)])
                comp[y, x] = cid
                while q:
                    cy, cx = q.popleft()
                    cnt += 1
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and alpha[ny, nx] and comp[ny, nx] == 0:
                            comp[ny, nx] = cid
                            q.append((ny, nx))
                sizes[cid] = cnt
    if sizes:
        best_id = max(sizes, key=sizes.get)
        arr[comp != best_id, 3] = 0
    return Image.fromarray(arr)

def prepare_start_end_frame(src_path, out_path, strip_bucket=False):
    im = Image.open(src_path).convert("RGBA")
    if strip_bucket:
        im = remove_detached_bucket(im)
        bbox = im.getbbox()
        if bbox:
            im = im.crop(bbox)
    canvas = Image.new("RGB", (720, 1280), (255, 255, 255))
    scale = min(620 / im.width, 1080 / im.height)
    nw, nh = int(im.width * scale), int(im.height * scale)
    res = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas.paste(res, ((720 - nw) // 2, 1280 - 80 - nh), res)
    canvas.save(out_path, "PNG")

def extract_walk_frames(mp4_path, out_dir, out_prefix, target_size):
    cap = cv2.VideoCapture(mp4_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total < 10:
        raise RuntimeError(f"Video {mp4_path} has too few frames: {total}")
    # Sample 6 evenly spaced mid-stride frames (skip static start/end)
    indices = [int((i + 1) * (total - 1) / 7.5) for i in range(6)]
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if ok:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            im_rgba = sss.remove_white_bg_floodfill(Image.fromarray(rgb), threshold=232)
            bbox = im_rgba.getbbox()
            if bbox:
                frames.append(im_rgba.crop(bbox))
    cap.release()

    tw, th = target_size
    max_fw = max(f.width for f in frames)
    max_fh = max(f.height for f in frames)
    sc1 = min((tw - 8) / max_fw, (th - 8) / max_fh)
    sc2 = min((tw * 2 - 16) / max_fw, (th * 2 - 16) / max_fh)

    for i, frame in enumerate(frames, start=1):
        name = f"{out_prefix}_{i:02d}"
        for sc, sz, suf in [(sc1, (tw, th), ""), (sc2, (tw * 2, th * 2), "@2x")]:
            nw = max(1, int(round(frame.width * sc)))
            nh = max(1, int(round(frame.height * sc)))
            res = frame.resize((nw, nh), Image.Resampling.LANCZOS)
            c = Image.new("RGBA", sz, (0, 0, 0, 0))
            c.paste(res, ((sz[0] - nw) // 2, sz[1] - (4 if suf == "" else 8) - nh), res)
            c.save(os.path.join(out_dir, f"{name}{suf}.png"), "PNG")
    print(f"Extracted {len(frames)} smooth frames -> {out_prefix}_01..06.png", flush=True)

def main():
    for name, sub_dir, ref_file, out_prefix, target_size, direction, desc, strip_bucket in UNITS:
        ref_path = os.path.join(ASSETS_DIR, sub_dir, ref_file)
        se_path = os.path.join(VIDEO_DIR, f"{name}_start_end.png")
        mp4_path = os.path.join(VIDEO_DIR, f"{name}_walk.mp4")
        out_dir = os.path.join(ASSETS_DIR, sub_dir)

        prepare_start_end_frame(ref_path, se_path, strip_bucket=strip_bucket)
        prompt = (
            f"2D game character {desc}, keeping the character centered in frame. "
            f"Strict locked-off static orthographic 2D side-view camera facing {direction}, "
            f"NO camera movement, NO zoom, NO pan, flat semi-shaded Chinese guofeng 2D animation "
            f"with clean 1.5px dark outlines on a completely pure solid white background, no ground shadow."
        )

        if not os.path.exists(mp4_path):
            print(f"\n=== Generating video for {name} ===", flush=True)
            cmd = [
                "gflow", "video", "i2v",
                "--initial-frame", se_path,
                "--end-frame", se_path,
                prompt,
                "--model", "omni-1.2-flash",
                "--duration", "3",
                "--aspect", "9:16",
                "--out-file", mp4_path,
            ]
            res = subprocess.run(cmd, capture_output=False)
            if res.returncode != 0:
                print(f"WARN: {name} failed with code {res.returncode}, retrying once...", flush=True)
                res = subprocess.run(cmd, capture_output=False)
                if res.returncode != 0:
                    print(f"ERROR: {name} failed after retry, skipping.", flush=True)
                    continue
        else:
            print(f"\n=== Reusing existing video {mp4_path} ===", flush=True)

        extract_walk_frames(mp4_path, out_dir, out_prefix, target_size)

    print("\nALL 9 UNIT WALK ANIMATIONS COMPLETED!", flush=True)

if __name__ == "__main__":
    main()
