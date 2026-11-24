import os
import math
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

BASE_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\assets"

# 1.3 统一色板
COLORS = {
    # 场景
    "sky_night": "#101829",
    "night_mask": "#0B1426",
    "sky_day": "#4A6FA5",
    "sky_dusk": "#7A5C3E",
    "ground_fortress": "#3B3026",
    "stone_road": "#718096",
    "beach": "#B79F78",
    "sea": "#1E4E79",
    "mountain_far": "#2C3E50",
    "mountain_daluo": "#2F4F4F",
    "house_light": "#3B4A59",
    "house_dark": "#2D3748",
    
    # 地标
    "shrine": "#9B2C2C",
    "paddy": "#68A357",
    "salt_office": "#D6B36A",
    "water_gate": "#5A6772",
    "main_wall": "#718096",
    "east_gate": "#4A5568",
    "arrow_tower": "#8C6D46",
    "cannon_tower": "#4A5568",

    # 我方单位点缀色
    "hero": "#D97706",
    "idle": "#CBD5E0",
    "farmer": "#48BB78",
    "salt_worker": "#ECC94B",
    "builder": "#ED8936",
    "militia": "#4299E1",
    "kung_fu": "#E53E3E",

    # 敌方
    "scout": "#9F7AEA",
    "samurai": "#C53030",
    "boss": "#742A2A",

    # UI / 通用
    "panel_bg": "#1A202C",
    "outline": "#1A202C",
    "border": "#4A5568",
    "gold_bright": "#F6E05E",
    "gold_pale": "#FEFCBF",
    "gold_sub": "#FBD38D",
    "text_main": "#E2E8F0",
    "text_sub": "#CBD5E0",
    "hp_green": "#48BB78",
    "hp_red": "#E53E3E",
    "durability_blue": "#63B3ED",
    "prompt_orange": "#F6AD55",
    "skin": "#FBD38D",
}

def hex_to_rgb(hex_code, alpha=255):
    hex_code = hex_code.lstrip('#')
    lv = len(hex_code)
    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)
    return (r, g, b, alpha)

def blend_colors(c1, c2, t):
    """Linear blend between two RGBA tuples (t in [0, 1])"""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))

def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

# -------------------------------------------------------------
# D 组：场景与背景
# -------------------------------------------------------------
def generate_backgrounds():
    bg_dir = os.path.join(BASE_DIR, "bg")
    os.makedirs(bg_dir, exist_ok=True)
    
    # D01 天空·白昼 (1280x720) 渐变 #4A6FA5 -> #E2E8F0
    img_day = Image.new("RGBA", (1280, 720))
    top_c = hex_to_rgb(COLORS["sky_day"])
    bot_c = hex_to_rgb("#E2E8F0")
    for y in range(720):
        t = y / 719.0
        c = blend_colors(top_c, bot_c, t)
        for x in range(1280):
            img_day.putpixel((x, y), c)
    # Add subtle distant mountain / cloud layer
    draw = ImageDraw.Draw(img_day)
    cloud_c = hex_to_rgb("#CBD5E0", 60)
    for cx in range(0, 1280, 240):
        draw.ellipse([cx, 480, cx + 320, 560], fill=cloud_c)
    img_day.save(os.path.join(bg_dir, "d01_sky_day.png"))
    print("Generated d01_sky_day.png")

    # D02 天空·黄昏 (1280x720) #7A5C3E -> #DD6B20 -> #FBD38D
    img_dusk = Image.new("RGBA", (1280, 720))
    c_top = hex_to_rgb(COLORS["sky_dusk"])
    c_mid = hex_to_rgb("#DD6B20")
    c_bot = hex_to_rgb("#FBD38D")
    for y in range(720):
        t = y / 719.0
        if t < 0.6:
            c = blend_colors(c_top, c_mid, t / 0.6)
        else:
            c = blend_colors(c_mid, c_bot, (t - 0.6) / 0.4)
        for x in range(1280):
            img_dusk.putpixel((x, y), c)
    img_dusk.save(os.path.join(bg_dir, "d02_sky_dusk.png"))
    print("Generated d02_sky_dusk.png")

    # D03 天空·黑夜 (1280x720) #101829 -> #0B1426
    img_night = Image.new("RGBA", (1280, 720))
    top_n = hex_to_rgb(COLORS["sky_night"])
    bot_n = hex_to_rgb(COLORS["night_mask"])
    np.random.seed(42)
    for y in range(720):
        t = y / 719.0
        c = blend_colors(top_n, bot_n, t)
        for x in range(1280):
            img_night.putpixel((x, y), c)
    # Fine subtle stars in the upper half
    draw_n = ImageDraw.Draw(img_night)
    for _ in range(90):
        sx = int(np.random.uniform(10, 1270))
        sy = int(np.random.uniform(10, 360))
        br = int(np.random.uniform(140, 240))
        draw_n.point((sx, sy), fill=(240, 245, 255, br))
    img_night.save(os.path.join(bg_dir, "d03_sky_night.png"))
    print("Generated d03_sky_night.png")

    # D04 地面·堡内 (640x160) 夯土 #3B3026 + 石板路 #718096 (无缝水平平铺)
    img_g_fort = Image.new("RGBA", (640, 160), hex_to_rgb(COLORS["ground_fortress"]))
    draw_gf = ImageDraw.Draw(img_g_fort)
    # Top 48px: Stone flagstones
    stone_c = hex_to_rgb(COLORS["stone_road"])
    stone_dark = hex_to_rgb("#4A5568")
    line_c = hex_to_rgb(COLORS["outline"])
    draw_gf.rectangle([0, 0, 640, 48], fill=stone_c)
    # Flagstone blocks
    for bx in range(0, 640, 64):
        draw_gf.line([bx, 0, bx, 48], fill=line_c, width=2)
        draw_gf.rectangle([bx+2, 2, bx+62, 46], outline=stone_dark, width=1)
    # Separation edge between stone path and rammed earth
    draw_gf.line([0, 48, 640, 48], fill=line_c, width=3)
    # Rammed earth texture layers
    earth_sub = hex_to_rgb("#2D241C")
    for y in range(60, 160, 18):
        draw_gf.line([0, y, 640, y], fill=earth_sub, width=1)
    img_g_fort.save(os.path.join(bg_dir, "d04_ground_fortress.png"))
    print("Generated d04_ground_fortress.png")

    # D05 地面·城外滩涂 (640x160) 泥滩 #B79F78 + 潮间泥带
    img_g_beach = Image.new("RGBA", (640, 160), hex_to_rgb(COLORS["beach"]))
    draw_gb = ImageDraw.Draw(img_g_beach)
    mud_c = hex_to_rgb("#9C825E")
    reed_c = hex_to_rgb("#5B6A45")
    for rx in range(16, 640, 48):
        draw_gb.line([rx, 14, rx-4, 0], fill=reed_c, width=2)
        draw_gb.line([rx+4, 14, rx+8, 0], fill=reed_c, width=2)
    for my in range(40, 160, 24):
        draw_gb.line([0, my, 640, my], fill=mud_c, width=2)
    img_g_beach.save(os.path.join(bg_dir, "d05_ground_beach.png"))
    print("Generated d05_ground_beach.png")

    # D06 城墙远景地平线 (1280x160) 剪影 #3B4A59
    img_horiz = Image.new("RGBA", (1280, 160), (0, 0, 0, 0))
    draw_h = ImageDraw.Draw(img_horiz)
    wall_c = hex_to_rgb(COLORS["house_light"])
    line_c = hex_to_rgb(COLORS["outline"])
    # Draw repeating Ming wall crenellations and watchtowers
    wall_y = 70
    draw_h.rectangle([0, wall_y, 1280, 160], fill=wall_c)
    for cx in range(0, 1280, 20):
        # Battlements / crenels
        draw_h.rectangle([cx, wall_y - 12, cx + 12, wall_y], fill=wall_c)
    # Distant towers every 320px
    for tx in range(80, 1280, 320):
        # Tower base
        draw_h.rectangle([tx, wall_y - 38, tx + 48, wall_y], fill=wall_c)
        # Hip-and-gable roof silhouette
        draw_h.polygon([(tx - 8, wall_y - 38), (tx + 56, wall_y - 38), (tx + 24, wall_y - 58)], fill=wall_c)
    img_horiz.save(os.path.join(bg_dir, "d06_horizon_silhouette.png"))
    print("Generated d06_horizon_silhouette.png")

    # D07 夜色/火光遮罩 (1280x720) 40% 透明度 PNG (#0B1426, alpha=102)
    img_mask = Image.new("RGBA", (1280, 720), hex_to_rgb(COLORS["night_mask"], alpha=102))
    img_mask.save(os.path.join(bg_dir, "d07_night_mask.png"))
    print("Generated d07_night_mask.png")

# -------------------------------------------------------------
# E 组：UI 素材
# -------------------------------------------------------------
def generate_ui():
    ui_dir = os.path.join(BASE_DIR, "ui")
    os.makedirs(ui_dir, exist_ok=True)

    # E01 顶栏底板 (1280x64) #1A202C 88% alpha (alpha=224), 下缘描边 #4A5568 2px
    img_top = Image.new("RGBA", (1280, 64), hex_to_rgb(COLORS["panel_bg"], 224))
    draw_top = ImageDraw.Draw(img_top)
    draw_top.line([0, 62, 1280, 62], fill=hex_to_rgb(COLORS["border"]), width=2)
    # Gold corner brackets
    draw_top.line([0, 60, 24, 60], fill=hex_to_rgb(COLORS["prompt_orange"]), width=3)
    draw_top.line([1256, 60, 1280, 60], fill=hex_to_rgb(COLORS["prompt_orange"]), width=3)
    img_top.save(os.path.join(ui_dir, "e01_top_bar.png"))
    print("Generated e01_top_bar.png")

    # E02 底栏底板 (1280x76) #1A202C 88% alpha, 上缘描边 #4A5568 2px
    img_bot = Image.new("RGBA", (1280, 76), hex_to_rgb(COLORS["panel_bg"], 224))
    draw_bot = ImageDraw.Draw(img_bot)
    draw_bot.line([0, 1, 1280, 1], fill=hex_to_rgb(COLORS["border"]), width=2)
    draw_bot.line([0, 3, 30, 3], fill=hex_to_rgb(COLORS["prompt_orange"]), width=3)
    draw_bot.line([1250, 3, 1280, 3], fill=hex_to_rgb(COLORS["prompt_orange"]), width=3)
    img_bot.save(os.path.join(ui_dir, "e02_bottom_bar.png"))
    print("Generated e02_bottom_bar.png")

    # E03 弹窗底板 (700x380) 圆角 8px，金描边 #F6AD55 2px，四角卷云纹
    img_modal = Image.new("RGBA", (700, 380), (0, 0, 0, 0))
    draw_m = ImageDraw.Draw(img_modal)
    bg_c = hex_to_rgb(COLORS["panel_bg"], 240)
    gold_c = hex_to_rgb(COLORS["prompt_orange"])
    draw_m.rounded_rectangle([4, 4, 695, 375], radius=8, fill=bg_c, outline=gold_c, width=2)
    # Inner border
    draw_m.rounded_rectangle([10, 10, 689, 369], radius=6, outline=hex_to_rgb(COLORS["border"]), width=1)
    # Cloud corner ornaments
    corners = [(14, 14), (685, 14), (14, 365), (685, 365)]
    for cx, cy in corners:
        draw_m.ellipse([cx-4, cy-4, cx+4, cy+4], fill=hex_to_rgb(COLORS["gold_bright"]))
    img_modal.save(os.path.join(ui_dir, "e03_modal_dialog.png"))
    print("Generated e03_modal_dialog.png")

    # E04 按钮四态 (200x56)
    def make_btn(fill_hex, border_hex, out_name, alpha=255, glow=False):
        img_b = Image.new("RGBA", (200, 56), (0, 0, 0, 0))
        draw_b = ImageDraw.Draw(img_b)
        f_c = hex_to_rgb(fill_hex, alpha)
        b_c = hex_to_rgb(border_hex, alpha)
        draw_b.rounded_rectangle([2, 2, 197, 53], radius=6, fill=f_c, outline=b_c, width=2)
        if glow:
            draw_b.rounded_rectangle([5, 5, 194, 50], radius=4, outline=hex_to_rgb(COLORS["gold_bright"], 160), width=1)
        # Subtle horizontal bevel highlight
        draw_b.line([8, 6, 191, 6], fill=(255, 255, 255, 40), width=1)
        img_b.save(os.path.join(ui_dir, out_name))
        print(f"Generated {out_name}")

    make_btn(COLORS["house_dark"], COLORS["border"], "e04_btn_normal.png")
    make_btn(COLORS["house_light"], COLORS["gold_bright"], "e04_btn_hover.png", glow=True)
    make_btn(COLORS["panel_bg"], "#D69E2E", "e04_btn_pressed.png")
    make_btn(COLORS["panel_bg"], COLORS["house_dark"], "e04_btn_disabled.png", alpha=140)

    # E07 血条九宫格 (64x16)
    img_hp = Image.new("RGBA", (64, 16), (0, 0, 0, 0))
    draw_hp = ImageDraw.Draw(img_hp)
    draw_hp.rectangle([0, 0, 63, 15], fill=hex_to_rgb(COLORS["panel_bg"]), outline=hex_to_rgb(COLORS["outline"]), width=1)
    draw_hp.rectangle([2, 2, 61, 13], fill=hex_to_rgb(COLORS["hp_green"]))
    draw_hp.line([2, 3, 61, 3], fill=(255, 255, 255, 80), width=1)
    img_hp.save(os.path.join(ui_dir, "e07_bar_health.png"))
    print("Generated e07_bar_health.png")

    # E08 耐久/进度条九宫格 (64x16)
    img_dur = Image.new("RGBA", (64, 16), (0, 0, 0, 0))
    draw_dur = ImageDraw.Draw(img_dur)
    draw_dur.rectangle([0, 0, 63, 15], fill=hex_to_rgb(COLORS["panel_bg"]), outline=hex_to_rgb(COLORS["outline"]), width=1)
    draw_dur.rectangle([2, 2, 61, 13], fill=hex_to_rgb(COLORS["durability_blue"]))
    draw_dur.line([2, 3, 61, 3], fill=(255, 255, 255, 80), width=1)
    img_dur.save(os.path.join(ui_dir, "e08_bar_stamina.png"))
    print("Generated e08_bar_stamina.png")

    # E09 交互提示气泡 (96x96)
    img_bub = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    draw_bub = ImageDraw.Draw(img_bub)
    # Main bubble round rect
    draw_bub.rounded_rectangle([8, 8, 87, 72], radius=8, fill=hex_to_rgb(COLORS["panel_bg"], 230), outline=hex_to_rgb(COLORS["prompt_orange"]), width=2)
    # Downward pointer
    draw_bub.polygon([(40, 72), (56, 72), (48, 88)], fill=hex_to_rgb(COLORS["panel_bg"], 230))
    draw_bub.line([(40, 72), (48, 88)], fill=hex_to_rgb(COLORS["prompt_orange"]), width=2)
    draw_bub.line([(56, 72), (48, 88)], fill=hex_to_rgb(COLORS["prompt_orange"]), width=2)
    # Inner hotkey slot
    draw_bub.rounded_rectangle([28, 22, 68, 60], radius=4, fill=hex_to_rgb(COLORS["house_dark"]), outline=hex_to_rgb(COLORS["gold_pale"]), width=1)
    img_bub.save(os.path.join(ui_dir, "e09_prompt_bubble.png"))
    print("Generated e09_prompt_bubble.png")

    # E12 鼠标指针 (32x32)
    img_cur = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw_cur = ImageDraw.Draw(img_cur)
    # Ming style dagger/arrow pointer
    poly = [(4, 4), (24, 12), (15, 15), (12, 24)]
    draw_cur.polygon(poly, fill=hex_to_rgb(COLORS["gold_bright"]), outline=hex_to_rgb(COLORS["outline"]))
    draw_cur.line([(15, 15), (26, 26)], fill=hex_to_rgb(COLORS["gold_bright"]), width=2)
    img_cur.save(os.path.join(ui_dir, "e12_cursor.png"))
    print("Generated e12_cursor.png")

# -------------------------------------------------------------
# F 组：图标 (48x48, 透明底, 1.5px 描边 #1A202C, 统一光向)
# -------------------------------------------------------------
def generate_icons():
    icon_dir = os.path.join(BASE_DIR, "ui", "icons")
    os.makedirs(icon_dir, exist_ok=True)
    outline = hex_to_rgb(COLORS["outline"])

    def create_icon_canvas():
        return Image.new("RGBA", (48, 48), (0, 0, 0, 0))

    # F01 白银 (银锭)
    im = create_icon_canvas()
    d = ImageDraw.Draw(im)
    # Ming sycee shape (boat-like ingot)
    d.polygon([(10, 18), (38, 18), (42, 28), (6, 28)], fill=hex_to_rgb(COLORS["idle"]), outline=outline)
    d.ellipse([14, 14, 34, 22], fill=hex_to_rgb(COLORS["text_main"]), outline=outline)
    d.polygon([(14, 28), (34, 28), (30, 36), (18, 36)], fill=hex_to_rgb("#A0AEC0"), outline=outline)
    im.save(os.path.join(icon_dir, "icon_silver.png"))

    # F02 粮草 (稻穗)
    im = create_icon_canvas()
    d = ImageDraw.Draw(im)
    stem_c = hex_to_rgb("#D69E2E")
    grain_c = hex_to_rgb(COLORS["salt_worker"])
    d.line([(24, 42), (24, 12)], fill=stem_c, width=2)
    # Grains
    for gy in range(12, 34, 6):
        d.ellipse([16, gy, 23, gy+5], fill=grain_c, outline=outline)
        d.ellipse([25, gy-2, 32, gy+3], fill=grain_c, outline=outline)
    im.save(os.path.join(icon_dir, "icon_food.png"))

    # F03 人口 (族丁头)
    im = create_icon_canvas()
    d = ImageDraw.Draw(im)
    # Head and headcloth
    d.ellipse([16, 12, 32, 28], fill=hex_to_rgb(COLORS["skin"]), outline=outline)
    d.chord([15, 10, 33, 22], start=180, end=360, fill=hex_to_rgb(COLORS["idle"]), outline=outline)
    # Shoulders
    d.polygon([(10, 42), (38, 42), (34, 30), (14, 30)], fill=hex_to_rgb(COLORS["house_light"]), outline=outline)
    im.save(os.path.join(icon_dir, "icon_population.png"))

    # F04 宗祠耐久 (王氏宗祠马头墙门楼)
    im = create_icon_canvas()
    d = ImageDraw.Draw(im)
    shrine_c = hex_to_rgb(COLORS["shrine"])
    d.rectangle([12, 16, 36, 40], fill=shrine_c, outline=outline)
    # Horsehead gable
    d.polygon([(8, 16), (40, 16), (36, 10), (12, 10)], fill=hex_to_rgb(COLORS["text_main"]), outline=outline)
    d.rectangle([20, 26, 28, 40], fill=hex_to_rgb(COLORS["panel_bg"]), outline=outline)
    im.save(os.path.join(icon_dir, "icon_shrine.png"))

    # F05 东门瓮城 (城门石拱)
    im = create_icon_canvas()
    d = ImageDraw.Draw(im)
    gate_c = hex_to_rgb(COLORS["east_gate"])
    d.rectangle([8, 14, 40, 42], fill=gate_c, outline=outline)
    # Crenellations
    for cx in [10, 20, 30]:
        d.rectangle([cx, 10, cx+6, 14], fill=gate_c, outline=outline)
    d.pieslice([16, 24, 32, 42], start=180, end=360, fill=hex_to_rgb(COLORS["panel_bg"]), outline=outline)
    im.save(os.path.join(icon_dir, "icon_east_gate.png"))

    # F06 内城水门
    im = create_icon_canvas()
    d = ImageDraw.Draw(im)
    d.rectangle([10, 14, 38, 38], fill=hex_to_rgb(COLORS["water_gate"]), outline=outline)
    # Water ripples at base
    d.line([(8, 40), (40, 40)], fill=hex_to_rgb(COLORS["durability_blue"]), width=3)
    d.line([(14, 22), (14, 36)], fill=outline, width=2)
    d.line([(24, 22), (24, 36)], fill=outline, width=2)
    d.line([(34, 22), (34, 36)], fill=outline, width=2)
    im.save(os.path.join(icon_dir, "icon_water_gate.png"))

    # F07 敌台箭楼
    im = create_icon_canvas()
    d = ImageDraw.Draw(im)
    d.polygon([(16, 10), (32, 10), (36, 42), (12, 42)], fill=hex_to_rgb(COLORS["arrow_tower"]), outline=outline)
    d.rectangle([20, 20, 28, 26], fill=hex_to_rgb(COLORS["panel_bg"]), outline=outline)
    im.save(os.path.join(icon_dir, "icon_tower.png"))

    # F08 昼夜/夜数 (日/月)
    im = create_icon_canvas()
    d = ImageDraw.Draw(im)
    d.ellipse([12, 12, 36, 36], fill=hex_to_rgb(COLORS["prompt_orange"]), outline=outline)
    im.save(os.path.join(icon_dir, "icon_day.png"))

    im = create_icon_canvas()
    d = ImageDraw.Draw(im)
    d.ellipse([10, 10, 38, 38], fill=hex_to_rgb(COLORS["gold_pale"]), outline=outline)
    d.ellipse([16, 8, 44, 38], fill=(0, 0, 0, 0))
    im.save(os.path.join(icon_dir, "icon_night.png"))

    # 六职业图标
    roles = [
        ("icon_role_idle.png", COLORS["idle"]),
        ("icon_role_farmer.png", COLORS["farmer"]),
        ("icon_role_salt.png", COLORS["salt_worker"]),
        ("icon_role_builder.png", COLORS["builder"]),
        ("icon_role_militia.png", COLORS["militia"]),
        ("icon_role_kungfu.png", COLORS["kung_fu"]),
    ]
    for r_name, r_color in roles:
        im = create_icon_canvas()
        d = ImageDraw.Draw(im)
        d.ellipse([10, 10, 38, 38], fill=hex_to_rgb(r_color), outline=outline, width=2)
        d.ellipse([14, 14, 34, 34], outline=hex_to_rgb(COLORS["gold_pale"]), width=1)
        im.save(os.path.join(icon_dir, r_name))
        print(f"Generated {r_name}")

    # 操作技能图标 (4)
    skills = [
        ("icon_op_interact.png", COLORS["prompt_orange"]),
        ("icon_op_qilin.png", COLORS["hero"]),
        ("icon_op_rally.png", COLORS["kung_fu"]),
        ("icon_op_move.png", COLORS["militia"]),
    ]
    for s_name, s_color in skills:
        im = create_icon_canvas()
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([6, 6, 42, 42], radius=6, fill=hex_to_rgb(s_color), outline=outline, width=2)
        d.rounded_rectangle([10, 10, 38, 38], radius=4, outline=hex_to_rgb(COLORS["gold_bright"]), width=1)
        im.save(os.path.join(icon_dir, s_name))
        print(f"Generated {s_name}")

# -------------------------------------------------------------
# A11 & A12: 道具与掉落拾荒 (48x48)
# -------------------------------------------------------------
def generate_tools_and_props():
    tools_dir = os.path.join(BASE_DIR, "sprites", "tools")
    os.makedirs(tools_dir, exist_ok=True)
    outline = hex_to_rgb(COLORS["outline"])

    # 锄头 (A11) 48x48
    im = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Wooden shaft diagonal
    d.line([(10, 38), (34, 14)], fill=hex_to_rgb("#8C6D46"), width=3)
    # Iron blade
    d.polygon([(32, 10), (42, 16), (36, 22), (28, 14)], fill=hex_to_rgb(COLORS["stone_road"]), outline=outline)
    # Farmer green sash tie
    d.ellipse([26, 18, 32, 24], fill=hex_to_rgb(COLORS["farmer"]))
    im.save(os.path.join(tools_dir, "tool_hoe.png"))

    # 盐铲 (A11) 48x48
    im = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line([(10, 38), (28, 20)], fill=hex_to_rgb("#8C6D46"), width=3)
    d.rectangle([24, 10, 40, 22], fill=hex_to_rgb("#D6B36A"), outline=outline)
    # Salt worker yellow sash tie
    d.ellipse([22, 22, 28, 28], fill=hex_to_rgb(COLORS["salt_worker"]))
    im.save(os.path.join(tools_dir, "tool_shovel.png"))

    # 木锤 (A11) 48x48
    im = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line([(12, 36), (30, 18)], fill=hex_to_rgb("#8C6D46"), width=3)
    d.rectangle([22, 8, 40, 20], fill=hex_to_rgb("#B79F78"), outline=outline)
    # Builder orange sash tie
    d.ellipse([22, 20, 28, 26], fill=hex_to_rgb(COLORS["builder"]))
    im.save(os.path.join(tools_dir, "tool_hammer.png"))

    # 长枪 (A11) 48x48
    im = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line([(6, 42), (38, 10)], fill=hex_to_rgb("#8C6D46"), width=2)
    # Spear blade
    d.polygon([(36, 12), (44, 4), (40, 16)], fill=hex_to_rgb(COLORS["text_main"]), outline=outline)
    # Red tassel
    d.ellipse([32, 12, 38, 18], fill=hex_to_rgb(COLORS["kung_fu"]))
    # Militia blue ribbon
    d.line([(30, 18), (26, 24)], fill=hex_to_rgb(COLORS["militia"]), width=2)
    im.save(os.path.join(tools_dir, "tool_spear.png"))

    # 红绸拳谱 (A11) 48x48
    im = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 14, 38, 34], radius=3, fill=hex_to_rgb("#FEFCBF"), outline=outline)
    d.line([(24, 14), (24, 34)], fill=hex_to_rgb(COLORS["kung_fu"]), width=4)
    im.save(os.path.join(tools_dir, "tool_manual.png"))

    # 拾荒：盐包 (A12) 48x48
    im = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([10, 14, 38, 40], fill=hex_to_rgb("#C2A782"), outline=outline)
    # Salt crystals spilling
    d.polygon([(20, 14), (28, 14), (24, 8)], fill=hex_to_rgb("#E2E8F0"), outline=outline)
    im.save(os.path.join(tools_dir, "salvage_salt_bag.png"))

    # 拾荒：漂流木料 (A12) 48x48
    im = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    wood_c = hex_to_rgb("#8C6D46")
    d.rounded_rectangle([6, 16, 42, 26], radius=2, fill=wood_c, outline=outline)
    d.rounded_rectangle([6, 26, 42, 36], radius=2, fill=wood_c, outline=outline)
    # Ropes
    d.line([(16, 14), (16, 38)], fill=hex_to_rgb("#FEFCBF"), width=2)
    d.line([(32, 14), (32, 38)], fill=hex_to_rgb("#FEFCBF"), width=2)
    im.save(os.path.join(tools_dir, "salvage_driftwood.png"))
    print("Generated all tools and salvage items.")

# -------------------------------------------------------------
# C 组：投射物与特效
# -------------------------------------------------------------
def generate_vfx_and_projectiles():
    props_dir = os.path.join(BASE_DIR, "sprites", "props")
    os.makedirs(props_dir, exist_ok=True)
    outline = hex_to_rgb(COLORS["outline"])

    # C01 箭矢 (32x16) 朝右
    im = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line([(4, 8), (28, 8)], fill=hex_to_rgb("#8C6D46"), width=2)
    d.polygon([(24, 4), (30, 8), (24, 12)], fill=hex_to_rgb(COLORS["stone_road"]), outline=outline)
    d.line([(4, 4), (8, 8), (4, 12)], fill=hex_to_rgb(COLORS["text_main"]), width=1)
    im.save(os.path.join(props_dir, "proj_arrow.png"))

    # C02 炮弹 (24x24)
    im = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([3, 3, 21, 21], fill=hex_to_rgb(COLORS["house_dark"]), outline=outline)
    d.ellipse([5, 5, 11, 11], fill=hex_to_rgb(COLORS["stone_road"]))
    im.save(os.path.join(props_dir, "proj_cannonball.png"))

    # C05 拳师震击波 (224x64)
    im = Image.new("RGBA", (224, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    red_c = hex_to_rgb(COLORS["kung_fu"], 200)
    gold_c = hex_to_rgb(COLORS["gold_bright"], 230)
    d.ellipse([10, 10, 214, 54], outline=red_c, width=3)
    d.ellipse([24, 16, 200, 48], outline=gold_c, width=2)
    im.save(os.path.join(props_dir, "fx_shockwave.png"))

    # C06 忠义光环 (512x512) 半透明金色圆环
    im = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ring_c = hex_to_rgb(COLORS["gold_pale"], 180)
    inner_c = hex_to_rgb(COLORS["gold_bright"], 220)
    d.ellipse([32, 32, 480, 480], outline=ring_c, width=12)
    d.ellipse([64, 64, 448, 448], outline=inner_c, width=4)
    im.save(os.path.join(props_dir, "fx_halo_loyalty.png"))

    # C07 火把光晕 (128x128) 径向橙光 #F6AD55
    im = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    center = (64, 64)
    for r in range(60, 0, -2):
        alpha = int((1.0 - r / 60.0) ** 1.8 * 160)
        c = hex_to_rgb(COLORS["prompt_orange"], alpha)
        d = ImageDraw.Draw(im)
        d.ellipse([center[0]-r, center[1]-r, center[0]+r, center[1]+r], fill=c)
    im.save(os.path.join(props_dir, "fx_torch_glow.png"))
    print("Generated VFX and projectiles.")

# -------------------------------------------------------------
# B 组：核心地标建筑 (规范尺寸，正侧视，符合 1.3 色板与 2.2 规范)
# -------------------------------------------------------------
def generate_landmarks():
    b_dir = os.path.join(BASE_DIR, "buildings")
    os.makedirs(b_dir, exist_ok=True)
    outline = hex_to_rgb(COLORS["outline"])

    # B07 敌台箭楼 (112x210) 底部中心对齐
    im = Image.new("RGBA", (112, 210), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Stone base (80px high, 100px wide)
    stone_c = hex_to_rgb(COLORS["stone_road"])
    d.polygon([(16, 202), (96, 202), (88, 110), (24, 110)], fill=stone_c, outline=outline, width=2)
    # Wooden upper arrow tower (80px high)
    wood_c = hex_to_rgb(COLORS["arrow_tower"])
    d.rectangle([30, 40, 82, 110], fill=wood_c, outline=outline, width=2)
    # Slit windows
    d.rectangle([40, 56, 48, 76], fill=hex_to_rgb(COLORS["panel_bg"]), outline=outline)
    d.rectangle([64, 56, 72, 76], fill=hex_to_rgb(COLORS["panel_bg"]), outline=outline)
    # Ming hip-and-gable eave roof
    d.polygon([(12, 40), (100, 40), (56, 12)], fill=hex_to_rgb(COLORS["house_dark"]), outline=outline, width=2)
    im.save(os.path.join(b_dir, "b07_tower_arrow.png"))

    # B08 佛郎机炮台 (112x210)
    im = Image.new("RGBA", (112, 210), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(12, 202), (100, 202), (92, 120), (20, 120)], fill=stone_c, outline=outline, width=2)
    # Parapet
    d.rectangle([20, 96, 92, 120], fill=hex_to_rgb(COLORS["cannon_tower"]), outline=outline, width=2)
    # Folangji breech-loading cannon barrel pointing right
    d.polygon([(46, 88), (96, 80), (96, 90), (46, 98)], fill=hex_to_rgb(COLORS["panel_bg"]), outline=outline, width=2)
    im.save(os.path.join(b_dir, "b08_tower_cannon.png"))

    # B02 堡内水田 (440x88)
    im = Image.new("RGBA", (440, 88), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    paddy_c = hex_to_rgb(COLORS["paddy"])
    water_c = hex_to_rgb("#4A7C59")
    d.rectangle([0, 10, 440, 86], fill=paddy_c, outline=outline, width=2)
    # Rows of young rice seedlings
    for px in range(16, 430, 24):
        for py in [26, 46, 66]:
            d.polygon([(px, py), (px-4, py-10), (px+4, py-10)], fill=hex_to_rgb("#85E368"))
    im.save(os.path.join(b_dir, "b02_paddy.png"))

    # B06 环海楼与东门瓮城 (280x440) 核心地标
    im = Image.new("RGBA", (280, 440), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    wall_c = hex_to_rgb(COLORS["east_gate"])
    # Massive fortress wall and barbican arch
    d.polygon([(20, 432), (260, 432), (240, 240), (40, 240)], fill=wall_c, outline=outline, width=2)
    # Stone arch gateway
    d.pieslice([80, 310, 200, 432], start=180, end=360, fill=hex_to_rgb(COLORS["panel_bg"]), outline=outline, width=2)
    # Two-tiered watchtower on top
    d.rectangle([60, 160, 220, 240], fill=hex_to_rgb(COLORS["arrow_tower"]), outline=outline, width=2)
    d.polygon([(40, 160), (240, 160), (140, 120)], fill=hex_to_rgb(COLORS["house_dark"]), outline=outline, width=2)
    d.rectangle([80, 80, 200, 120], fill=hex_to_rgb(COLORS["arrow_tower"]), outline=outline, width=2)
    d.polygon([(60, 80), (220, 80), (140, 46)], fill=hex_to_rgb(COLORS["house_dark"]), outline=outline, width=2)
    im.save(os.path.join(b_dir, "b06_east_gate_barbican.png"))

    # B01 王氏宗祠 (360x360)
    im = Image.new("RGBA", (360, 360), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shrine_c = hex_to_rgb(COLORS["shrine"])
    d.rectangle([40, 160, 320, 352], fill=shrine_c, outline=outline, width=2)
    # Ming horsehead gable roof
    d.polygon([(20, 160), (340, 160), (180, 80)], fill=hex_to_rgb(COLORS["house_dark"]), outline=outline, width=3)
    # Entrance red door with gold studs
    d.rectangle([130, 240, 230, 352], fill=hex_to_rgb("#742A2A"), outline=outline, width=2)
    d.rectangle([120, 200, 240, 230], fill=hex_to_rgb(COLORS["panel_bg"]), outline=hex_to_rgb(COLORS["gold_bright"]), width=2)
    im.save(os.path.join(b_dir, "b01_shrine.png"))

    # B04 内城水门与作坊 (260x380)
    im = Image.new("RGBA", (260, 380), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([20, 120, 240, 372], fill=hex_to_rgb(COLORS["water_gate"]), outline=outline, width=2)
    # Iron sluice gate
    d.rectangle([60, 240, 200, 372], fill=hex_to_rgb(COLORS["panel_bg"]), outline=outline, width=2)
    for gy in range(256, 372, 24):
        d.line([(60, gy), (200, gy)], fill=hex_to_rgb(COLORS["stone_road"]), width=2)
    # Roof
    d.polygon([(10, 120), (250, 120), (130, 70)], fill=hex_to_rgb(COLORS["house_dark"]), outline=outline, width=2)
    im.save(os.path.join(b_dir, "b04_inner_water_gate.png"))

    print("Generated all core landmarks.")

# -------------------------------------------------------------
# A 组：族丁与敌方标准立绘骨架 (128x192 / 192x256, 正侧视, 规范色板)
# -------------------------------------------------------------
def generate_unit_sprites():
    v_dir = os.path.join(BASE_DIR, "sprites", "villagers")
    e_dir = os.path.join(BASE_DIR, "sprites", "enemies")
    os.makedirs(v_dir, exist_ok=True)
    os.makedirs(e_dir, exist_ok=True)
    outline = hex_to_rgb(COLORS["outline"])

    # 6 族丁职业 (A02-A07, 128x192, 正侧视向右, 底部中心对齐)
    villager_defs = [
        ("villager_idle_01.png", COLORS["idle"], "none"),
        ("villager_farmer_01.png", COLORS["farmer"], "hoe"),
        ("villager_salt_worker_01.png", COLORS["salt_worker"], "shovel"),
        ("villager_builder_01.png", COLORS["builder"], "hammer"),
        ("villager_militia_01.png", COLORS["militia"], "spear"),
        ("villager_kung_fu_01.png", COLORS["kung_fu"], "boxing"),
    ]

    for fname, ribbon_color, tool in villager_defs:
        im = Image.new("RGBA", (128, 192), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        ribbon_c = hex_to_rgb(ribbon_color)
        tunic_c = hex_to_rgb("#4A5568") if tool == "spear" else hex_to_rgb("#3B3026")
        
        # Legs / Pants (y: 130 to 182)
        d.polygon([(52, 130), (64, 130), (66, 182), (54, 182)], fill=hex_to_rgb("#2D3748"), outline=outline)
        d.polygon([(66, 130), (78, 130), (84, 182), (72, 182)], fill=hex_to_rgb("#2D3748"), outline=outline)
        # Shoes (facing right)
        d.polygon([(54, 180), (74, 180), (74, 186), (54, 186)], fill=hex_to_rgb("#1A202C"))
        d.polygon([(72, 180), (94, 180), (94, 186), (72, 186)], fill=hex_to_rgb("#1A202C"))

        # Torso / Short tunic (y: 80 to 135)
        d.polygon([(46, 80), (86, 80), (88, 135), (44, 135)], fill=tunic_c, outline=outline, width=2)
        # Waist band / ribbon
        d.rectangle([44, 118, 88, 126], fill=ribbon_c, outline=outline)

        # Head / Face (facing right)
        d.ellipse([54, 46, 80, 72], fill=hex_to_rgb(COLORS["skin"]), outline=outline)
        if tool == "farmer":
            # Straw hat
            d.polygon([(36, 48), (96, 48), (66, 26)], fill=hex_to_rgb("#D6B36A"), outline=outline)
        else:
            # Ming headcloth
            d.chord([52, 42, 82, 64], start=180, end=360, fill=ribbon_c, outline=outline)

        # Arms and tools
        d.polygon([(56, 84), (74, 98), (68, 120), (52, 106)], fill=tunic_c, outline=outline)
        if tool == "spear":
            # Upright spear
            d.line([(86, 18), (86, 184)], fill=hex_to_rgb("#8C6D46"), width=3)
            d.polygon([(82, 18), (86, 4), (90, 18)], fill=hex_to_rgb(COLORS["text_main"]), outline=outline)
            d.ellipse([82, 18, 90, 26], fill=hex_to_rgb(COLORS["kung_fu"]))
        elif tool == "hoe":
            d.line([(70, 70), (88, 160)], fill=hex_to_rgb("#8C6D46"), width=3)
            d.polygon([(84, 160), (96, 164), (90, 172)], fill=hex_to_rgb(COLORS["stone_road"]), outline=outline)
        elif tool == "shovel":
            d.line([(70, 70), (88, 160)], fill=hex_to_rgb("#8C6D46"), width=3)
            d.rectangle([(84, 150), (98, 170)], fill=hex_to_rgb(COLORS["salt_worker"]), outline=outline)
        elif tool == "hammer":
            d.line([(70, 95), (86, 130)], fill=hex_to_rgb("#8C6D46"), width=3)
            d.rectangle([(82, 122), (96, 136)], fill=hex_to_rgb(COLORS["builder"]), outline=outline)
        elif tool == "boxing":
            # Red silk wrist wraps
            d.rectangle([68, 106, 78, 114], fill=ribbon_c, outline=outline)

        im.save(os.path.join(v_dir, fname))
        print(f"Generated {fname}")

    # 敌方倭寇 (A08 斥候, A09 精锐, A10 统领 BOSS) 朝左
    # A08 浪人斥候 (128x192, 朝左, 识别色 #9F7AEA)
    im_scout = Image.new("RGBA", (128, 192), (0, 0, 0, 0))
    d_s = ImageDraw.Draw(im_scout)
    violet_c = hex_to_rgb(COLORS["scout"])
    # Cloak / Body
    d_s.polygon([(40, 80), (86, 70), (92, 150), (32, 150)], fill=hex_to_rgb("#2D3748"), outline=outline, width=2)
    d_s.rectangle([48, 120, 80, 128], fill=violet_c, outline=outline)
    # Head facing left
    d_s.ellipse([46, 44, 74, 72], fill=hex_to_rgb(COLORS["skin"]), outline=outline)
    # Bare feet (facing left)
    d_s.polygon([(34, 180), (54, 180), (54, 186), (34, 186)], fill=hex_to_rgb(COLORS["skin"]))
    d_s.polygon([(54, 180), (74, 180), (74, 186), (54, 186)], fill=hex_to_rgb(COLORS["skin"]))
    # Thin katana pointing down-left
    d_s.line([(42, 110), (18, 160)], fill=hex_to_rgb(COLORS["stone_road"]), width=2)
    im_scout.save(os.path.join(e_dir, "enemy_scout_01.png"))

    # A09 倭刀精锐 (128x192, 朝左, 恶鬼面, 识别色 #C53030)
    im_sam = Image.new("RGBA", (128, 192), (0, 0, 0, 0))
    d_sam = ImageDraw.Draw(im_sam)
    d_sam.polygon([(38, 76), (88, 76), (90, 140), (36, 140)], fill=hex_to_rgb(COLORS["samurai"]), outline=outline, width=2)
    # Katana
    d_sam.line([(40, 95), (14, 170)], fill=hex_to_rgb(COLORS["text_main"]), width=3)
    im_sam.save(os.path.join(e_dir, "enemy_samurai_01.png"))

    # A10 倭酋统领 BOSS (192x256, 阵羽织+角盔, 朝左, 识别色 #742A2A)
    im_boss = Image.new("RGBA", (192, 256), (0, 0, 0, 0))
    d_b = ImageDraw.Draw(im_boss)
    boss_c = hex_to_rgb(COLORS["boss"])
    d_b.polygon([(46, 80), (146, 80), (154, 210), (38, 210)], fill=boss_c, outline=outline, width=3)
    # Horned helmet
    d_b.ellipse([68, 44, 124, 100], fill=hex_to_rgb(COLORS["panel_bg"]), outline=outline)
    d_b.polygon([(68, 50), (46, 16), (82, 38)], fill=hex_to_rgb(COLORS["gold_bright"]), outline=outline)
    d_b.polygon([(124, 50), (146, 16), (110, 38)], fill=hex_to_rgb(COLORS["gold_bright"]), outline=outline)
    # Dual swords
    d_b.line([(50, 140), (18, 220)], fill=hex_to_rgb(COLORS["text_main"]), width=4)
    d_b.line([(130, 140), (160, 220)], fill=hex_to_rgb(COLORS["text_main"]), width=4)
    im_boss.save(os.path.join(e_dir, "enemy_boss_01.png"))
    print("Generated all enemy sprites.")

if __name__ == "__main__":
    print("Generating comprehensive game art assets according to Art Bible...")
    generate_backgrounds()
    generate_ui()
    generate_icons()
    generate_tools_and_props()
    generate_vfx_and_projectiles()
    generate_landmarks()
    generate_unit_sprites()
    print("ALL ASSETS SUCCESSFULLY GENERATED!")
