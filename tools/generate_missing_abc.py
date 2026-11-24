import os
import math
import shutil
from collections import deque
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np

ASSETS_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\assets"
BRAIN_DIR = r"C:\Users\jakfc\.gemini\antigravity-cli\brain\384857b6-a774-4e45-a487-fa6fafddb5e9"

def hex_to_rgba(hex_code, alpha=255):
    h = hex_code.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)

def remove_white_bg_floodfill(img, threshold=232):
    arr = np.array(img.convert("RGBA"))
    h, w = arr.shape[:2]
    visited = np.zeros((h, w), dtype=bool)
    queue = deque()
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

def fit_bottom_center(img, target_size, pad_x=8, pad_bottom=0, pad_top=8):
    bbox = img.getbbox()
    if not bbox:
        raise ValueError("Empty image")
    cropped = img.crop(bbox)
    tw, th = target_size
    avail_w = tw - pad_x * 2
    avail_h = th - pad_bottom - pad_top
    scale = min(avail_w / cropped.width, avail_h / cropped.height)
    nw = max(1, int(round(cropped.width * scale)))
    nh = max(1, int(round(cropped.height * scale)))
    resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    px = (tw - nw) // 2
    py = th - pad_bottom - nh
    canvas.paste(resized, (px, py), resized)
    return canvas

# -------------------------------------------------------------
# A1 & A2: Process Nano Banana generated buildings
# -------------------------------------------------------------
def process_nanobanana_buildings():
    jobs = [
        ("b03_salt_office_1795503201798.jpg", "buildings/b03_salt_office.png", (340, 300)),
        ("b05_main_wall_1795503181941.jpg", "buildings/b05_main_wall.png", (360, 320)),
    ]
    for src_name, dst_rel, size in jobs:
        src_path = os.path.join(BRAIN_DIR, src_name)
        dst_path = os.path.join(ASSETS_DIR, dst_rel)
        im = remove_white_bg_floodfill(Image.open(src_path))
        out_1x = fit_bottom_center(im, size, pad_x=6, pad_bottom=0, pad_top=6)
        out_2x = fit_bottom_center(im, (size[0]*2, size[1]*2), pad_x=12, pad_bottom=0, pad_top=12)
        out_1x.save(dst_path, "PNG")
        out_2x.save(dst_path.replace(".png", "@2x.png"), "PNG")
        print(f"Processed Nano Banana building -> {dst_rel} ({size[0]}x{size[1]})")

# -------------------------------------------------------------
# A3, A4, A5: Daluo Mountain, Outer Salt Flat, Coast
# -------------------------------------------------------------
def generate_a3_a4_a5():
    bg_dir = os.path.join(ASSETS_DIR, "bg")
    outline = hex_to_rgba("#1A202C")

    # A3: b09_daluo_mountain.png (320x760, 纯剪影 #2C3E50, 左高右低连绵, 底边贴地)
    im = Image.new("RGBA", (320, 760), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Far misty ridge (#2F4F4F at 75% alpha)
    far_poly = [(0, 760), (0, 260), (45, 210), (95, 250), (160, 310), (235, 360), (320, 410), (320, 760)]
    d.polygon(far_poly, fill=hex_to_rgba("#2F4F4F", 190))
    # Main Daluo mountain silhouette (#2C3E50, left high -> right low)
    main_poly = [(0, 760), (0, 140), (38, 90), (78, 175), (125, 220), (175, 295), (245, 355), (320, 440), (320, 760)]
    d.polygon(main_poly, fill=hex_to_rgba("#2C3E50", 255))
    # Subtle soft mist gradient near bottom 120px
    arr = np.array(im)
    for y in range(640, 760):
        t = (y - 640) / 120.0
        # keep solid at bottom or slight atmospheric fade? Spec says 底边贴地，纯剪影 #2C3E50
        pass
    im.save(os.path.join(bg_dir, "b09_daluo_mountain.png"), "PNG")
    print("Generated bg/b09_daluo_mountain.png (320x760)")

    # A4: b10_outer_salt_flat.png (1120x120, 横向可平铺, 白盐堆 + 浅水格田, 底边贴地)
    im = Image.new("RGBA", (1120, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Mudflat base
    d.rectangle([0, 56, 1120, 120], fill=hex_to_rgba("#B79F78"), outline=None)
    d.line([(0, 56), (1120, 56)], fill=outline, width=2)
    # Shallow rectangular salt evaporation pans (seamless every 280px)
    pan_water = hex_to_rgba("#5A6772")
    pan_rim = hex_to_rgba("#9C825E")
    salt_white = hex_to_rgba("#E2E8F0")
    salt_shade = hex_to_rgba("#CBD5E0")
    for x0 in range(0, 1120, 280):
        # Salt pan rectangle
        d.polygon([(x0+18, 66), (x0+190, 66), (x0+205, 108), (x0+8, 108)], fill=pan_water, outline=outline, width=2)
        d.line([(x0+26, 76), (x0+180, 76)], fill=hex_to_rgba("#718096"), width=2)
        # Raised bund
        d.rectangle([x0+198, 60, x0+214, 112], fill=pan_rim, outline=outline, width=1)
        # White salt mounds
        d.polygon([(x0+215, 66), (x0+245, 34), (x0+272, 66)], fill=salt_white, outline=outline, width=2)
        d.polygon([(x0+245, 34), (x0+272, 66), (x0+245, 66)], fill=salt_shade)
    im.save(os.path.join(bg_dir, "b10_outer_salt_flat.png"), "PNG")
    print("Generated bg/b10_outer_salt_flat.png (1120x120)")

    # A5: b11_coast.png (520x160, 底边贴地, 沙 + 礁石 + 浪花, 右侧接海面)
    im = Image.new("RGBA", (520, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Sea on right half (#1E4E79)
    d.polygon([(210, 92), (520, 92), (520, 160), (140, 160)], fill=hex_to_rgba("#1E4E79"), outline=outline, width=2)
    # Sandy beach slope on left (#B79F78)
    d.polygon([(0, 82), (240, 96), (310, 130), (220, 160), (0, 160)], fill=hex_to_rgba("#B79F78"), outline=outline, width=2)
    # Coastal rocks
    rock_c = hex_to_rgba("#4A5568")
    rock_hi = hex_to_rgba("#718096")
    d.polygon([(110, 105), (140, 72), (185, 78), (205, 112)], fill=rock_c, outline=outline, width=2)
    d.polygon([(140, 72), (165, 75), (155, 105), (110, 105)], fill=rock_hi)
    d.polygon([(235, 118), (262, 92), (295, 102), (305, 126)], fill=rock_c, outline=outline, width=2)
    # Stylized guofeng white sea-foam waves
    foam = hex_to_rgba("#E2E8F0")
    for wx in [250, 340, 430]:
        d.arc([wx, 92, wx+70, 112], start=190, end=350, fill=foam, width=3)
        d.arc([wx+20, 118, wx+80, 134], start=190, end=350, fill=hex_to_rgba("#CBD5E0"), width=2)
    im.save(os.path.join(bg_dir, "b11_coast.png"), "PNG")
    print("Generated bg/b11_coast.png (520x160)")

# -------------------------------------------------------------
# B1-B6: Status variants, upgraded towers, UI bars, 24x24 icons
# -------------------------------------------------------------
def add_damage_overlay(base_img, cracks=6, scorch_spots=4, chip_top=True):
    """Derive a damaged state sprite from an intact building sprite with identical silhouette alignment."""
    im = base_img.copy().convert("RGBA")
    arr = np.array(im)
    h, w = arr.shape[:2]
    alpha = arr[:, :, 3]

    # Slightly darken/desaturate overall tone
    enhancer = ImageEnhance.Brightness(im)
    im = enhancer.enhance(0.86)
    d = ImageDraw.Draw(im)

    np.random.seed(1558)
    non_empty_y, non_empty_x = np.where(alpha > 128)
    if len(non_empty_x) == 0:
        return im
    min_x, max_x = int(np.min(non_empty_x)), int(np.max(non_empty_x))
    min_y, max_y = int(np.min(non_empty_y)), int(np.max(non_empty_y))

    # Add jagged cracks strictly masked inside building alpha
    crack_layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dc_crack = ImageDraw.Draw(crack_layer)
    outline = hex_to_rgba("#1A202C", 230)
    for _ in range(cracks):
        cx = int(np.random.uniform(min_x + (max_x-min_x)*0.15, max_x - (max_x-min_x)*0.15))
        cy = int(np.random.uniform(min_y + (max_y-min_y)*0.28, max_y - (max_y-min_y)*0.15))
        pts = [(cx, cy)]
        for _ in range(4):
            cx += int(np.random.uniform(-14, 14))
            cy += int(np.random.uniform(8, 20))
            pts.append((cx, cy))
        dc_crack.line(pts, fill=outline, width=2)
    c_arr = np.array(crack_layer)
    c_arr[:, :, 3] = np.minimum(c_arr[:, :, 3], alpha)
    im = Image.alpha_composite(im, Image.fromarray(c_arr))

    # Add scorch smoke blotches strictly masked inside building alpha
    scorch = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(scorch)
    for _ in range(scorch_spots):
        sx = int(np.random.uniform(min_x + 20, max_x - 20))
        sy = int(np.random.uniform(min_y + 30, max_y - 20))
        sr = int(np.random.uniform(16, 34))
        ds.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], fill=(20, 18, 18, 130))
    scorch = scorch.filter(ImageFilter.GaussianBlur(8))
    s_arr = np.array(scorch)
    s_arr[:, :, 3] = np.minimum(s_arr[:, :, 3], alpha)
    im = Image.alpha_composite(im, Image.fromarray(s_arr))
    return im

def generate_b_group():
    b_dir = os.path.join(ASSETS_DIR, "buildings")
    ui_dir = os.path.join(ASSETS_DIR, "ui")
    icons_dir = os.path.join(ui_dir, "icons")
    tools_dir = os.path.join(ASSETS_DIR, "sprites", "tools")
    outline = hex_to_rgba("#1A202C")

    # B1: b06_east_gate_broken.png (280x440)
    east_ok = Image.open(os.path.join(b_dir, "b06_east_gate_barbican.png"))
    east_broken = add_damage_overlay(east_ok, cracks=8, scorch_spots=6, chip_top=True)
    east_broken.save(os.path.join(b_dir, "b06_east_gate_broken.png"), "PNG")
    print("Generated buildings/b06_east_gate_broken.png")

    # B2: b04_inner_water_gate_broken.png (260x380)
    wgate_ok = Image.open(os.path.join(b_dir, "b04_inner_water_gate.png"))
    wgate_broken = add_damage_overlay(wgate_ok, cracks=6, scorch_spots=5, chip_top=True)
    wgate_broken.save(os.path.join(b_dir, "b04_inner_water_gate_broken.png"), "PNG")
    print("Generated buildings/b04_inner_water_gate_broken.png")

    # B3: b01_shrine_lv2.png (360x360) - Upgraded with gold ornaments, red banners, lanterns
    shrine = Image.open(os.path.join(b_dir, "b01_shrine.png")).convert("RGBA")
    d = ImageDraw.Draw(shrine)
    gold = hex_to_rgba("#F6E05E")
    crimson = hex_to_rgba("#9B2C2C")
    # Flanking red banners on stone terrace
    for bx in [36, 314]:
        d.line([(bx, 180), (bx, 340)], fill=hex_to_rgba("#8C6D46"), width=3)
        d.polygon([(bx, 185), (bx+16, 195), (bx+16, 265), (bx, 275)], fill=crimson, outline=outline, width=2)
    # Warm glowing lanterns under eaves
    for lx in [105, 255]:
        d.ellipse([lx-7, 235, lx+7, 253], fill=hex_to_rgba("#F6AD55"), outline=outline, width=2)
        d.ellipse([lx-3, 240, lx+3, 248], fill=hex_to_rgba("#FEFCBF"))
    # Gold ridge trim
    d.line([(85, 162), (275, 162)], fill=gold, width=3)
    shrine.save(os.path.join(b_dir, "b01_shrine_lv2.png"), "PNG")
    print("Generated buildings/b01_shrine_lv2.png")

    # B4: b07_tower_arrow_lv2.png & b08_tower_cannon_lv2.png (design width 72 -> 144x240)
    arrow_lv1 = Image.open(os.path.join(b_dir, "b07_tower_arrow.png")).convert("RGBA")
    arrow_lv2 = fit_bottom_center(arrow_lv1, (144, 240), pad_x=12, pad_bottom=0, pad_top=36)
    da = ImageDraw.Draw(arrow_lv2)
    # Ming red banner on top + gold trim
    da.line([(72, 6), (72, 52)], fill=hex_to_rgba("#8C6D46"), width=3)
    da.polygon([(72, 8), (112, 16), (104, 28), (72, 30)], fill=hex_to_rgba("#C53030"), outline=outline, width=2)
    da.line([(34, 134), (110, 134)], fill=hex_to_rgba("#F6E05E"), width=3)
    arrow_lv2.save(os.path.join(b_dir, "b07_tower_arrow_lv2.png"), "PNG")

    cannon_lv1 = Image.open(os.path.join(b_dir, "b08_tower_cannon.png")).convert("RGBA")
    cannon_lv2 = fit_bottom_center(cannon_lv1, (144, 240), pad_x=10, pad_bottom=0, pad_top=44)
    dc = ImageDraw.Draw(cannon_lv2)
    dc.line([(54, 16), (54, 68)], fill=hex_to_rgba("#8C6D46"), width=3)
    dc.polygon([(54, 18), (94, 26), (86, 38), (54, 40)], fill=hex_to_rgba("#D97706"), outline=outline, width=2)
    # Heavy reinforced brass ring on cannon
    dc.rectangle([72, 92, 126, 102], fill=hex_to_rgba("#2D3748"), outline=outline, width=2)
    dc.rectangle([86, 90, 92, 104], fill=hex_to_rgba("#F6E05E"), outline=outline, width=1)
    cannon_lv2.save(os.path.join(b_dir, "b08_tower_cannon_lv2.png"), "PNG")
    print("Generated buildings/b07_tower_arrow_lv2.png & b08_tower_cannon_lv2.png")

    # B5: e10_bar_empty.png & e08_bar_stamina.png (128x16 = design 64x8 * 2)
    im_empty = Image.new("RGBA", (128, 16), (0, 0, 0, 0))
    de = ImageDraw.Draw(im_empty)
    de.rounded_rectangle([0, 0, 127, 15], radius=3, fill=hex_to_rgba("#1A202C", 230), outline=hex_to_rgba("#4A5568"), width=2)
    im_empty.save(os.path.join(ui_dir, "e10_bar_empty.png"), "PNG")

    im_stam = Image.new("RGBA", (128, 16), (0, 0, 0, 0))
    ds = ImageDraw.Draw(im_stam)
    ds.rounded_rectangle([0, 0, 127, 15], radius=3, fill=hex_to_rgba("#1A202C"), outline=outline, width=1)
    ds.rounded_rectangle([2, 2, 125, 13], radius=2, fill=hex_to_rgba("#63B3ED"))
    ds.line([(4, 4), (123, 4)], fill=(255, 255, 255, 90), width=2)
    im_stam.save(os.path.join(ui_dir, "e08_bar_stamina.png"), "PNG")
    print("Generated ui/e10_bar_empty.png & updated ui/e08_bar_stamina.png (128x16)")

    # B6: Tool button icons (48x48 = design 24x24 * 2) from 2dflat tools
    for tname in ["hoe", "spear", "hammer", "shovel", "manual"]:
        src_t = os.path.join(tools_dir, f"tool_{tname}.png")
        dst_t = os.path.join(icons_dir, f"icon_tool_{tname}.png")
        if os.path.exists(src_t):
            tim = Image.open(src_t).convert("RGBA").resize((48, 48), Image.Resampling.LANCZOS)
            tim.save(dst_t, "PNG")
            print(f"Generated ui/icons/icon_tool_{tname}.png (48x48)")

# -------------------------------------------------------------
# C1-C6: Mid houses, Title BG, Victory/Defeat BG, Boss Bar, VFX
# -------------------------------------------------------------
def generate_c_group():
    bg_dir = os.path.join(ASSETS_DIR, "bg")
    ui_dir = os.path.join(ASSETS_DIR, "ui")
    props_dir = os.path.join(ASSETS_DIR, "sprites", "props")
    outline = hex_to_rgba("#1A202C")

    # C1: d08_mid_houses.png (1280x160, 中景村舍剪影, 横向可平铺)
    im = Image.new("RGBA", (1280, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c_dark = hex_to_rgba("#2D3748")
    c_light = hex_to_rgba("#3B4A59")
    # Seamless repeating village silhouettes every 320px
    for x0 in range(0, 1280, 320):
        # House 1: Horsehead gable
        d.rectangle([x0+16, 78, x0+110, 160], fill=c_dark)
        d.polygon([(x0+8, 78), (x0+118, 78), (x0+63, 46)], fill=c_light)
        d.rectangle([x0+12, 42, x0+24, 160], fill=c_dark)
        d.rectangle([x0+102, 42, x0+114, 160], fill=c_dark)
        # House 2: Lower cottage
        d.rectangle([x0+145, 96, x0+225, 160], fill=c_light)
        d.polygon([(x0+138, 96), (x0+232, 96), (x0+185, 70)], fill=c_dark)
        # House 3: Taller storehouse
        d.rectangle([x0+240, 64, x0+308, 160], fill=c_dark)
        d.polygon([(x0+234, 64), (x0+314, 64), (x0+274, 38)], fill=c_light)
    im.save(os.path.join(bg_dir, "d08_mid_houses.png"), "PNG")
    print("Generated bg/d08_mid_houses.png (1280x160)")

    # C2: d09_title_bg.png (1280x720, 夜色永昌堡 + 大罗山 + 东海 + 篝火)
    sky_n = Image.new("RGBA", (1280, 720))
    arr_n = np.zeros((720, 1280, 4), dtype=np.uint8)
    for y in range(720):
        t = y / 719.0
        r = int(16 + (11 - 16) * t)
        g = int(24 + (20 - 24) * t)
        b = int(41 + (38 - 41) * t)
        arr_n[y, :] = [r, g, b, 255]
    sky_n = Image.fromarray(arr_n)
    d = ImageDraw.Draw(sky_n)
    # Fine stars + pale crescent moon
    np.random.seed(1558)
    for _ in range(70):
        sx, sy = int(np.random.uniform(20, 1260)), int(np.random.uniform(20, 320))
        d.ellipse([sx, sy, sx+2, sy+2], fill=(226, 232, 240, int(np.random.uniform(100, 210))))
    d.ellipse([1040, 80, 1110, 150], fill=hex_to_rgba("#FEFCBF", 210))
    d.ellipse([1058, 72, 1128, 142], fill=hex_to_rgba("#101829", 255))
    # Distant Daluo mountain left
    d.polygon([(0, 600), (0, 220), (180, 150), (420, 320), (650, 440), (650, 600)], fill=hex_to_rgba("#1E293B"))
    # East China Sea right
    d.rectangle([720, 520, 1280, 720], fill=hex_to_rgba("#1E4E79"))
    # Fortress silhouette mid
    d.rectangle([0, 480, 860, 720], fill=hex_to_rgba("#1A202C"))
    for cx in range(40, 840, 28):
        d.rectangle([cx, 464, cx+16, 480], fill=hex_to_rgba("#1A202C"))
    # Actual East Gate silhouette/night tint
    gate_n = Image.open(os.path.join(ASSETS_DIR, "buildings", "b06_east_gate_barbican.png")).convert("RGBA")
    gate_n = ImageEnhance.Brightness(gate_n).enhance(0.55)
    sky_n.alpha_composite(gate_n, (580, 520 - gate_n.height + 10))
    # Torchlight glows
    glow = Image.open(os.path.join(props_dir, "fx_torch_glow.png")).convert("RGBA")
    for tx, ty in [(660, 390), (775, 390), (420, 465)]:
        sky_n.alpha_composite(glow, (tx-64, ty-64))
    sky_n.save(os.path.join(bg_dir, "d09_title_bg.png"), "PNG")
    print("Generated bg/d09_title_bg.png (1280x720)")

    # C3: d10_victory.png & d11_defeat.png (1280x720)
    sky_d = Image.open(os.path.join(bg_dir, "d01_sky_day.png")).convert("RGBA").resize((1280, 720))
    dv = ImageDraw.Draw(sky_d)
    # Warm morning sun over sea
    dv.ellipse([960, 160, 1140, 340], fill=hex_to_rgba("#F6E05E", 200))
    dv.rectangle([0, 520, 1280, 720], fill=hex_to_rgba("#3B3026"))
    dv.rectangle([780, 520, 1280, 720], fill=hex_to_rgba("#1E4E79"))
    # Intact East Gate
    gate = Image.open(os.path.join(ASSETS_DIR, "buildings", "b06_east_gate_barbican.png")).convert("RGBA")
    sky_d.alpha_composite(gate, (480, 520 - gate.height + 8))
    sky_d.save(os.path.join(bg_dir, "d10_victory.png"), "PNG")

    sky_dusk = Image.open(os.path.join(bg_dir, "d02_sky_dusk.png")).convert("RGBA").resize((1280, 720))
    dd = ImageDraw.Draw(sky_dusk)
    dd.rectangle([0, 520, 1280, 720], fill=hex_to_rgba("#2D241C"))
    gate_br = Image.open(os.path.join(ASSETS_DIR, "buildings", "b06_east_gate_broken.png")).convert("RGBA")
    sky_dusk.alpha_composite(gate_br, (480, 520 - gate_br.height + 8))
    # Dark smoke tint
    dd.rectangle([0, 0, 1280, 720], fill=hex_to_rgba("#0B1426", 85))
    sky_dusk.save(os.path.join(bg_dir, "d11_defeat.png"), "PNG")
    print("Generated bg/d10_victory.png & bg/d11_defeat.png (1280x720)")

    # C4: e11_boss_bar.png (600x24)
    im_boss = Image.new("RGBA", (600, 24), (0, 0, 0, 0))
    db = ImageDraw.Draw(im_boss)
    db.rounded_rectangle([0, 0, 599, 23], radius=4, fill=hex_to_rgba("#1A202C", 240), outline=hex_to_rgba("#F6AD55"), width=2)
    db.rounded_rectangle([4, 4, 595, 19], radius=2, fill=hex_to_rgba("#742A2A"))
    db.line([(6, 6), (593, 6)], fill=hex_to_rgba("#C53030"), width=3)
    im_boss.save(os.path.join(ui_dir, "e11_boss_bar.png"), "PNG")
    print("Generated ui/e11_boss_bar.png (600x24)")

    # C5: fx_slash.png, fx_arrow_hit.png, fx_cannon_hit.png (192x192 = 96x96 * 2)
    im_s = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    ds = ImageDraw.Draw(im_s)
    ds.arc([16, 24, 176, 168], start=290, end=70, fill=hex_to_rgba("#FEFCBF", 230), width=14)
    ds.arc([28, 34, 164, 158], start=300, end=60, fill=hex_to_rgba("#D97706", 200), width=6)
    im_s.save(os.path.join(props_dir, "fx_slash.png"), "PNG")

    im_ah = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    dah = ImageDraw.Draw(im_ah)
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        x1, y1 = 96 + int(math.cos(rad)*18), 96 + int(math.sin(rad)*18)
        x2, y2 = 96 + int(math.cos(rad)*72), 96 + int(math.sin(rad)*72)
        dah.line([(x1, y1), (x2, y2)], fill=hex_to_rgba("#FEFCBF"), width=6)
    dah.ellipse([76, 76, 116, 116], fill=hex_to_rgba("#F6AD55"))
    im_ah.save(os.path.join(props_dir, "fx_arrow_hit.png"), "PNG")

    im_ch = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    dch = ImageDraw.Draw(im_ch)
    dch.ellipse([24, 24, 168, 168], fill=hex_to_rgba("#F6AD55", 190), outline=outline, width=3)
    dch.ellipse([48, 48, 144, 144], fill=hex_to_rgba("#F6E05E", 220))
    dch.ellipse([70, 70, 122, 122], fill=hex_to_rgba("#FEFCBF", 245))
    im_ch.save(os.path.join(props_dir, "fx_cannon_hit.png"), "PNG")
    print("Generated fx_slash.png, fx_arrow_hit.png, fx_cannon_hit.png (192x192)")

    # C6: fx_recruit.png, fx_levelup.png (240x400 = 120x200 * 2)
    for fname, col_hex in [("fx_recruit.png", "#68D391"), ("fx_levelup.png", "#F6E05E")]:
        im_p = Image.new("RGBA", (240, 400), (0, 0, 0, 0))
        arr = np.zeros((400, 240, 4), dtype=np.uint8)
        rc, gc, bc, _ = hex_to_rgba(col_hex)
        for y in range(400):
            # Fade near top
            vy = min(1.0, (400 - y) / 360.0)
            for x in range(40, 200):
                dx = abs(x - 120) / 80.0
                alpha = int((1.0 - dx*dx) * vy * 150)
                arr[y, x] = [rc, gc, bc, max(0, alpha)]
        im_p = Image.fromarray(arr)
        dp = ImageDraw.Draw(im_p)
        dp.ellipse([40, 360, 200, 396], outline=hex_to_rgba(col_hex, 230), width=4)
        im_p.save(os.path.join(props_dir, fname), "PNG")
    print("Generated fx_recruit.png & fx_levelup.png (240x400)")

if __name__ == "__main__":
    process_nanobanana_buildings()
    generate_a3_a4_a5()
    generate_b_group()
    generate_c_group()
    print("ALL A, B, C ASSETS GENERATED!")
