import os
import math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np

ASSETS_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\assets"

def hex_to_rgba(hex_code, alpha=255):
    h = hex_code.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)

OUTLINE = hex_to_rgba("#1A202C")

def draw_stone_courses(d, x0, y0, x1, y1, row_h=16, col_w=34, base_c="#718096", hi_c="#8A99AD", sh_c="#4A5568", batter=0.0):
    """Draw clean Ming granite ashlar stone courses with staggered joints and 1.5px outlines."""
    total_h = y1 - y0
    rows = max(1, int(total_h // row_h))
    actual_rh = total_h / rows
    for r in range(rows):
        ry0 = y0 + r * actual_rh
        ry1 = y0 + (r + 1) * actual_rh
        t0 = r / rows
        t1 = (r + 1) / rows
        lx0 = x0 + batter * (1 - t0)
        rx0 = x1 - batter * (1 - t0)
        lx1 = x0 + batter * (1 - t1)
        rx1 = x1 - batter * (1 - t1)
        # Alternating subtle tone per row
        fill_c = hex_to_rgba(base_c if r % 2 == 0 else "#64748B")
        d.polygon([(lx0, ry0), (rx0, ry0), (rx1, ry1), (lx1, ry1)], fill=fill_c)
        # Top-left highlight line
        d.line([(lx0 + 1, ry0 + 1), (rx0 - 1, ry0 + 1)], fill=hex_to_rgba(hi_c, 160), width=1)
        # Horizontal course line
        d.line([(lx1, ry1), (rx1, ry1)], fill=OUTLINE, width=2)
        # Staggered vertical stone joints
        offset = (col_w // 2) if (r % 2 == 1) else 0
        row_w = rx0 - lx0
        jx = lx0 + offset + col_w
        while jx < rx0 - 10:
            # Slight right-side shadow block
            if jx > (lx0 + rx0) * 0.68:
                d.polygon([(jx, ry0), (min(rx0, jx + col_w), ry0), (min(rx1, jx + col_w), ry1), (jx, ry1)], fill=hex_to_rgba(sh_c, 120))
            d.line([(jx, ry0), (jx, ry1)], fill=OUTLINE, width=2)
            jx += col_w

def draw_ming_tiled_roof(d, x_left, x_right, y_eave, y_ridge, tile_c="#3B4A59", dark_c="#2D3748", ridge_c="#4A5568"):
    """Draw a clean Ming blue-gray hip-and-gable tiled roof matching b01_shrine / b06_east_gate."""
    inset = (x_right - x_left) * 0.14
    poly = [(x_left, y_eave), (x_right, y_eave), (x_right - inset, y_ridge), (x_left + inset, y_ridge)]
    d.polygon(poly, fill=hex_to_rgba(tile_c), outline=OUTLINE, width=2)
    # Right shaded slope
    d.polygon([(x_right - inset*1.8, y_eave), (x_right, y_eave), (x_right - inset, y_ridge), (x_right - inset*1.8, y_ridge)], fill=hex_to_rgba(dark_c))
    # Vertical tile ribs
    span = x_right - x_left - 12
    steps = max(4, int(span // 10))
    for i in range(1, steps):
        t = i / steps
        bx = x_left + 6 + t * span
        tx = (x_left + inset) + t * (x_right - x_left - 2 * inset)
        d.line([(bx, y_eave - 1), (tx, y_ridge + 1)], fill=hex_to_rgba("#1A202C", 140), width=1)
    # Upturned eave tips
    d.polygon([(x_left - 6, y_eave - 5), (x_left + 10, y_eave), (x_left + 4, y_eave + 3)], fill=hex_to_rgba(dark_c), outline=OUTLINE, width=2)
    d.polygon([(x_right + 6, y_eave - 5), (x_right - 10, y_eave), (x_right - 4, y_eave + 3)], fill=hex_to_rgba(dark_c), outline=OUTLINE, width=2)
    # Main ridge beam + chiwen ends
    d.rectangle([x_left + inset - 2, y_ridge - 4, x_right - inset + 2, y_ridge + 2], fill=hex_to_rgba(ridge_c), outline=OUTLINE, width=2)
    d.polygon([(x_left + inset - 2, y_ridge - 4), (x_left + inset + 6, y_ridge - 12), (x_left + inset + 8, y_ridge - 4)], fill=hex_to_rgba(ridge_c), outline=OUTLINE, width=2)
    d.polygon([(x_right - inset + 2, y_ridge - 4), (x_right - inset - 6, y_ridge - 12), (x_right - inset - 8, y_ridge - 4)], fill=hex_to_rgba(ridge_c), outline=OUTLINE, width=2)

# -------------------------------------------------------------
# 1. 重绘 B04 内城水门与作坊 (260x380 & @2x)
# -------------------------------------------------------------
def redraw_water_gate():
    b_dir = os.path.join(ASSETS_DIR, "buildings")
    # Render at 2x (520x760) then downsample cleanly for crisp 1.5px outlines
    w, h = 520, 760
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # Bottom aligned: ground at y = 752
    gy = 752
    # Main Yongchang granite wall body (left 340px, height ~390px -> y: 362..752)
    wall_top = 370
    draw_stone_courses(d, 24, wall_top, 356, gy - 20, row_h=28, col_w=56, batter=14)
    # Stone plinth base
    d.rectangle([16, gy - 24, 360, gy], fill=hex_to_rgba("#5A6772"), outline=OUTLINE, width=3)
    # Wall outer border
    d.polygon([(38, wall_top), (342, wall_top), (356, gy - 24), (24, gy - 24)], outline=OUTLINE, width=3)

    # Crenellations (雉堞垛口) on top of water gate wall
    d.rectangle([32, wall_top - 14, 348, wall_top], fill=hex_to_rgba("#718096"), outline=OUTLINE, width=3)
    for cx in range(36, 336, 48):
        d.rectangle([cx, wall_top - 42, cx + 30, wall_top - 14], fill=hex_to_rgba("#718096"), outline=OUTLINE, width=3)
        d.rectangle([cx + 6, wall_top - 34, cx + 14, wall_top - 22], fill=hex_to_rgba("#1A202C"))

    # Arched Water Gate Portal (水门石拱) in center of stone wall
    ax0, ax1 = 112, 268
    arch_top = 500
    # Outer arch voussoir ring
    d.pieslice([ax0 - 16, arch_top - 16, ax1 + 16, arch_top + (ax1 - ax0) + 16], 180, 360, fill=hex_to_rgba("#8A99AD"), outline=OUTLINE, width=3)
    d.rectangle([ax0 - 16, arch_top + (ax1 - ax0)//2, ax1 + 16, gy - 20], fill=hex_to_rgba("#8A99AD"), outline=OUTLINE, width=3)
    # Inner dark gate opening
    d.pieslice([ax0, arch_top, ax1, arch_top + (ax1 - ax0)], 180, 360, fill=hex_to_rgba("#1A202C"), outline=OUTLINE, width=3)
    d.rectangle([ax0, arch_top + (ax1 - ax0)//2, ax1, gy - 20], fill=hex_to_rgba("#1A202C"), outline=OUTLINE, width=3)

    # Iron & timber sluice gate portcullis (raised halfway)
    sluice_bot = 635
    d.rectangle([ax0 + 6, arch_top + 48, ax1 - 6, sluice_bot], fill=hex_to_rgba("#3B3026"), outline=OUTLINE, width=2)
    for sx in range(ax0 + 22, ax1 - 12, 22):
        d.line([(sx, arch_top + 30), (sx, sluice_bot + 10)], fill=hex_to_rgba("#4A5568"), width=5)
        d.line([(sx, arch_top + 30), (sx, sluice_bot + 10)], fill=OUTLINE, width=2)
    for sy in range(arch_top + 60, sluice_bot, 28):
        d.line([(ax0 + 4, sy), (ax1 - 4, sy)], fill=hex_to_rgba("#5A6772"), width=5)

    # Flowing blue canal water at bottom of water gate
    d.rectangle([ax0 - 8, gy - 32, ax1 + 8, gy], fill=hex_to_rgba("#1E4E79"), outline=OUTLINE, width=3)
    d.line([(ax0 + 10, gy - 20), (ax1 - 24, gy - 20)], fill=hex_to_rgba("#63B3ED"), width=3)
    d.line([(ax0 + 30, gy - 10), (ax1 - 10, gy - 10)], fill=hex_to_rgba("#CBD5E0"), width=2)

    # Adjacent Ming Timber Workshop (旁侧作坊) on the right (x: 348..504, y: 460..752)
    wx0, wx1 = 348, 496
    wy_top = 485
    # Stone lower wainscot
    d.rectangle([wx0, gy - 65, wx1, gy], fill=hex_to_rgba("#718096"), outline=OUTLINE, width=3)
    # Timber & plaster workshop walls
    d.rectangle([wx0, wy_top, wx1, gy - 65], fill=hex_to_rgba("#D6B36A"), outline=OUTLINE, width=3)
    # Dark red/brown timber pillars
    for px in [wx0 + 8, wx0 + 72, wx1 - 16]:
        d.rectangle([px, wy_top, px + 10, gy - 65], fill=hex_to_rgba("#8C6D46"), outline=OUTLINE, width=2)
    # Lattice window
    d.rectangle([wx0 + 26, wy_top + 48, wx0 + 64, wy_top + 115], fill=hex_to_rgba("#2D3748"), outline=OUTLINE, width=2)
    d.line([(wx0 + 45, wy_top + 48), (wx0 + 45, wy_top + 115)], fill=hex_to_rgba("#8C6D46"), width=2)
    d.line([(wx0 + 26, wy_top + 81), (wx0 + 64, wy_top + 81)], fill=hex_to_rgba("#8C6D46"), width=2)
    # Blue-gray Ming tiled roof over workshop
    draw_ming_tiled_roof(d, wx0 - 16, wx1 + 16, wy_top, wy_top - 72)

    # Save @2x (520x760) and 1x (260x380)
    im.save(os.path.join(b_dir, "b04_inner_water_gate@2x.png"), "PNG")
    im_1x = im.resize((260, 380), Image.Resampling.LANCZOS)
    im_1x.save(os.path.join(b_dir, "b04_inner_water_gate.png"), "PNG")
    print("Redrew b04_inner_water_gate.png (260x380) & @2x")

# -------------------------------------------------------------
# 2. 重绘 B07 敌台箭楼 (112x210 & lv2 144x240)
# -------------------------------------------------------------
def redraw_arrow_tower():
    b_dir = os.path.join(ASSETS_DIR, "buildings")
    # Render at 2x (224x420) -> downsample to 112x210
    w, h = 224, 420
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    gy = 414

    # Heavy battered granite stone bastion (y: 196..414)
    draw_stone_courses(d, 22, 196, 202, gy - 14, row_h=24, col_w=42, batter=14)
    d.rectangle([16, gy - 16, 208, gy], fill=hex_to_rgba("#4A5568"), outline=OUTLINE, width=3)
    d.polygon([(36, 196), (188, 196), (202, gy - 16), (22, gy - 16)], outline=OUTLINE, width=3)

    # Lower arched sally port door
    d.pieslice([86, 336, 138, 388], 180, 360, fill=hex_to_rgba("#1A202C"), outline=OUTLINE, width=3)
    d.rectangle([86, 362, 138, gy - 16], fill=hex_to_rgba("#1A202C"), outline=OUTLINE, width=3)

    # Hollow enemy tower arrow/gun embrasures (空心敌台箭窗/铳眼)
    for ex in [62, 104, 146]:
        d.rectangle([ex, 222, ex + 16, 246], fill=hex_to_rgba("#1A202C"), outline=OUTLINE, width=2)
        d.rectangle([ex + 4, 272, ex + 12, 290], fill=hex_to_rgba("#1A202C"), outline=OUTLINE, width=2)

    # Stone parapet & crenellations
    d.rectangle([28, 182, 196, 198], fill=hex_to_rgba("#8A99AD"), outline=OUTLINE, width=3)
    for cx in [34, 76, 126, 168]:
        d.rectangle([cx, 164, cx + 22, 182], fill=hex_to_rgba("#718096"), outline=OUTLINE, width=3)

    # Ming Wooden Watchtower atop bastion (y: 88..166)
    d.rectangle([48, 92, 176, 166], fill=hex_to_rgba("#D6B36A"), outline=OUTLINE, width=3)
    # Red wooden pillars and railing
    for px in [48, 86, 130, 168]:
        d.rectangle([px, 92, px + 8, 166], fill=hex_to_rgba("#9B2C2C"), outline=OUTLINE, width=2)
    d.rectangle([44, 144, 180, 156], fill=hex_to_rgba("#8C6D46"), outline=OUTLINE, width=2)
    # Slit windows
    d.rectangle([64, 108, 80, 134], fill=hex_to_rgba("#1A202C"), outline=OUTLINE, width=2)
    d.rectangle([102, 108, 122, 134], fill=hex_to_rgba("#1A202C"), outline=OUTLINE, width=2)
    d.rectangle([144, 108, 160, 134], fill=hex_to_rgba("#1A202C"), outline=OUTLINE, width=2)

    # Blue-gray tiled Ming roof
    draw_ming_tiled_roof(d, 22, 202, 92, 34)

    im.save(os.path.join(b_dir, "b07_tower_arrow@2x.png"), "PNG")
    im_1x = im.resize((112, 210), Image.Resampling.LANCZOS)
    im_1x.save(os.path.join(b_dir, "b07_tower_arrow.png"), "PNG")
    print("Redrew b07_tower_arrow.png (112x210) & @2x")

    # Lv2 Arrow Tower (144x240) - taller, double-tiered banner + gold trim
    im_lv2 = Image.new("RGBA", (288, 480), (0, 0, 0, 0))
    # Paste Lv1 centered at bottom, then add red Ming defense banner & second eave trim
    im_lv2.paste(im, (32, 60), im)
    dl = ImageDraw.Draw(im_lv2)
    # Banner pole on roof
    dl.line([(144, 12), (144, 94)], fill=hex_to_rgba("#8C6D46"), width=4)
    dl.polygon([(144, 16), (206, 28), (194, 48), (144, 52)], fill=hex_to_rgba("#9B2C2C"), outline=OUTLINE, width=3)
    dl.line([(96, 152), (192, 152)], fill=hex_to_rgba("#F6E05E"), width=3)
    im_lv2.resize((144, 240), Image.Resampling.LANCZOS).save(os.path.join(b_dir, "b07_tower_arrow_lv2.png"), "PNG")
    print("Redrew b07_tower_arrow_lv2.png (144x240)")

# -------------------------------------------------------------
# 3. 重绘地面 D04 堡内青石板路 & D05 城外海涂 (640x160 无缝平铺)
# -------------------------------------------------------------
def redraw_grounds():
    bg_dir = os.path.join(ASSETS_DIR, "bg")

    # D04: 永昌堡内青石板路 + 夯土剖面 (640x160)
    im = Image.new("RGBA", (640, 160), hex_to_rgba("#3B3026"))
    d = ImageDraw.Draw(im)
    # Top 48px: 青灰色温州青石板路 (seamless 640px)
    d.rectangle([0, 0, 640, 48], fill=hex_to_rgba("#718096"))
    stone_tones = ["#718096", "#64748B", "#7A899F", "#5A6772"]
    # Two rows of staggered flagstones (y: 0..24, 24..48)
    for row, (ry0, ry1, w_unit, off) in enumerate([(0, 24, 80, 0), (24, 48, 80, 40)]):
        for i in range(-1, 9):
            x0 = i * w_unit + off
            x1 = x0 + w_unit
            c = hex_to_rgba(stone_tones[(i + row * 2) % len(stone_tones)])
            d.rectangle([x0, ry0, x1, ry1], fill=c)
            # Top-left bright bevel
            d.line([(x0 + 1, ry0 + 1), (x1 - 1, ry0 + 1)], fill=hex_to_rgba("#A0AEC0", 160), width=2)
            # Clean stone joint
            d.rectangle([x0, ry0, x1, ry1], outline=OUTLINE, width=2)
    # Curb edge separating flagstone street and rammed earth
    d.rectangle([0, 46, 640, 54], fill=hex_to_rgba("#4A5568"), outline=OUTLINE, width=2)

    # Lower 54..160px: clean Ming rammed-earth strata (no noisy speckles!)
    d.rectangle([0, 54, 640, 96], fill=hex_to_rgba("#3B3026"))
    d.rectangle([0, 96, 640, 160], fill=hex_to_rgba("#2D241C"))
    # Subtle horizontal strata bands
    d.line([(0, 74), (640, 74)], fill=hex_to_rgba("#4A3D31"), width=2)
    d.line([(0, 96), (640, 96)], fill=hex_to_rgba("#1A202C"), width=2)
    d.line([(0, 128), (640, 128)], fill=hex_to_rgba("#3B3026"), width=2)
    # Embedded foundation stones in earth strata (seamless)
    for sx, sy, sw, sh in [(48, 66, 36, 18), (190, 108, 44, 20), (360, 68, 32, 16), (510, 104, 40, 20)]:
        d.rounded_rectangle([sx, sy, sx + sw, sy + sh], radius=3, fill=hex_to_rgba("#5A6772"), outline=OUTLINE, width=2)
    im.save(os.path.join(bg_dir, "d04_ground_fortress.png"), "PNG")
    print("Redrew bg/d04_ground_fortress.png (640x160)")

    # D05: 城外海涂泥沙 + 芦苇 (640x160, 干净硬边扁平风格，无高斯模糊!)
    im_b = Image.new("RGBA", (640, 160), hex_to_rgba("#B79F78"))
    db = ImageDraw.Draw(im_b)
    # Top sand crust (y: 0..48)
    db.rectangle([0, 0, 640, 48], fill=hex_to_rgba("#B79F78"))
    # Tidal puddles & sand ripples (crisp flat shapes)
    for px in [40, 220, 430]:
        db.rounded_rectangle([px, 18, px + 110, 34], radius=6, fill=hex_to_rgba("#9C825E"), outline=hex_to_rgba("#7A5C3E"), width=1)
        db.line([(px + 12, 26), (px + 86, 26)], fill=hex_to_rgba("#5A6772", 180), width=2)
    # Lower mud strata (y: 48..160)
    db.line([(0, 48), (640, 48)], fill=OUTLINE, width=2)
    db.rectangle([0, 49, 640, 100], fill=hex_to_rgba("#9C825E"))
    db.rectangle([0, 100, 640, 160], fill=hex_to_rgba("#7A5C3E"))
    db.line([(0, 100), (640, 100)], fill=hex_to_rgba("#5E462E"), width=2)
    # Crisp pebbles & coastal reed tufts along top edge
    for rx in [20, 150, 310, 490]:
        db.line([(rx, 16), (rx - 6, 2)], fill=hex_to_rgba("#48BB78"), width=2)
        db.line([(rx + 2, 16), (rx + 4, 0)], fill=hex_to_rgba("#68A357"), width=2)
        db.line([(rx + 5, 16), (rx + 11, 4)], fill=hex_to_rgba("#48BB78"), width=2)
    for px, py in [(95, 68), (280, 80), (410, 64), (570, 76)]:
        db.ellipse([px, py, px + 16, py + 10], fill=hex_to_rgba("#718096"), outline=OUTLINE, width=1)
    im_b.save(os.path.join(bg_dir, "d05_ground_beach.png"), "PNG")
    print("Redrew bg/d05_ground_beach.png (640x160)")

# -------------------------------------------------------------
# 4. 重绘背景层：天空、大罗山、中景永昌水乡民居
# -------------------------------------------------------------
def draw_flat_guofeng_cloud(d, cx, cy, w, h, main_c, shade_c):
    """Crisp layered flat guofeng cloud (zero gaussian blur)."""
    r = h // 2
    d.rounded_rectangle([cx, cy, cx + w, cy + h], radius=r, fill=main_c)
    d.rounded_rectangle([cx + w * 0.18, cy - h * 0.45, cx + w * 0.72, cy + h * 0.6], radius=r, fill=main_c)
    d.rounded_rectangle([cx + 4, cy + h * 0.55, cx + w - 4, cy + h], radius=r // 2, fill=shade_c)

def redraw_skies_and_parallax():
    bg_dir = os.path.join(ASSETS_DIR, "bg")

    # D01 白昼天空 (1280x720)
    arr = np.zeros((720, 1280, 4), dtype=np.uint8)
    for y in range(720):
        t = y / 719.0
        r = int(74 + (216 - 74) * t)
        g = int(111 + (228 - 111) * t)
        b = int(165 + (240 - 165) * t)
        arr[y, :] = [r, g, b, 255]
    im_day = Image.fromarray(arr)
    dd = ImageDraw.Draw(im_day)
    draw_flat_guofeng_cloud(dd, 120, 150, 220, 36, hex_to_rgba("#E2E8F0", 160), hex_to_rgba("#CBD5E0", 140))
    draw_flat_guofeng_cloud(dd, 560, 110, 280, 42, hex_to_rgba("#E2E8F0", 150), hex_to_rgba("#CBD5E0", 130))
    draw_flat_guofeng_cloud(dd, 980, 180, 200, 32, hex_to_rgba("#E2E8F0", 140), hex_to_rgba("#CBD5E0", 120))
    im_day.save(os.path.join(bg_dir, "d01_sky_day.png"), "PNG")

    # D02 黄昏天空 (1280x720)
    arr = np.zeros((720, 1280, 4), dtype=np.uint8)
    for y in range(720):
        t = y / 719.0
        if t < 0.55:
            k = t / 0.55
            r = int(92 + (192 - 92) * k)
            g = int(75 + (92 - 75) * k)
            b = int(78 + (48 - 78) * k)
        else:
            k = (t - 0.55) / 0.45
            r = int(192 + (246 - 192) * k)
            g = int(92 + (173 - 92) * k)
            b = int(48 + (85 - 48) * k)
        arr[y, :] = [r, g, b, 255]
    im_dusk = Image.fromarray(arr)
    dsk = ImageDraw.Draw(im_dusk)
    draw_flat_guofeng_cloud(dsk, 180, 190, 260, 36, hex_to_rgba("#FBD38D", 130), hex_to_rgba("#DD6B20", 120))
    draw_flat_guofeng_cloud(dsk, 760, 140, 300, 40, hex_to_rgba("#FBD38D", 120), hex_to_rgba("#C05621", 110))
    im_dusk.save(os.path.join(bg_dir, "d02_sky_dusk.png"), "PNG")

    # D03 黑夜天空 (1280x720)
    arr = np.zeros((720, 1280, 4), dtype=np.uint8)
    for y in range(720):
        t = y / 719.0
        r = int(16 + (11 - 16) * t)
        g = int(24 + (20 - 24) * t)
        b = int(41 + (38 - 41) * t)
        arr[y, :] = [r, g, b, 255]
    im_night = Image.fromarray(arr)
    dn = ImageDraw.Draw(im_night)
    np.random.seed(1558)
    for _ in range(90):
        sx, sy = int(np.random.uniform(20, 1260)), int(np.random.uniform(20, 360))
        dn.rectangle([sx, sy, sx + 2, sy + 2], fill=(226, 232, 240, int(np.random.uniform(90, 210))))
    draw_flat_guofeng_cloud(dn, 220, 170, 240, 32, hex_to_rgba("#1A2639", 180), hex_to_rgba("#101829", 190))
    draw_flat_guofeng_cloud(dn, 820, 130, 260, 34, hex_to_rgba("#1A2639", 170), hex_to_rgba("#101829", 180))
    im_night.save(os.path.join(bg_dir, "d03_sky_night.png"), "PNG")
    print("Redrew d01_sky_day, d02_sky_dusk, d03_sky_night")

    # A3: b09_daluo_mountain.png (320x760, 温州大罗山连绵剪影，左高右低)
    im_m = Image.new("RGBA", (320, 760), (0, 0, 0, 0))
    dm = ImageDraw.Draw(im_m)
    # Far misty peak ridge
    dm.polygon([(0, 760), (0, 250), (42, 200), (95, 240), (150, 290), (210, 355), (275, 420), (320, 490), (320, 760)],
               fill=hex_to_rgba("#3B4A59", 180))
    # Main Daluo mountain ridge (#2C3E50) with faceted guofeng stone ridge
    dm.polygon([(0, 760), (0, 130), (36, 85), (72, 160), (118, 195), (165, 270), (225, 340), (285, 425), (320, 480), (320, 760)],
               fill=hex_to_rgba("#2C3E50", 255))
    # Subtle lighter left-facing mountain facet (upper-left light!)
    dm.polygon([(0, 130), (36, 85), (42, 340), (0, 400)], fill=hex_to_rgba("#364B61", 255))
    dm.polygon([(118, 195), (132, 360), (96, 380), (72, 160)], fill=hex_to_rgba("#364B61", 180))
    im_m.save(os.path.join(bg_dir, "b09_daluo_mountain.png"), "PNG")
    print("Redrew bg/b09_daluo_mountain.png (320x760)")

    # C1: d08_mid_houses.png (1280x160, 永昌堡内浙南水乡马头墙古民居剪影，横向无缝平铺)
    im_h = Image.new("RGBA", (1280, 160), (0, 0, 0, 0))
    dh = ImageDraw.Draw(im_h)
    c_dark = hex_to_rgba("#2D3748")
    c_mid = hex_to_rgba("#3B4A59")
    c_roof = hex_to_rgba("#1A202C")
    for x0 in range(0, 1280, 320):
        # 1. Stepped Horsehead gable mansion (马头墙)
        dh.rectangle([x0 + 14, 72, x0 + 116, 160], fill=c_mid, outline=OUTLINE, width=1)
        # Stepped white-gray gable caps
        for step, (sx, sy) in enumerate([(10, 48), (24, 58), (104, 58), (116, 48)]):
            dh.rectangle([x0 + sx, sy, x0 + sx + 12, 160], fill=c_dark)
        dh.polygon([(x0 + 16, 72), (x0 + 114, 72), (x0 + 65, 42)], fill=c_roof)
        # 2. Stone arch bridge silhouette over inner canal
        dh.rectangle([x0 + 122, 126, x0 + 186, 160], fill=c_dark)
        dh.pieslice([x0 + 136, 134, x0 + 172, 166], 180, 360, fill=(0, 0, 0, 0))
        # 3. Traditional pitched-roof riverfront houses
        dh.rectangle([x0 + 190, 84, x0 + 260, 160], fill=c_dark, outline=OUTLINE, width=1)
        dh.polygon([(x0 + 182, 84), (x0 + 268, 84), (x0 + 252, 56), (x0 + 198, 56)], fill=c_roof)
        dh.rectangle([x0 + 264, 68, x0 + 314, 160], fill=c_mid, outline=OUTLINE, width=1)
        dh.polygon([(x0 + 258, 68), (x0 + 320, 68), (x0 + 289, 44)], fill=c_roof)
    im_h.save(os.path.join(bg_dir, "d08_mid_houses.png"), "PNG")
    print("Redrew bg/d08_mid_houses.png (1280x160)")

# -------------------------------------------------------------
# 5. 重绘 B1/B2 破损水门 & 全景封面/胜利/失败背景 (1280x720)
# -------------------------------------------------------------
def add_clean_damage(im_in, cracks=6, scorch_spots=5):
    im = ImageEnhance.Brightness(im_in.copy().convert("RGBA")).enhance(0.84)
    arr = np.array(im)
    alpha = arr[:, :, 3]
    non_y, non_x = np.where(alpha > 128)
    if len(non_x) == 0:
        return im
    min_x, max_x = int(np.min(non_x)), int(np.max(non_x))
    min_y, max_y = int(np.min(non_y)), int(np.max(non_y))

    np.random.seed(1558)
    crack_layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dc = ImageDraw.Draw(crack_layer)
    for _ in range(cracks):
        cx = int(np.random.uniform(min_x + (max_x - min_x)*0.15, max_x - (max_x - min_x)*0.15))
        cy = int(np.random.uniform(min_y + (max_y - min_y)*0.25, max_y - (max_y - min_y)*0.15))
        pts = [(cx, cy)]
        for _ in range(4):
            cx += int(np.random.uniform(-12, 12))
            cy += int(np.random.uniform(8, 18))
            pts.append((cx, cy))
        dc.line(pts, fill=hex_to_rgba("#1A202C", 220), width=2)
    c_arr = np.array(crack_layer)
    c_arr[:, :, 3] = np.minimum(c_arr[:, :, 3], alpha)
    im = Image.alpha_composite(im, Image.fromarray(c_arr))

    scorch = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(scorch)
    for _ in range(scorch_spots):
        sx = int(np.random.uniform(min_x + 20, max_x - 20))
        sy = int(np.random.uniform(min_y + 30, max_y - 20))
        sr = int(np.random.uniform(14, 28))
        ds.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(20, 18, 18, 120))
    scorch = scorch.filter(ImageFilter.GaussianBlur(7))
    s_arr = np.array(scorch)
    s_arr[:, :, 3] = np.minimum(s_arr[:, :, 3], alpha)
    return Image.alpha_composite(im, Image.fromarray(s_arr))

def redraw_panoramas():
    bg_dir = os.path.join(ASSETS_DIR, "bg")
    b_dir = os.path.join(ASSETS_DIR, "buildings")
    props_dir = os.path.join(ASSETS_DIR, "sprites", "props")

    # Update broken water gate to match new b04
    wg = Image.open(os.path.join(b_dir, "b04_inner_water_gate.png"))
    add_clean_damage(wg, cracks=6, scorch_spots=5).save(os.path.join(b_dir, "b04_inner_water_gate_broken.png"), "PNG")
    print("Updated b04_inner_water_gate_broken.png")

    def compose_panorama(sky_name, broken=False, is_night=False):
        canvas = Image.open(os.path.join(bg_dir, sky_name)).convert("RGBA").resize((1280, 720))
        d = ImageDraw.Draw(canvas)
        if is_night:
            # Crescent moon
            d.ellipse([1050, 75, 1118, 143], fill=hex_to_rgba("#FEFCBF", 220))
            d.ellipse([1066, 67, 1134, 135], fill=hex_to_rgba("#101829", 255))
        elif sky_name == "d01_sky_day.png":
            # Morning sun
            d.ellipse([960, 150, 1100, 290], fill=hex_to_rgba("#F6E05E", 210))

        # Far Daluo Mountain on left
        mtn = Image.open(os.path.join(bg_dir, "b09_daluo_mountain.png")).convert("RGBA").resize((520, 480))
        if is_night:
            mtn = ImageEnhance.Brightness(mtn).enhance(0.6)
        canvas.alpha_composite(mtn, (0, 560 - mtn.height))

        # Midground houses inside fortress
        houses = Image.open(os.path.join(bg_dir, "d08_mid_houses.png")).convert("RGBA")
        if is_night:
            houses = ImageEnhance.Brightness(houses).enhance(0.65)
        canvas.alpha_composite(houses.crop((0, 0, 760, 160)), (0, 560 - 160))

        # East China Sea on right
        d.rectangle([760, 560, 1280, 720], fill=hex_to_rgba("#1E4E79" if not is_night else "#0F2942"))
        # Fortress ground on left
        ground = Image.open(os.path.join(bg_dir, "d04_ground_fortress.png")).convert("RGBA")
        if is_night:
            ground = ImageEnhance.Brightness(ground).enhance(0.55)
        canvas.alpha_composite(ground, (0, 560))
        canvas.alpha_composite(ground.crop((0, 0, 140, 160)), (640, 560))

        # Beach ground + Coastline transition at x=780
        beach = Image.open(os.path.join(bg_dir, "d05_ground_beach.png")).convert("RGBA")
        if is_night:
            beach = ImageEnhance.Brightness(beach).enhance(0.55)
        canvas.alpha_composite(beach.crop((0, 0, 220, 160)), (780, 560))
        coast = Image.open(os.path.join(bg_dir, "b11_coast.png")).convert("RGBA")
        if is_night:
            coast = ImageEnhance.Brightness(coast).enhance(0.6)
        canvas.alpha_composite(coast, (760, 560 - coast.height + 48))

        # Real Yongchang Fortress line-up: Main Wall + Arrow Tower + East Gate Barbican
        wall = Image.open(os.path.join(b_dir, "b05_main_wall.png")).convert("RGBA").resize((240, 214))
        tower = Image.open(os.path.join(b_dir, "b07_tower_arrow.png")).convert("RGBA")
        gate_file = "b06_east_gate_broken.png" if broken else "b06_east_gate_barbican.png"
        gate = Image.open(os.path.join(b_dir, gate_file)).convert("RGBA")
        if is_night:
            wall = ImageEnhance.Brightness(wall).enhance(0.6)
            tower = ImageEnhance.Brightness(tower).enhance(0.6)
            gate = ImageEnhance.Brightness(gate).enhance(0.65)

        canvas.alpha_composite(wall, (120, 560 - wall.height))
        canvas.alpha_composite(wall, (356, 560 - wall.height))
        canvas.alpha_composite(tower, (310, 560 - tower.height))
        canvas.alpha_composite(gate, (540, 560 - gate.height))

        if is_night:
            glow = Image.open(os.path.join(props_dir, "fx_torch_glow.png")).convert("RGBA")
            for tx, ty in [(635, 420), (725, 420), (366, 440)]:
                canvas.alpha_composite(glow, (tx - 64, ty - 64))
        return canvas

    compose_panorama("d03_sky_night.png", broken=False, is_night=True).save(os.path.join(bg_dir, "d09_title_bg.png"), "PNG")
    compose_panorama("d01_sky_day.png", broken=False, is_night=False).save(os.path.join(bg_dir, "d10_victory.png"), "PNG")
    compose_panorama("d02_sky_dusk.png", broken=True, is_night=False).save(os.path.join(bg_dir, "d11_defeat.png"), "PNG")
    print("Redrew d09_title_bg.png, d10_victory.png, d11_defeat.png")

if __name__ == "__main__":
    redraw_water_gate()
    redraw_arrow_tower()
    redraw_grounds()
    redraw_skies_and_parallax()
    redraw_panoramas()
    print("ALL YONGCHANG ASSETS REDRAWN SUCCESSFULLY!")
