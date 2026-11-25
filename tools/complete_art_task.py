import os
from PIL import Image, ImageDraw
import numpy as np

ROOT = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test"
ASSETS = os.path.join(ROOT, "assets")
BG_DIR = os.path.join(ASSETS, "bg")
PROPS_DIR = os.path.join(ASSETS, "sprites", "props")
BLDG_DIR = os.path.join(ASSETS, "buildings")

def hex_to_rgba(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

OUTLINE = hex_to_rgba("#1A202C")

# -------------------------------------------------------------
# A. 地面铺装变体 (640x160 1x + 1280x320 @2x, 绝对无缝且同色板/同亮度)
# -------------------------------------------------------------
def generate_ground_variants():
    # 1. d05_ground_beach_b & _c derived directly from d05_ground_beach.png
    #    keeping the exact left/right edge 40px seams, horizon, and mud strata intact,
    #    while rearranging & varying interior puddles, reeds, pebbles, and shells!
    beach_src = Image.open(os.path.join(BG_DIR, "d05_ground_beach.png")).convert("RGBA")
    # Upscale base to 1280x320 cleanly for @2x working canvas
    base_2x = beach_src.resize((1280, 320), Image.Resampling.LANCZOS)
    # Also save d05_ground_beach@2x.png if missing
    beach_2x_path = os.path.join(BG_DIR, "d05_ground_beach@2x.png")
    if not os.path.exists(beach_2x_path):
        base_2x.save(beach_2x_path, "PNG")

    arr = np.array(base_2x)
    # Identify top grass/sky line and horizontal bands:
    # We'll create B and C by circularly shifting interior bands and adding/rearranging
    # crisp pebbles, shells, and reed variations while keeping edge strips [0:48] & [1232:1280] identical!
    def make_beach_variant(out_name, shift_top, shift_bot, seed):
        v = arr.copy()
        # Circularly shift the interior ground [48:1232] differently for surface vs deep strata
        # Actually, shifting the whole image circularly by shift_x preserves seamlessness if we
        # blend/keep edge continuity — wait: since d05_ground_beach.png itself tiles seamlessly,
        # ANY circular horizontal roll (np.roll(..., shift, axis=1)) is ALSO 100% seamlessly tileable
        # and has the EXACT same horizon & brightness!
        # Even better: roll top half (y<115) by shift_top and deep mud (y>=115) by shift_bot,
        # AND stamp extra clean pebbles/shells/water glints in the middle!
        v[:112, :] = np.roll(arr[:112, :], shift_top, axis=1)
        v[112:, :] = np.roll(arr[112:, :], shift_bot, axis=1)
        im_v = Image.fromarray(v)
        d = ImageDraw.Draw(im_v)
        rng = np.random.default_rng(seed)
        # Add subtle varied shells & pebbles on the sand strip (y: 88..112)
        for _ in range(7):
            px = int(rng.uniform(80, 1180))
            py = int(rng.uniform(92, 110))
            pr = int(rng.uniform(4, 8))
            col = hex_to_rgba("#E2E8F0" if rng.random() > 0.5 else "#718096")
            d.ellipse([px - pr, py - pr // 2, px + pr, py + pr // 2], fill=col, outline=OUTLINE, width=1)
        # Save @2x (1280x320) and 1x (640x160)
        p_2x = os.path.join(BG_DIR, out_name.replace(".png", "@2x.png"))
        p_1x = os.path.join(BG_DIR, out_name)
        im_v.save(p_2x, "PNG")
        im_v.resize((640, 160), Image.Resampling.LANCZOS).save(p_1x, "PNG")
        print(f"Generated {out_name} (640x160 & @2x)")

    make_beach_variant("d05_ground_beach_b.png", shift_top=360, shift_bot=740, seed=15581)
    make_beach_variant("d05_ground_beach_c.png", shift_top=820, shift_bot=290, seed=15582)

    # 2. d04_ground_fortress_b.png: same structure/horizon/palette as d04_ground_fortress.png,
    #    rearranged flagstone joints + subtle moss patches + shifted strata stones!
    fort_src = Image.open(os.path.join(BG_DIR, "d04_ground_fortress.png")).convert("RGBA")
    fort_2x = fort_src.resize((1280, 320), Image.Resampling.LANCZOS)
    fort_2x_path = os.path.join(BG_DIR, "d04_ground_fortress@2x.png")
    if not os.path.exists(fort_2x_path):
        fort_2x.save(fort_2x_path, "PNG")

    f_arr = np.array(fort_2x)
    # Roll top stone pavement (y<108) and earth strata (y>=108) independently
    fb = f_arr.copy()
    fb[:108, :] = np.roll(f_arr[:108, :], 480, axis=1)
    fb[108:, :] = np.roll(f_arr[108:, :], 260, axis=1)
    im_fb = Image.fromarray(fb)
    df = ImageDraw.Draw(im_fb)
    # Add subtle Ming courtyard moss tufts along stone joints (y: 26..96)
    moss_c = hex_to_rgba("#48BB78", 140)
    moss_dark = hex_to_rgba("#2F4F4F", 160)
    for mx, my in [(180, 48), (460, 88), (740, 44), (1020, 86)]:
        df.ellipse([mx - 12, my - 4, mx + 12, my + 4], fill=moss_dark)
        df.ellipse([mx - 8, my - 3, mx + 8, my + 2], fill=moss_c)
    im_fb.save(os.path.join(BG_DIR, "d04_ground_fortress_b@2x.png"), "PNG")
    im_fb.resize((640, 160), Image.Resampling.LANCZOS).save(os.path.join(BG_DIR, "d04_ground_fortress_b.png"), "PNG")
    print("Generated d04_ground_fortress_b.png (640x160 & @2x)")

# -------------------------------------------------------------
# B. 地面碎屑 (6 件独立透明小图，底边贴地，1x + @2x)
# -------------------------------------------------------------
def save_1x_2x_from_4x(im_4x, out_1x_path, target_1x_size):
    w1, h1 = target_1x_size
    im_2x = im_4x.resize((w1 * 2, h1 * 2), Image.Resampling.LANCZOS)
    im_1x = im_2x.resize((w1, h1), Image.Resampling.LANCZOS)
    im_2x.save(out_1x_path.replace(".png", "@2x.png"), "PNG")
    im_1x.save(out_1x_path, "PNG")
    print(f"Saved {os.path.basename(out_1x_path)} ({w1}x{h1} & @2x {w1*2}x{h1*2})")

def generate_decals():
    # Render each decal at 4x supersampling so 1x & @2x have crisp anti-aliased outlines!
    # 1. decal_rock_01: 2~3 grouped gray-brown stones, 1x h=10, w=26 -> 4x 104x40
    im = Image.new("RGBA", (104, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(8, 38), (18, 12), (46, 8), (64, 24), (60, 38)], fill=hex_to_rgba("#718096"), outline=OUTLINE, width=4)
    d.polygon([(18, 12), (46, 8), (38, 22), (16, 26)], fill=hex_to_rgba("#A0AEC0"))
    d.polygon([(52, 38), (62, 18), (84, 16), (96, 38)], fill=hex_to_rgba("#5A6772"), outline=OUTLINE, width=4)
    save_1x_2x_from_4x(im, os.path.join(PROPS_DIR, "decal_rock_01.png"), (26, 10))

    # 2. decal_rock_02: single pebble, 1x h=7, w=14 -> 4x 56x28
    im = Image.new("RGBA", (56, 28), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([4, 4, 52, 26], fill=hex_to_rgba("#718096"), outline=OUTLINE, width=4)
    d.arc([10, 6, 40, 18], start=190, end=330, fill=hex_to_rgba("#CBD5E0"), width=3)
    save_1x_2x_from_4x(im, os.path.join(PROPS_DIR, "decal_rock_02.png"), (14, 7))

    # 3. decal_grass_01: reed/sea-grass clump 3~5 blades, 1x h=14, w=24 -> 4x 96x56
    im = Image.new("RGBA", (96, 56), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    blades = [
        ([(36, 54), (16, 16), (44, 54)], "#48BB78"),
        ([(44, 54), (38, 6), (52, 54)], "#68A357"),
        ([(50, 54), (62, 10), (58, 54)], "#48BB78"),
        ([(56, 54), (82, 20), (64, 54)], "#2F855A"),
    ]
    for pts, col in blades:
        d.polygon(pts, fill=hex_to_rgba(col), outline=OUTLINE, width=3)
    save_1x_2x_from_4x(im, os.path.join(PROPS_DIR, "decal_grass_01.png"), (24, 14))

    # 4. decal_grass_02: short grass tuft, 1x h=11, w=20 -> 4x 80x44
    im = Image.new("RGBA", (80, 44), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for pts, col in [
        ([(28, 42), (12, 14), (36, 42)], "#68A357"),
        ([(38, 42), (40, 6), (46, 42)], "#48BB78"),
        ([(46, 42), (66, 16), (54, 42)], "#2F855A"),
    ]:
        d.polygon(pts, fill=hex_to_rgba(col), outline=OUTLINE, width=3)
    save_1x_2x_from_4x(im, os.path.join(PROPS_DIR, "decal_grass_02.png"), (20, 11))

    # 5. decal_shell_01: white + pale pink seashell, 1x h=6, w=12 -> 4x 48x24
    im = Image.new("RGBA", (48, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.chord([4, 2, 44, 28], start=180, end=360, fill=hex_to_rgba("#FED7D7"), outline=OUTLINE, width=3)
    d.pieslice([12, 6, 36, 24], start=180, end=360, fill=hex_to_rgba("#FFFFFF"))
    d.rectangle([16, 18, 32, 22], fill=hex_to_rgba("#FBB6CE"), outline=OUTLINE, width=2)
    save_1x_2x_from_4x(im, os.path.join(PROPS_DIR, "decal_shell_01.png"), (12, 6))

    # 6. decal_wood_01: broken driftwood piece, 1x h=8, w=26 -> 4x 104x32
    im = Image.new("RGBA", (104, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(6, 26), (16, 12), (96, 8), (88, 20), (98, 28), (12, 30)], fill=hex_to_rgba("#8C6D46"), outline=OUTLINE, width=3)
    d.line([(20, 20), (80, 16)], fill=hex_to_rgba("#5C4028"), width=3)
    save_1x_2x_from_4x(im, os.path.join(PROPS_DIR, "decal_wood_01.png"), (26, 8))

# -------------------------------------------------------------
# C. 银两飘袋动画 (2 件: fx_silver_pouch, fx_silver_rise)
# -------------------------------------------------------------
def generate_silver_fx():
    # 1. fx_silver_pouch.png (1x h=30, w=26; @2x 52x60, tied cloth pouch, bottom aligned)
    im = Image.new("RGBA", (104, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Ruffled pouch top
    d.polygon([(34, 12), (52, 22), (70, 12), (62, 38), (42, 38)], fill=hex_to_rgba("#CBD5E0"), outline=OUTLINE, width=4)
    # Round belly of silver pouch (bottom flush at y=118)
    d.ellipse([14, 34, 90, 118], fill=hex_to_rgba("#E2E8F0"), outline=OUTLINE, width=4)
    # Right-side shade crescent
    d.chord([14, 34, 90, 118], start=310, end=80, fill=hex_to_rgba("#A0AEC0"))
    # Tied hemp rope at neck
    d.rounded_rectangle([34, 32, 70, 44], radius=4, fill=hex_to_rgba("#D6B36A"), outline=OUTLINE, width=4)
    d.line([(52, 42), (38, 60)], fill=hex_to_rgba("#D6B36A"), width=5)
    d.line([(52, 42), (66, 60)], fill=hex_to_rgba("#D6B36A"), width=5)
    save_1x_2x_from_4x(im, os.path.join(PROPS_DIR, "fx_silver_pouch.png"), (26, 30))

    # 2. fx_silver_rise.png (1x 22x30, @2x 44x60: Ming silver sycee ingot + rising glow trail)
    im = Image.new("RGBA", (88, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Rising trail streaks downward
    d.polygon([(28, 48), (60, 48), (52, 114), (36, 114)], fill=hex_to_rgba("#FEFCBF", 120))
    d.line([(32, 52), (32, 100)], fill=hex_to_rgba("#F6E05E", 190), width=4)
    d.line([(56, 52), (56, 108)], fill=hex_to_rgba("#F6E05E", 190), width=4)
    # Silver ingot (sycee) at top
    d.polygon([(12, 22), (76, 22), (64, 48), (24, 48)], fill=hex_to_rgba("#E2E8F0"), outline=OUTLINE, width=4)
    d.ellipse([24, 10, 64, 28], fill=hex_to_rgba("#FFFFFF"), outline=OUTLINE, width=4)
    d.ellipse([34, 14, 54, 24], fill=hex_to_rgba("#CBD5E0"))
    save_1x_2x_from_4x(im, os.path.join(PROPS_DIR, "fx_silver_rise.png"), (22, 30))

# -------------------------------------------------------------
# D. 东门铁闸 (b06_east_gate_portcullis.png: 1x w=62, h=80; @2x w=124, h=160)
# -------------------------------------------------------------
def generate_portcullis():
    # Render at 4x (248x320) -> downsample cleanly to 124x160 (@2x) and 62x80 (1x)
    w4, h4 = 248, 320
    im = Image.new("RGBA", (w4, h4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    wood_main = hex_to_rgba("#6E4E32")
    wood_dark = hex_to_rgba("#4A3320")
    iron_main = hex_to_rgba("#4A5568")
    iron_dark = hex_to_rgba("#2D3748")
    iron_hi = hex_to_rgba("#718096")

    # Vertical iron bars (6 bars) + spikes at bottom (y=318)
    spike_h = 26
    frame_bot = h4 - spike_h
    bar_xs = [36, 74, 112, 136, 174, 212]
    for bx in bar_xs:
        d.rectangle([bx - 8, 12, bx + 8, frame_bot], fill=iron_main, outline=OUTLINE, width=4)
        d.line([(bx - 4, 16), (bx - 4, frame_bot - 4)], fill=iron_hi, width=3)
        # Sharp iron spike at bottom edge (tip touches y=318)
        d.polygon([(bx - 8, frame_bot), (bx + 8, frame_bot), (bx, h4 - 2)], fill=iron_dark, outline=OUTLINE, width=4)

    # Horizontal iron cross-bars (4 bars)
    for by in [64, 128, 192, 256]:
        d.rectangle([12, by - 8, w4 - 12, by + 8], fill=iron_main, outline=OUTLINE, width=4)
        d.line([(16, by - 4), (w4 - 16, by - 4)], fill=iron_hi, width=3)

    # Heavy Ming timber outer frame (left, right, top, bottom beam)
    d.rectangle([4, 4, 24, frame_bot], fill=wood_main, outline=OUTLINE, width=4)
    d.rectangle([w4 - 24, 4, w4 - 4, frame_bot], fill=wood_dark, outline=OUTLINE, width=4)
    d.rectangle([4, 4, w4 - 4, 28], fill=wood_main, outline=OUTLINE, width=4)
    d.rectangle([4, frame_bot - 22, w4 - 4, frame_bot], fill=wood_dark, outline=OUTLINE, width=4)

    # Iron rivets at intersections
    for bx in bar_xs:
        for by in [16, 64, 128, 192, 256, frame_bot - 11]:
            d.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=hex_to_rgba("#CBD5E0"), outline=OUTLINE, width=2)

    save_1x_2x_from_4x(im, os.path.join(BLDG_DIR, "b06_east_gate_portcullis.png"), (62, 80))

# -------------------------------------------------------------
# E. 顺手补缺的 @2x 主稿
# -------------------------------------------------------------
def generate_missing_2x():
    targets = [
        "sprites/props/fx_recruit.png",
        "sprites/tools/salvage_salt_bag.png",
        "sprites/tools/salvage_driftwood.png",
        "ui/e01_top_bar.png",
        "ui/e02_bottom_bar.png",
        "ui/e04_btn_normal.png",
        "ui/e11_boss_bar.png",
        "ui/e03_modal_dialog.png",
        "ui/icons/icon_day.png",
        "ui/icons/icon_night.png",
        "ui/icons/icon_silver.png",
        "ui/icons/icon_grain.png",
        "ui/icons/icon_population.png",
        "sprites/villagers/villager_salt_worker_work_02.png",
        "sprites/villagers/villager_salt_worker_work_03.png",
    ]
    for rel in targets:
        p1 = os.path.join(ASSETS, rel)
        p2 = p1.replace(".png", "@2x.png")
        if not os.path.exists(p1):
            print(f"SKIP (1x not on disk): {rel}")
            continue
        if os.path.exists(p2):
            print(f"OK (already has @2x): {rel}")
            continue
        im = Image.open(p1).convert("RGBA")
        im2 = im.resize((im.width * 2, im.height * 2), Image.Resampling.LANCZOS)
        im2.save(p2, "PNG")
        print(f"Created @2x: {rel.replace('.png', '@2x.png')} ({im2.width}x{im2.height})")

if __name__ == "__main__":
    generate_ground_variants()
    generate_decals()
    generate_silver_fx()
    generate_portcullis()
    generate_missing_2x()
    print("ALL ART TASK ITEMS COMPLETED!")
