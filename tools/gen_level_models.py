# -*- coding: utf-8 -*-
"""逐级建模：为「每一次升级都换一座独立的楼」补齐等级美术。

设计约定
- 输出 `assets/buildings/<name>.png`（1x 设计稿）+ `<name>@2x.png`（2 倍主稿，主稿才是原生分辨率）。
- 贴图一律底边对齐（游戏里按 `padBottom` 落在地平线上），所以「长高」= 画布向上扩，
  基座像素行不动，地面线自然保持不动。
- 建筑升级：以现有等级图作底，往上叠一层楼 / 加一圈雉堞，颜色从底图取样，保证同一栋楼。
- 地形升级（水田 / 盐田）：荒地另画，熟田 = 上一级 + 田埂 / 水光 / 盐堆 / 稻浪。
- 已存在的文件跳过，不会覆盖美术同学重画的稿子；`--force` 可强制重生成。

用法：python tools/gen_level_models.py [--force]
"""

import argparse
import os
import random

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BD = os.path.join(ROOT, 'assets', 'buildings')
BG = os.path.join(ROOT, 'assets', 'bg')
S = 2  # 原生工作分辨率倍数：先按 2x 画，再缩一半得到 1x 设计稿

OUTLINE = (26, 32, 44, 255)
GOLD = (214, 180, 92, 255)

random.seed(20240501)


# --------------------------------------------------------------------------- 工具

def path_of(name, folder=BD):
    return os.path.join(folder, name + '.png')


def load(*parts):
    return Image.open(os.path.join(ROOT, *parts)).convert('RGBA')


def tint(color, k=1.0, add=0):
    return tuple(max(0, min(255, int(c * k + add))) for c in color[:3]) + (255,)


def avg_color(arr, box):
    """取样一块区域里不透明像素的平均色。"""
    x0, y0, x1, y1 = [int(v) for v in box]
    sub = arr[max(0, y0):max(1, y1), max(0, x0):max(1, x1)]
    if sub.size == 0:
        return (128, 128, 128)
    m = sub[..., 3] > 60
    if not m.any():
        return (128, 128, 128)
    return tuple(int(v) for v in sub[m][: :3].mean(0))


def alpha_bbox(im):
    a = np.array(im)
    ys, xs = np.where(a[..., 3] > 10)
    if len(xs) == 0:
        return (0, 0, im.size[0], im.size[1])
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def poly(d, pts, fill, outline=OUTLINE, width=4):
    pts = [(int(round(x)), int(round(y))) for x, y in pts]
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=outline, width=width, joint='curve')


def save_pair(im, name, folder=BD):
    """写 2x 原生主稿 + 1x 设计稿（1x = 主稿等比缩一半，绝不放大）。"""
    if not os.path.isdir(folder):
        os.makedirs(folder)
    w, h = im.size
    im.save(path_of(name + '@2x', folder))
    one = im.resize((max(1, w // 2), max(1, h // 2)), Image.LANCZOS)
    one.save(path_of(name, folder))
    print('  生成 %-28s 1x=%-11s @2x=%s' % (name, one.size, im.size))


def exists(name, folder=BD):
    return os.path.exists(path_of(name, folder))


# --------------------------------------------------------------- 建筑：往上长一层

def stack_floor(d, cx0, cx1, y_base, fh, roof_c, wall_c, gold=True):
    """在 y_base（1x 像素，已乘 S）之上盖一层：墙身 + 飞檐。"""
    body_h = fh * 0.52
    eave = (cx1 - cx0) * 0.11
    x0, x1 = cx0 + (cx1 - cx0) * 0.05, cx1 - (cx1 - cx0) * 0.05
    wy0 = y_base - body_h
    d.rectangle([x0, wy0, x1, y_base], fill=tint(wall_c, 0.94), outline=OUTLINE, width=4)
    # 墙身木柱
    for fx in (0.18, 0.82):
        px = x0 + (x1 - x0) * fx
        d.line([(px, wy0 + 3), (px, y_base - 3)], fill=tint(wall_c, 0.7), width=3)
    # 飞檐
    ry1 = wy0
    ry0 = wy0 - fh * 0.44
    poly(
        d,
        [
            (x0 - eave, ry1),
            (x1 + eave, ry1),
            (x1 + eave * 0.5, ry0),
            (x0 - eave * 0.5, ry0),
        ],
        tint(roof_c, 1.02),
        width=4,
    )
    # 瓦垄
    n = 7
    for i in range(1, n):
        fx = i / float(n)
        tx = (x0 - eave) + (x1 + eave - (x0 - eave)) * fx
        d.line(
            [(tx, ry1 - 2), (tx - eave * 0.5 * (fx - 0.0) / 1.0, ry0 + 3)],
            fill=tint(roof_c, 0.78),
            width=2,
        )
    if gold:
        d.line(
            [(x0 - eave * 0.5, ry0 + 3), (x1 + eave * 0.5, ry0 + 3)], fill=GOLD, width=3
        )
    # 窗
    ww = (x1 - x0) * 0.16
    wyc = wy0 + body_h * 0.30
    for fx in (0.30, 0.70):
        px = x0 + (x1 - x0) * fx
        d.rectangle(
            [px - ww / 2, wyc, px + ww / 2, wyc + body_h * 0.34],
            fill=(64, 60, 56, 255),
            outline=OUTLINE,
            width=3,
        )
    return ry0


def extend_upwards(base_name, floors, out_name, floor_ratio=0.26):
    base = load('assets', 'buildings', base_name + '.png')
    W0, H0 = base.size
    bx0, by0, bx1, by1 = alpha_bbox(base)
    a0 = np.array(base)
    mid = by0 + (by1 - by0) // 2
    roof_c = avg_color(a0, (bx0, by0, bx1, mid))
    wall_c = avg_color(a0, (bx0, mid, bx1, by1))

    fh = floor_ratio * H0  # 每层高度（1x 单位）
    extra = int(round(floors * fh))
    new_h = H0 + extra

    W, H = W0 * S, new_h * S
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    off = extra * S
    cv.paste(base.resize((W0 * S, H0 * S), Image.LANCZOS), (0, off))
    d = ImageDraw.Draw(cv)

    # 从底图顶端往上叠，每层压进下一层 0.18 层高，看着像从屋顶长出来
    for i in range(floors):
        yb = off + (by0 + 0.18 * fh - i * fh) * S
        stack_floor(
            d,
            bx0 * S,
            bx1 * S,
            yb,
            fh * S,
            roof_c,
            wall_c,
            gold=(i == floors - 1),
        )

    # 顶层加一面小旗，旗帜越高说明等级越高
    top_y = off + (by0 + 0.18 * fh - (floors - 1) * fh - fh * 0.44) * S
    flag_x = (bx0 + bx1) / 2.0 * S
    d.line([(flag_x, top_y), (flag_x, top_y - 0.07 * H0 * S)], fill=(96, 72, 50, 255), width=4)
    poly(
        d,
        [
            (flag_x, top_y - 0.07 * H0 * S),
            (flag_x + 0.09 * W0 * S, top_y - 0.055 * H0 * S),
            (flag_x, top_y - 0.038 * H0 * S),
        ],
        (178, 58, 48, 255),
        width=3,
    )
    save_pair(cv, out_name)


def extend_battlements(base_name, tiers, out_name):
    """城墙 / 瓮城升级：往上加一圈带雉堞的城墙，不动基座。"""
    base = load('assets', 'buildings', base_name + '.png')
    W0, H0 = base.size
    bx0, by0, bx1, by1 = alpha_bbox(base)
    a0 = np.array(base)
    mid = by0 + (by1 - by0) // 2
    wall_c = avg_color(a0, (bx0, by0 + (by1 - by0) // 4, bx1, by1))
    roof_c = avg_color(a0, (bx0, by0, bx1, mid))
    stone = tint(wall_c, 1.06, 8)

    tier_h = 0.17 * H0
    extra = int(round(tiers * tier_h))
    new_h = H0 + extra
    W, H = W0 * S, new_h * S
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    off = extra * S
    cv.paste(base.resize((W0 * S, H0 * S), Image.LANCZOS), (0, off))
    d = ImageDraw.Draw(cv)

    cw = (bx1 - bx0) / float(tiers + 1)
    for i in range(tiers):
        # 每加一级，城墙往两边各长一点
        grow = 0.06 * (bx1 - bx0) * (i + 1)
        x0 = (bx0 - grow) * S
        x1 = (bx1 + grow) * S
        yb = off + (by0 + 0.10 * tier_h - i * tier_h) * S
        yt = yb - tier_h * S
        d.rectangle([x0, yt, x1, yb], fill=stone, outline=OUTLINE, width=4)
        # 砖缝
        for k in range(1, 6):
            yy = yt + (yb - yt) * k / 6.0
            d.line([(x0 + 4, yy), (x1 - 4, yy)], fill=tint(wall_c, 0.86), width=2)
        # 雉堞
        n = max(4, int((x1 - x0) / (14 * S)))
        step = (x1 - x0) / float(n)
        for k in range(n):
            if k % 2:
                continue
            d.rectangle(
                [x0 + k * step, yt - 0.035 * H0 * S, x0 + (k + 0.62) * step, yt],
                fill=tint(stone, 1.04),
                outline=OUTLINE,
                width=3,
            )
        # 顶部压边
        d.line([(x0, yt), (x1, yt)], fill=tint(roof_c, 0.9), width=4)

    # 中军楼：顶上一层带旗
    top = off + (by0 + 0.10 * tier_h - (tiers - 1) * tier_h - tier_h) * S
    mx = (bx0 + bx1) / 2.0 * S
    mw = cw * 0.42 * S
    d.rectangle([mx - mw / 2, top, mx + mw / 2, top + tier_h * 0.55 * S], fill=tint(stone, 1.02), outline=OUTLINE, width=4)
    poly(
        d,
        [
            (mx - mw * 0.72, top),
            (mx + mw * 0.72, top),
            (mx + mw * 0.34, top - 0.07 * H0 * S),
            (mx - mw * 0.34, top - 0.07 * H0 * S),
        ],
        tint(roof_c, 0.92),
        width=4,
    )
    d.line([(mx, top - 0.07 * H0 * S), (mx, top - 0.15 * H0 * S)], fill=(96, 72, 50, 255), width=4)
    poly(
        d,
        [(mx, top - 0.15 * H0 * S), (mx + mw * 0.6, top - 0.125 * H0 * S), (mx, top - 0.10 * H0 * S)],
        (178, 58, 48, 255),
        width=3,
    )
    save_pair(cv, out_name)


# ------------------------------------------------------------- 地形：荒地 / 熟田

def paint_scrub(d, x0, y0, x1, y1, n=60, seed=1):
    rnd = random.Random(seed)
    for _ in range(n):
        x = rnd.uniform(x0, x1)
        y = rnd.uniform(y0, y1)
        w = rnd.uniform(3, 14) * S / 2.0
        h = rnd.uniform(2, 7) * S / 2.0
        c = rnd.choice([(96, 78, 58), (72, 62, 46), (118, 96, 66), (86, 88, 52)])
        d.ellipse([x, y, x + w, y + h], fill=c + (255,))


def paint_stones(d, x0, y0, x1, y1, n=14, seed=2):
    rnd = random.Random(seed)
    for _ in range(n):
        x = rnd.uniform(x0, x1)
        y = rnd.uniform(y0, y1)
        r = rnd.uniform(2.2, 5.4) * S
        c = rnd.choice([(146, 142, 134), (122, 118, 112), (168, 164, 156)])
        d.ellipse([x - r, y - r * 0.62, x + r, y + r * 0.62], fill=c + (255,), outline=OUTLINE, width=3)


def paint_weeds(d, x0, y0, x1, y1, n=30, seed=3):
    rnd = random.Random(seed)
    for _ in range(n):
        x = rnd.uniform(x0, x1)
        y = rnd.uniform(y0, y1)
        h = rnd.uniform(5, 13) * S
        c = rnd.choice([(124, 118, 62), (150, 140, 80), (104, 104, 56)])
        d.line([(x, y), (x - h * 0.25, y - h)], fill=c + (255,), width=max(2, S))
        d.line([(x, y), (x + h * 0.3, y - h * 0.8)], fill=c + (255,), width=max(2, S))


def gen_paddy_plot(out_name, W0=440, H0=88):
    """荒芜水田（未开垦）：一片干裂的土地 + 碎石杂草。"""
    W, H = W0 * S, H0 * S
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    x0, x1 = 4 * S, (W0 - 5) * S
    y0, y1 = 16 * S, (H0 - 6) * S
    d.rounded_rectangle([x0, y0, x1, y1], radius=10 * S, fill=(104, 84, 62, 255), outline=OUTLINE, width=4)
    # 土色分层
    d.rectangle([x0 + 3, y0 + 3, x1 - 3, y0 + (y1 - y0) * 0.42], fill=(118, 96, 70, 255))
    paint_scrub(d, x0, y0, x1, y1, 90, 11)
    paint_stones(d, x0, y0 + 6 * S, x1, y1, 18, 12)
    paint_weeds(d, x0, y0, x1, y1 - 6 * S, 26, 13)
    # 干裂纹
    rnd = random.Random(14)
    for _ in range(9):
        x = rnd.uniform(x0 + 20 * S, x1 - 20 * S)
        y = rnd.uniform(y0 + 8 * S, y1 - 8 * S)
        d.line(
            [(x, y), (x + rnd.uniform(-30, 30) * S, y + rnd.uniform(-9, 9) * S)],
            fill=(74, 60, 44, 255),
            width=3,
        )
    save_pair(cv, out_name)


def gen_paddy_tier(base_name, out_name, level):
    """熟田升级：以 lv1 作底，叠田埂 / 水光 / 石岸（lv2）与金黄稻浪（lv3）。"""
    W0, H0 = (440, 88)
    base = load('assets', 'buildings', base_name + '.png').resize((W0 * S, H0 * S), Image.LANCZOS)
    cv = base.copy()
    d = ImageDraw.Draw(cv)
    x0, x1 = 6 * S, (W0 - 6) * S
    ytop, ybot = 20 * S, (H0 - 8) * S

    # 石砌田岸（加固）
    d.rounded_rectangle(
        [x0, ybot - 7 * S, x1, ybot + 4 * S],
        radius=4 * S,
        fill=(146, 142, 134, 255),
        outline=OUTLINE,
        width=4,
    )
    for i in range(1, 16):
        bx = x0 + (x1 - x0) * i / 16.0
        d.line([(bx, ybot - 6 * S), (bx, ybot + 3 * S)], fill=(116, 112, 106, 255), width=3)

    # 田埂：横竖分割出规整田块
    n = 8 if level >= 3 else 6
    for i in range(1, n):
        bx = x0 + (x1 - x0) * i / float(n)
        d.line([(bx, ytop), (bx, ybot - 7 * S)], fill=(92, 76, 52, 255), width=5)
    for fy in (0.42, 0.74):
        yy = ytop + (ybot - 7 * S - ytop) * fy
        d.line([(x0, yy), (x1, yy)], fill=(92, 76, 52, 255), width=4)

    # 水光
    for i in range(n):
        bx = x0 + (x1 - x0) * i / float(n)
        bw = (x1 - x0) / float(n)
        yy = ytop + (ybot - 7 * S - ytop) * 0.55
        d.rectangle([bx + 5 * S, yy, bx + bw - 5 * S, yy + 6 * S], fill=(150, 180, 186, 150))
        d.rectangle([bx + 8 * S, yy + 10 * S, bx + bw * 0.55, yy + 13 * S], fill=(150, 180, 186, 110))

    if level >= 3:
        # 金黄稻浪：熟田才有的收成色
        rnd = random.Random(31)
        for i in range(n):
            bx = x0 + (x1 - x0) * i / float(n)
            bw = (x1 - x0) / float(n)
            for k in range(9):
                yy = ytop + 4 * S + (ybot - 16 * S - ytop) * k / 9.0
                d.line(
                    [
                        (bx + 6 * S, yy + rnd.uniform(-2, 2) * S),
                        (bx + bw - 6 * S, yy + rnd.uniform(-2, 2) * S),
                    ],
                    fill=(200, 172, 92, 205),
                    width=max(3, 2 * S),
                )
        # 田头稻草人 + 谷捆
        sx = x0 + 26 * S
        d.line([(sx, ybot - 8 * S), (sx, ybot - 52 * S)], fill=(104, 78, 52, 255), width=5)
        d.line([(sx - 16 * S, ybot - 40 * S), (sx + 16 * S, ybot - 40 * S)], fill=(104, 78, 52, 255), width=5)
        d.ellipse([sx - 10 * S, ybot - 62 * S, sx + 10 * S, ybot - 44 * S], fill=(196, 168, 96, 255), outline=OUTLINE, width=3)
        for j, gx in enumerate((x1 - 30 * S, x1 - 62 * S)):
            d.ellipse([gx - 12 * S, ybot - 26 * S - j * 4 * S, gx + 12 * S, ybot - 6 * S], fill=(206, 178, 98, 255), outline=OUTLINE, width=3)
        d.line([(x0, ybot - 9 * S), (x1, ybot - 9 * S)], fill=GOLD, width=3)
    save_pair(cv, out_name)


def gen_salt_plot(out_name, W0=1120, H0=120):
    """盐碱荒地（未开垦）：灰褐滩涂 + 盐霜斑块 + 碎石枯苇。"""
    W, H = W0 * S, H0 * S
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    x0, x1 = 0, W - 1
    y0, y1 = 20 * S, (H0 - 1) * S
    d.rounded_rectangle([x0 + 2 * S, y0, x1 - 2 * S, y1], radius=8 * S, fill=(122, 110, 94, 255), outline=OUTLINE, width=4)
    d.rectangle([x0 + 4 * S, y0 + 4 * S, x1 - 4 * S, y0 + (y1 - y0) * 0.35], fill=(138, 126, 108, 255))
    paint_scrub(d, x0, y0, x1, y1, 200, 21)
    paint_stones(d, x0, y0 + 8 * S, x1, y1, 34, 22)
    paint_weeds(d, x0, y0, x1, y1 - 8 * S, 40, 23)
    # 盐霜斑块
    rnd = random.Random(24)
    for _ in range(26):
        cx = rnd.uniform(x0 + 30 * S, x1 - 30 * S)
        cy = rnd.uniform(y0 + 14 * S, y1 - 6 * S)
        rw = rnd.uniform(16, 54) * S / 2.0
        rh = rnd.uniform(5, 13) * S / 2.0
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(206, 204, 198, 185))
    save_pair(cv, out_name)


def gen_salt_tier(base_name, out_name, level, folder=BG, out_folder=BD):
    """盐田升级：以 lv1 作底，叠卤水分畦 / 盐堆（lv2）与盐仓晒架（lv3）。"""
    W0, H0 = (1120, 120)
    src = os.path.relpath(os.path.join(folder, base_name + '.png'), ROOT).replace('\\', '/')
    base = load(*src.split('/')).resize((W0 * S, H0 * S), Image.LANCZOS)
    cv = base.copy()
    d = ImageDraw.Draw(cv)
    x0, x1 = 4 * S, W0 * S - 4 * S
    ytop, ybot = 26 * S, (H0 - 3) * S

    # 卤水塘
    n = 9 if level >= 3 else 6
    for i in range(1, n):
        bx = x0 + (x1 - x0) * i / float(n)
        d.line([(bx, ytop), (bx, ybot)], fill=(96, 84, 68, 255), width=4)
    for fy in (0.55, 0.86):
        yy = ytop + (ybot - ytop) * fy
        d.line([(x0, yy), (x1, yy)], fill=(96, 84, 68, 255), width=4)
    for i in range(n):
        bx = x0 + (x1 - x0) * i / float(n)
        bw = (x1 - x0) / float(n)
        d.rectangle([bx + 6 * S, ytop + 6 * S, bx + bw - 6 * S, ytop + 22 * S], fill=(152, 176, 186, 170))
        d.rectangle([bx + 10 * S, ytop + 28 * S, bx + bw * 0.6, ytop + 36 * S], fill=(152, 176, 186, 120))

    # 盐堆：白花花的收成
    rnd = random.Random(41)
    piles = 7 if level >= 3 else 4
    for i in range(piles):
        cx = x0 + (x1 - x0) * (i + 0.5) / float(piles)
        rw = rnd.uniform(26, 42) * S / 2.0
        rh = rnd.uniform(20, 30) * S / 2.0
        poly(
            d,
            [(cx - rw, ybot), (cx + rw, ybot), (cx + rw * 0.45, ybot - rh), (cx - rw * 0.45, ybot - rh)],
            (236, 236, 232, 255),
            width=3,
        )
        d.line([(cx - rw * 0.35, ybot - rh * 0.35), (cx + rw * 0.35, ybot - rh * 0.35)], fill=(206, 206, 200, 255), width=3)

    if level >= 3:
        # 盐仓（木架草顶小棚）
        hx = x0 + 60 * S
        d.rectangle([hx - 46 * S, ybot - 62 * S, hx + 46 * S, ybot], fill=(206, 200, 186, 255), outline=OUTLINE, width=4)
        poly(
            d,
            [(hx - 60 * S, ybot - 62 * S), (hx + 60 * S, ybot - 62 * S), (hx + 40 * S, ybot - 88 * S), (hx - 40 * S, ybot - 88 * S)],
            (150, 124, 74, 255),
            width=4,
        )
        d.rectangle([hx - 42 * S, ybot - 24 * S, hx + 42 * S, ybot], fill=(94, 66, 44, 255), outline=OUTLINE, width=3)
        # 晒盐竹架
        rx = x1 - 190 * S
        for j in range(3):
            bx = rx + j * 60 * S
            d.line([(bx, ybot), (bx, ybot - 54 * S)], fill=(120, 92, 60, 255), width=4)
            d.line([(bx - 24 * S, ybot - 46 * S), (bx + 24 * S, ybot - 46 * S)], fill=(140, 112, 74, 255), width=4)
        d.line([(rx - 30 * S, ybot - 54 * S), (rx + 150 * S, ybot - 54 * S)], fill=(200, 198, 192, 255), width=4)
        d.line([(x0, ybot - 2 * S), (x1, ybot - 2 * S)], fill=GOLD, width=3)
    save_pair(cv, out_name, out_folder)


# ------------------------------------------------------------------ 民居：每级一座

# ------------------------------------------------------- 民居：浙南白墙黛瓦（重画）
# 画布纵向必须占满：贴图底边贴地，高度就是视觉身高（见 Assets.ts 的 PERSON_TARGET）。

C_PLASTER_T = (240, 235, 223, 255)
C_PLASTER_B = (216, 208, 192, 255)
C_STAIN = (198, 190, 174, 255)
C_TIMBER = (126, 90, 56, 255)
C_TIMBER_D = (84, 58, 34, 255)
C_TILE = (62, 70, 84, 255)
C_TILE_D = (40, 46, 58, 255)
C_TILE_L = (108, 120, 138, 255)
C_STONE = (152, 148, 140, 255)
C_STONE_D = (114, 110, 104, 255)
C_STONE_L = (182, 178, 170, 255)
C_THATCH = (172, 144, 90, 255)
C_THATCH_D = (126, 100, 56, 255)
C_THATCH_L = (210, 186, 130, 255)
C_RED = (148, 54, 44, 255)
C_RED_D = (108, 34, 28, 255)
C_SHADOW = (26, 22, 18, 62)


def _h_grad(d, box, c_top, c_bot):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    n = max(1, y1 - y0)
    for i in range(n):
        t = i / float(n)
        c = tuple(int(c_top[k] + (c_bot[k] - c_top[k]) * t) for k in range(3)) + (255,)
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c)


def _h_plaster(d, box, seed=1):
    """白粉墙：竖向渐变 + 斑驳污渍 + 描边。"""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    _h_grad(d, box, C_PLASTER_T, C_PLASTER_B)
    rnd = random.Random(seed)
    n = int((x1 - x0) * (y1 - y0) / 2200) + 4
    for _ in range(n):
        px = rnd.uniform(x0 + 4, x1 - 4)
        py = rnd.uniform(y0 + 5, y1 - 5)
        rw = rnd.uniform(3, 10) * S / 2.0
        rh = rnd.uniform(2, 6) * S / 2.0
        d.ellipse([px - rw, py - rh, px + rw, py + rh], fill=C_STAIN)
    # 勒脚（墙根湿痕）
    d.rectangle([x0, y1 - 6 * S / 2.0, x1, y1], fill=(176, 170, 156, 255))
    d.rectangle([x0, y0, x1, y1], outline=OUTLINE, width=4)


def _h_stone_base(d, cx, y_base, half_w, h, steps=True):
    """台基：石条 + 压顶 + 石板缝 + 台阶。"""
    x0, x1 = cx - half_w, cx + half_w
    yt = y_base - h
    d.polygon([(x0 - 4, y_base), (x1 + 4, y_base), (x1 + 4, yt), (x0 - 4, yt)], fill=C_STONE)
    d.line([(x0 - 4, yt), (x1 + 4, yt)], fill=C_STONE_L, width=4)
    d.line([(x0 - 4, y_base - 3), (x1 + 4, y_base - 3)], fill=C_STONE_D, width=3)
    for i in range(1, 6):
        bx = x0 - 4 + (x1 - x0 + 8) * i / 6.0
        d.line([(bx, yt + 3), (bx, y_base - 3)], fill=C_STONE_D, width=3)
    d.line([(x0 - 4, yt + h * 0.5), (x1 + 4, yt + h * 0.5)], fill=C_STONE_D, width=2)
    d.rectangle([x0 - 4, yt, x1 + 4, y_base], outline=OUTLINE, width=4)
    if steps:
        sw = half_w * 0.36
        d.rectangle([cx - sw, y_base - h * 0.45, cx + sw, y_base + 2], fill=C_STONE_L, outline=OUTLINE, width=3)
        d.line([(cx - sw + 4, y_base - h * 0.45), (cx - sw + 4, y_base)], fill=C_STONE_D, width=2)


def _h_lr(xl_t, xr_t, xl_b, xr_b, y_t, y_b):
    """屋面梯形：给任意 y 返回左右边界。"""
    def lr(y):
        t = (y - y_t) / float(max(1.0, y_b - y_t))
        return xl_t + (xl_b - xl_t) * t, xr_t + (xr_b - xr_t) * t
    return lr


def _h_tile_roof(d, xl_t, xr_t, xl_b, xr_b, y_t, y_b, cols=9, upturn=True):
    """黛瓦屋面：梯形底 + 竖瓦垄 + 横瓦排 + 滴水檐 + 正脊 + 翘角。"""
    lr = _h_lr(xl_t, xr_t, xl_b, xr_b, y_t, y_b)
    for y in range(int(y_t), int(y_b) + 1):
        x0, x1 = lr(y)
        d.line([(x0, y), (x1, y)], fill=C_TILE)
    for i in range(cols + 1):
        f = i / float(cols)
        cc = C_TILE_D if i % 2 == 0 else C_TILE_L
        xa = xl_t + (xr_t - xl_t) * f
        xb = xl_b + (xr_b - xl_b) * f
        d.line([(xa, y_t + 2), (xb, y_b)], fill=cc, width=2)
    for r in range(1, 5):
        y = y_t + (y_b - y_t) * r / 5.0
        x0, x1 = lr(y)
        d.line([(x0, y), (x1, y)], fill=C_TILE_D, width=2)
    # 檐口滴水
    x0, x1 = lr(y_b)
    d.line([(x0, y_b), (x1, y_b)], fill=C_TILE_L, width=5)
    d.line([(x0, y_b + 4), (x1, y_b + 4)], fill=C_TILE_D, width=4)
    if upturn:
        for sgn, x in ((-1, x0), (1, x1)):
            poly(d, [(x, y_b + 2), (x + sgn * 7 * S, y_b - 8 * S), (x + sgn * 1 * S, y_b - 4)], C_TILE, width=3)
    # 正脊
    xa, xb = lr(y_t + 1)
    d.line([(xa - 4, y_t), (xb + 4, y_t)], fill=C_TILE_L, width=7)
    d.line([(xa - 4, y_t - 5), (xb + 4, y_t - 5)], fill=C_TILE_D, width=3)
    for sgn, x in ((-1, xa), (1, xb)):
        d.rectangle([x - 3 * S, y_t - 12, x + 3 * S, y_t - 2], fill=C_TILE_D)


def _h_thatch_roof(d, xl_t, xr_t, xl_b, xr_b, y_t, y_b, seed=7):
    """茅草顶：梯形底 + 细草茎 + 压脊草绳。"""
    lr = _h_lr(xl_t, xr_t, xl_b, xr_b, y_t, y_b)
    for y in range(int(y_t), int(y_b) + 1):
        x0, x1 = lr(y)
        t = (y - y_t) / float(max(1.0, y_b - y_t))
        c = tuple(int(C_THATCH_D[k] + (C_THATCH[k] - C_THATCH_D[k]) * (1 - t * 0.5)) for k in range(3)) + (255,)
        d.line([(x0, y), (x1, y)], fill=c)
    rnd = random.Random(seed)
    for _ in range(120):
        y = rnd.uniform(y_t + 3, y_b - 2)
        x0, x1 = lr(y)
        if x1 - x0 < 6:
            continue
        x = rnd.uniform(x0 + 2, x1 - 2)
        d.line([(x, y), (x + rnd.uniform(-4, 4) * S / 2.0, min(y + rnd.uniform(8, 26), y_b))],
               fill=C_THATCH_L if rnd.random() < 0.45 else C_THATCH_D, width=2)
    # 檐口
    x0, x1 = lr(y_b)
    d.line([(x0, y_b), (x1, y_b)], fill=C_THATCH_D, width=7)
    d.line([(x0 + 3, y_b + 3), (x1 - 3, y_b + 3)], fill=C_THATCH_L, width=3)
    # 压脊（草绳 + 木压条）
    xa, xb = lr(y_t + 2)
    d.line([(xa - 3, y_t), (xb + 3, y_t)], fill=C_THATCH_L, width=8)
    for i in range(6):
        px = xa + (xb - xa) * (i + 1) / 7.0
        d.line([(px, y_t - 4), (px, y_t + 5)], fill=C_THATCH_D, width=3)
    d.line([(xa - 6, y_t - 4), (xb + 6, y_t - 4)], fill=C_TIMBER_D, width=4)


def _h_lattice(d, cx, cy, w, h, cols=3, rows=2, dark=False):
    """木格窗（含窗台）。"""
    x0, y0, x1, y1 = cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0
    d.rectangle([x0, y0, x1, y1], fill=(48, 46, 42, 255) if dark else (86, 82, 74, 255))
    for i in range(1, cols):
        bx = x0 + w * i / cols
        d.line([(bx, y0 + 2), (bx, y1 - 2)], fill=C_TIMBER, width=3)
    for i in range(1, rows):
        by = y0 + h * i / rows
        d.line([(x0 + 2, by), (x1 - 2, by)], fill=C_TIMBER, width=3)
    d.rectangle([x0, y0, x1, y1], outline=OUTLINE, width=3)
    d.rectangle([x0 - 5, y1 + 1, x1 + 5, y1 + 7], fill=C_STONE_L, outline=OUTLINE, width=2)


def _h_door(d, cx, y_bottom, w, h, red=False, threshold=True):
    """木门 / 大门（含门槛、门簪、门环）。"""
    x0, y0, x1, y1 = cx - w / 2.0, y_bottom - h, cx + w / 2.0, y_bottom
    body = C_RED if red else (112, 80, 50, 255)
    d.rectangle([x0, y0, x1, y1], fill=body, outline=OUTLINE, width=4)
    d.line([(cx, y0 + 2), (cx, y1)], fill=C_RED_D if red else C_TIMBER_D, width=3)
    for sx in (x0 + 5, x1 - 5):
        d.line([(sx, y0 + 3), (sx, y1 - 3)], fill=C_TIMBER_D, width=2)
    if red:
        for py in (y0 + h * 0.26, y0 + h * 0.5, y0 + h * 0.74):
            for px in (cx - w * 0.22, cx + w * 0.22):
                d.ellipse([px - 3 * S / 2.0, py - 3 * S / 2.0, px + 3 * S / 2.0, py + 3 * S / 2.0], fill=GOLD)
        for px in (cx - w * 0.3, cx + w * 0.3):
            d.ellipse([px - 4 * S, y0 + h * 0.42, px + 4 * S, y0 + h * 0.46], outline=GOLD, width=3)
    else:
        d.ellipse([cx + w * 0.24 - 5 * S, y1 - h * 0.42, cx + w * 0.24 + 5 * S, y1 - h * 0.42 + 5 * S],
                  outline=GOLD, width=3)
    if threshold:
        d.rectangle([x0 - 6, y1 - 4, x1 + 6, y1 + 6], fill=C_STONE_L, outline=OUTLINE, width=3)
    # 门楣
    d.rectangle([x0 - 8, y0 - 8, x1 + 8, y0], fill=C_TIMBER, outline=OUTLINE, width=3)


def _h_lantern(d, cx, y_top, r, rope=10):
    d.line([(cx, y_top - rope), (cx, y_top)], fill=(78, 56, 38, 255), width=3)
    d.ellipse([cx - r, y_top, cx + r, y_top + r * 2.1], fill=(198, 74, 60, 255), outline=OUTLINE, width=3)
    d.line([(cx - r * 0.7, y_top + r * 0.5), (cx + r * 0.7, y_top + r * 0.5)], fill=(226, 150, 120, 255), width=2)
    d.line([(cx, y_top + r * 2.1), (cx, y_top + r * 2.1 + 5)], fill=(198, 74, 60, 255), width=3)


def _h_eave_shadow(d, x0, y0, x1, h):
    """檐下阴影：贴在墙上一条，给屋面一点厚度感。"""
    d.rectangle([x0, y0, x1, y0 + h], fill=C_SHADOW)


def gen_house_plot(out_name, W0=120, H0=70):
    """空地：夯土台 + 放线木桩，等着盖房。"""
    W, H = W0 * S, H0 * S
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    x0, x1 = 10 * S, (W0 - 10) * S
    y1 = H
    y0 = y1 - 26 * S
    d.polygon([(x0 - 6 * S, y1), (x1 + 6 * S, y1), (x1, y0), (x0, y0)], fill=(158, 150, 136, 255))
    paint_stones(d, x0, y0, x1, y1, 12, 51)
    d.line([(x0, y0), (x1, y0)], fill=(126, 120, 110, 255), width=4)
    d.rectangle([x0, y0, x1, y1], outline=OUTLINE, width=4)
    for px in (x0 + 5 * S, x1 - 5 * S):
        d.rectangle([px - 4 * S, y0 - 26 * S, px + 4 * S, y0], fill=(126, 94, 60, 255), outline=OUTLINE, width=3)
        d.line([(px - 4 * S, y0 - 20 * S), (px + 4 * S, y0 - 16 * S)], fill=C_TIMBER_D, width=2)
    d.rectangle([x0 + 12 * S, y0 - 46 * S, x1 - 12 * S, y0], outline=(200, 196, 188, 190), width=3)
    save_pair(cv, out_name)


def gen_house_lv1(out_name, W0=150, H0=162):
    """一级：石基 + 白墙 + 木窗木门 + 茅草顶。

    门高 = 画布的 43%，配 3.0 人的屋子 → 门净高约 1.36 人：
    人从门下过要明显矮一截，不能出现「人跟门一样高」。
    """
    W, H = W0 * S, H0 * S
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    cx = W0 / 2.0 * S
    base_y = H - 1
    plinth = 15 * S
    wx0, wx1 = 20 * S, 130 * S
    wall_t = 46 * S
    wall_b = base_y - plinth
    _h_stone_base(d, cx, base_y, 62 * S, plinth)
    _h_plaster(d, [wx0, wall_t, wx1, wall_b], 11)
    # 木构架：角柱 + 中柱
    for px in (wx0 + 4, cx, wx1 - 4):
        d.line([(px, wall_t + 4), (px, wall_b - 2)], fill=C_TIMBER, width=5)
    d.line([(wx0 + 4, wall_t + 12), (wx1 - 4, wall_t + 12)], fill=C_TIMBER, width=4)
    # 门：整张图里唯一「人要穿过去」的地方，必须明显高过人
    _h_door(d, cx, wall_b, 32 * S, 70 * S)
    # 门两侧各开一扇窗（比门矮，横向上也不跟门打架）
    _h_lattice(d, cx - 47 * S, wall_b - 38 * S, 22 * S, 30 * S, 3, 3)
    _h_lattice(d, cx + 47 * S, wall_b - 38 * S, 22 * S, 30 * S, 3, 3)
    # 檐下阴影
    _h_eave_shadow(d, wx0 + 2, wall_t, wx1 - 2, 9 * S)
    # 茅草顶
    _h_thatch_roof(d, 36 * S, 114 * S, 4 * S, 146 * S, 6 * S, wall_t + 6 * S, 61)
    save_pair(cv, out_name)


def gen_house_lv2(out_name, W0=185, H0=188):
    """二级：两层瓦房，一层高门脸 + 二层挑阁，黛瓦翘角，挂灯笼。

    门高 = 画布的 43%，配 3.8 人的屋子 → 门净高约 1.7 人。
    """
    W, H = W0 * S, H0 * S
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    cx = W0 / 2.0 * S
    base_y = H - 1
    plinth = 15 * S
    wx0, wx1 = 24 * S, 161 * S
    floor_b = base_y - plinth
    floor_mid = 76 * S
    _h_stone_base(d, cx, base_y, 78 * S, plinth, steps=False)
    # 一层：门几乎顶到一层檐口，两侧配高窗
    _h_plaster(d, [wx0, floor_mid, wx1, floor_b], 21)
    _h_door(d, cx, floor_b, 40 * S, 80 * S, red=True)
    _h_lattice(d, cx - 52 * S, floor_b - 46 * S, 24 * S, 34 * S, 3, 3)
    _h_lattice(d, cx + 52 * S, floor_b - 46 * S, 24 * S, 34 * S, 3, 3)
    _h_eave_shadow(d, wx0 + 2, floor_mid, wx1 - 2, 8 * S)
    # 一层瓦檐
    _h_tile_roof(d, 52 * S, 133 * S, 10 * S, 175 * S, 60 * S, floor_mid - 2 * S, 11)
    # 二层
    up0, up1 = 47 * S, 138 * S
    up_t, up_b = 26 * S, 58 * S
    _h_plaster(d, [up0, up_t, up1, up_b], 22)
    d.line([(up0 + 4, up_t + 10), (up1 - 4, up_t + 10)], fill=C_TIMBER, width=4)
    _h_lattice(d, cx - 26 * S, up_t + 20 * S, 22 * S, 16 * S, 3, 2, dark=True)
    _h_lattice(d, cx + 26 * S, up_t + 20 * S, 22 * S, 16 * S, 3, 2, dark=True)
    # 二层栏杆
    d.rectangle([up0 - 6, up_b - 2, up1 + 6, up_b + 4], fill=C_TIMBER, outline=OUTLINE, width=3)
    for i in range(7):
        bx = up0 + (up1 - up0) * (i + 1) / 8.0
        d.line([(bx, up_b - 10), (bx, up_b)], fill=C_TIMBER, width=3)
    _h_tile_roof(d, 64 * S, 121 * S, 34 * S, 151 * S, 8 * S, up_t - 2 * S, 9)
    # 灯笼（挂在门两侧、一层檐下）
    _h_lantern(d, 62 * S, 74 * S, 6 * S, 10)
    _h_lantern(d, 123 * S, 74 * S, 6 * S, 10)
    save_pair(cv, out_name)


def gen_house_lv3(out_name, W0=230, H0=230):
    """三级：院墙 + 马头墙 + 高门正屋 + 二层阁楼（大户人家）。

    门高 = 画布的 37%，配 4.6 人的宅院 → 门净高约 1.72 人。
    """
    W, H = W0 * S, H0 * S
    cv = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    cx = W0 / 2.0 * S
    base_y = H - 1
    plinth = 14 * S
    yard_t = 176 * S
    # 院墙 + 瓦压顶
    _h_stone_base(d, cx, base_y, 105 * S, plinth, steps=False)
    _h_plaster(d, [10 * S, yard_t, 220 * S, base_y - plinth], 31)
    d.rectangle([4 * S, yard_t - 6 * S, 226 * S, yard_t + 6 * S], fill=C_TILE, outline=OUTLINE, width=3)
    d.line([(4 * S, yard_t - 6 * S), (226 * S, yard_t - 6 * S)], fill=C_TILE_L, width=3)
    # 石板院地
    for i in range(1, 9):
        bx = 10 * S + 210 * S * i / 9.0
        d.line([(bx, yard_t + 8 * S), (bx, base_y - plinth)], fill=C_STONE_D, width=2)
    # 马头墙（阶梯山墙，两侧对称）
    for sgn in (-1, 1):
        bx = cx + sgn * 92 * S
        for (yy, hw) in ((140 * S, 32 * S), (112 * S, 24 * S), (86 * S, 17 * S)):
            _h_plaster(d, [bx - hw, yy - 26 * S, bx + hw, yy], 32 + int(hw))
            d.rectangle([bx - hw - 5 * S, yy - 32 * S, bx + hw + 5 * S, yy - 24 * S], fill=C_TILE, outline=OUTLINE, width=3)
            d.line([(bx - hw - 5 * S, yy - 32 * S), (bx + hw + 5 * S, yy - 32 * S)], fill=C_TILE_L, width=3)
    # 正屋：高门 + 两侧高窗
    hall_t, hall_b = 72 * S, 178 * S
    _h_plaster(d, [36 * S, hall_t, 194 * S, hall_b], 33)
    d.line([(40 * S, hall_t + 12), (190 * S, hall_t + 12)], fill=C_TIMBER, width=4)
    _h_lattice(d, 62 * S, hall_b - 50 * S, 24 * S, 34 * S, 3, 3, dark=True)
    _h_lattice(d, 168 * S, hall_b - 50 * S, 24 * S, 34 * S, 3, 3, dark=True)
    _h_eave_shadow(d, 38 * S, hall_t, 192 * S, 8 * S)
    _h_door(d, cx, hall_b, 46 * S, 84 * S, red=True)
    _h_lantern(d, 82 * S, hall_b - 88 * S, 7 * S, 12)
    _h_lantern(d, 148 * S, hall_b - 88 * S, 7 * S, 12)
    _h_tile_roof(d, 88 * S, 142 * S, 26 * S, 204 * S, 44 * S, hall_t - 2 * S, 13)
    # 二层阁楼
    att_t, att_b = 22 * S, 42 * S
    _h_plaster(d, [92 * S, att_t, 138 * S, att_b], 34)
    d.line([(96 * S, att_t + 9), (134 * S, att_t + 9)], fill=C_TIMBER, width=4)
    _h_lattice(d, cx - 16 * S, att_t + 14 * S, 18 * S, 12 * S, 3, 2, dark=True)
    _h_lattice(d, cx + 16 * S, att_t + 14 * S, 18 * S, 12 * S, 3, 2, dark=True)
    _h_tile_roof(d, 96 * S, 134 * S, 84 * S, 146 * S, 4 * S, att_t - 2 * S, 7)
    save_pair(cv, out_name)

# ------------------------------------------------------------------------ 主流程

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='已存在的文件也重新生成')
    ap.add_argument('--only', default='', help='只生成名字含该子串的任务')
    args = ap.parse_args()

    tasks = []
    # 宗祠：lv3 / lv4 / lv5 各加一层，越往上越巍峨
    tasks.append(('b01_shrine_lv3', lambda: extend_upwards('b01_shrine_lv2', 1, 'b01_shrine_lv3')))
    tasks.append(('b01_shrine_lv4', lambda: extend_upwards('b01_shrine_lv3', 1, 'b01_shrine_lv4', 0.24)))
    tasks.append(('b01_shrine_lv5', lambda: extend_upwards('b01_shrine_lv4', 1, 'b01_shrine_lv5', 0.22)))
    # 内城水门 / 东门瓮城：加高加雉堞
    tasks.append(('b04_inner_water_gate_lv2', lambda: extend_battlements('b04_inner_water_gate', 1, 'b04_inner_water_gate_lv2')))
    tasks.append(('b04_inner_water_gate_lv3', lambda: extend_battlements('b04_inner_water_gate_lv2', 1, 'b04_inner_water_gate_lv3')))
    tasks.append(('b06_east_gate_lv2', lambda: extend_battlements('b06_east_gate_barbican', 1, 'b06_east_gate_lv2')))
    tasks.append(('b06_east_gate_lv3', lambda: extend_battlements('b06_east_gate_lv2', 1, 'b06_east_gate_lv3')))
    # 民居：空地 → 茅屋 → 瓦房 → 大宅
    tasks.append(('b12_house_plot', lambda: gen_house_plot('b12_house_plot')))
    tasks.append(('b12_house_lv1', lambda: gen_house_lv1('b12_house_lv1')))
    tasks.append(('b12_house_lv2', lambda: gen_house_lv2('b12_house_lv2')))
    tasks.append(('b12_house_lv3', lambda: gen_house_lv3('b12_house_lv3')))
    # 水田：荒地 → 熟田两级
    tasks.append(('b02_paddy_lv0', lambda: gen_paddy_plot('b02_paddy_lv0')))
    tasks.append(('b02_paddy_lv2', lambda: gen_paddy_tier('b02_paddy', 'b02_paddy_lv2', 2)))
    tasks.append(('b02_paddy_lv3', lambda: gen_paddy_tier('b02_paddy_lv2', 'b02_paddy_lv3', 3)))
    # 盐田：荒地 → 盐场两级
    tasks.append(('b10_saltflat_lv0', lambda: gen_salt_plot('b10_saltflat_lv0')))
    tasks.append(('b10_saltflat_lv2', lambda: gen_salt_tier('b10_outer_salt_flat', 'b10_saltflat_lv2', 2)))
    tasks.append(('b10_saltflat_lv3', lambda: gen_salt_tier('b10_saltflat_lv2', 'b10_saltflat_lv3', 3, folder=BD, out_folder=BD)))

    print('逐级建模：共 %d 张' % len(tasks))
    done = 0
    for name, fn in tasks:
        if args.only and args.only not in name:
            continue
        if exists(name) and not args.force:
            print('  已有 %-28s 跳过（--force 可覆盖）' % name)
            continue
        fn()
        done += 1
    print('完成：新生成 %d 张，跳过 %d 张。' % (done, len(tasks) - done))


if __name__ == '__main__':
    main()
