# -*- coding: utf-8 -*-
"""生成东西两岸的码头（木栈桥）：完好 / 被打烂 两态，各出 1x + @2x。

    python tools/gen_pier.py

锚点约定和别的建筑一样：画布底边中点 = 落脚点（水岸线），所以桩子往下扎进水里。
画布 220x150（1x），@2x 440x300。栈桥面离地约 1.4 人高，整件含灯柱约 2.2 人。
"""
import io
import os

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'buildings')
S = 2                      # 先在 2x 上画，最后缩成 1x
W1, H1 = 220, 150
W2, H2 = W1 * S, H1 * S

WOOD_D = (58, 44, 30, 255)
WOOD = (94, 72, 46, 255)
WOOD_L = (132, 104, 68, 255)
WOOD_HI = (168, 138, 94, 255)
ROPE = (176, 156, 112, 255)
CHAR = (34, 28, 24, 255)
GLOW = (246, 214, 120, 255)
OUTLINE = (30, 22, 16, 255)


def grain(im, rng, amount=9.0, seed_off=0):
    a = np.asarray(im).astype(float)
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    n = (
        np.sin(xx * 1.7 + yy * 0.9 + seed_off) * 0.5
        + np.sin(xx * 0.31 - yy * 2.3 + seed_off * 2) * 0.3
        + rng.normal(0, 1, (h, w)) * 0.6
    )
    n = n / (np.abs(n).max() + 1e-6)
    a[:, :, :3] = np.clip(a[:, :, :3] + n[:, :, None] * amount, 0, 255)
    return Image.fromarray(a.astype('uint8'))


def plank(d, x0, x1, y, th, rng, gap=4):
    """一块板：底色 + 上亮下暗 + 木纹 + 端头暗线。"""
    x0, x1, th = int(x0), int(x1), int(th)
    yy = int(y)
    yts = max(1, th // 8)
    d.rectangle([x0, yy + yts, x1, yy + th], fill=WOOD, outline=None)
    for i in range(0, x1 - x0, max(6, gap * 3)):
        c = WOOD_L if rng.random() < 0.55 else WOOD
        d.line([(x0 + i + 2, yy + yts + 1), (min(x1, x0 + i + 14), yy + th - 1)], fill=c, width=1)
    d.line([(x0, yy + yts), (x1, yy + yts)], fill=WOOD_HI, width=max(1, yts // 2))
    d.line([(x0, yy + th), (x1, yy + th)], fill=WOOD_D, width=max(1, yts // 2))
    d.line([(x0, yy + yts), (x0, yy + th)], fill=OUTLINE, width=1)
    d.line([(x1, yy + yts), (x1, yy + th)], fill=OUTLINE, width=1)


def piling(d, cx, y_top, y_bot, th, rng, water_y, broken=False):
    """一根桩：上干下湿（水下更暗更绿），可选倾斜/断裂。"""
    cx, y_top, y_bot, th = int(cx), int(y_top), int(y_bot), int(th)
    x0, x1 = cx - th // 2, cx + th // 2
    if broken:
        d.polygon(
            [(x0, y_top), (x1, y_top), (x1 - th // 3, water_y - 6 * S), (x0 - th // 3, water_y - 6 * S)],
            fill=WOOD_D,
            outline=OUTLINE,
        )
        # 断口
        d.polygon(
            [
                (x0 - th // 3, water_y - 6 * S),
                (x1 - th // 3, water_y - 6 * S),
                (x1 - th // 2, water_y - 6 * S + th // 2),
                (x0 - th // 2, water_y - 6 * S + th // 3),
            ],
            fill=(150, 122, 84, 255),
            outline=OUTLINE,
        )
        return
    d.rectangle([x0, y_top, x1, y_bot], fill=WOOD, outline=OUTLINE)
    d.line([(x0 + 2, y_top), (x0 + 2, y_bot)], fill=WOOD_L, width=2)
    d.line([(x1 - 2, y_top), (x1 - 2, y_bot)], fill=WOOD_D, width=2)
    # 水线以下：湿 + 青苔
    wy = int(water_y)
    if wy < y_bot:
        d.rectangle([x0, wy, x1, y_bot], fill=(64, 58, 42, 255))
        for i in range(6):
            py = wy + rng.random() * max(1, y_bot - wy)
            px = x0 + rng.random() * th
            d.line([(px, py), (px + 3 * S / 2, py + 2 * S / 2)], fill=(70, 92, 62, 255), width=1)
    # 木纹
    for i in range(4):
        py = y_top + (i + 0.5) * (y_bot - y_top) / 4.0
        d.line([(x0 + 3, py), (x1 - 3, py)], fill=WOOD_D, width=1)


def brace(d, x0, y0, x1, y1, th=5 * S):
    x0, y0, x1, y1, th = int(x0), int(y0), int(x1), int(y1), int(th)
    d.line([(x0, y0), (x1, y1)], fill=WOOD_D, width=th)
    d.line([(x0, y0), (x1, y1)], fill=WOOD, width=max(1, th - 3 * S))


def lantern(d, cx, cy, r):
    cx, cy, r = int(cx), int(cy), int(r)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GLOW, outline=OUTLINE)
    d.ellipse([cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45], fill=(255, 246, 208, 255))


def build(broken=False, seed=7):
    rng = np.random.default_rng(seed)
    im = Image.new('RGBA', (W2, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base = H2 - 2 * S                      # 底边（落脚点）
    deck_y = int(H2 * 0.36)                # 桥面
    water_y = base - 26 * S                # 水面（和 GameConfig.WATER.SHORE_BAND 对得上）
    x0, x1 = 10 * S, W2 - 10 * S
    # 桩
    for i, cx in enumerate(range(x0 + 12 * S, x1, (x1 - x0 - 24 * S) // 4)):
        broken_pile = broken and i == 2
        piling(d, cx, deck_y + 6 * S, base, 11 * S, rng, water_y, broken=broken_pile)
    # 斜撑
    brace(d, x0 + 12 * S, deck_y + 20 * S, x0 + 62 * S, base - 6 * S)
    brace(d, x1 - 12 * S, deck_y + 20 * S, x1 - 62 * S, base - 6 * S)
    if broken:
        brace(d, x0 + 40 * S, deck_y + 16 * S, x0 + 96 * S, base - 4 * S, 4 * S)
    # 桥面：一块块板
    n = 11
    for i in range(n):
        px0 = x0 + (x1 - x0) * i / n
        px1 = x0 + (x1 - x0) * (i + 1) / n - 2 * S
        if broken and i in (3, 7):
            continue                       # 打烂：缺两块板
        plank(d, px0, px1, deck_y, 16 * S, rng)
    if broken:
        # 断板挂在边缘
        d.polygon(
            [(x0 + 46 * S, deck_y), (x0 + 70 * S, deck_y + 2 * S), (x0 + 66 * S, deck_y + 14 * S), (x0 + 44 * S, deck_y + 10 * S)],
            fill=WOOD_D,
            outline=OUTLINE,
        )
    # 护栏 + 绳
    for rx in (x0 + 8 * S, x1 - 8 * S):
        post_h = 22 * S if not (broken and rx > x1 - 20 * S) else 12 * S
        d.rectangle([rx - 3 * S, deck_y - post_h, rx + 3 * S, deck_y], fill=WOOD_D, outline=OUTLINE)
    d.line([(x0 + 8 * S, deck_y - 18 * S), (x1 - 8 * S, deck_y - 14 * S)], fill=ROPE, width=2 * S)
    # 灯柱
    lx = x0 + 26 * S
    if not broken:
        d.rectangle([lx - 4 * S, deck_y - 46 * S, lx + 4 * S, deck_y], fill=WOOD_D, outline=OUTLINE)
        d.line([(lx + 2 * S, deck_y - 44 * S), (lx + 16 * S, deck_y - 52 * S)], fill=WOOD_D, width=3 * S)
        lantern(d, lx + 18 * S, deck_y - 52 * S, 7 * S)
    else:
        # 灯柱倒了，斜插在水里
        d.line([(lx, deck_y), (lx + 30 * S, water_y + 10 * S)], fill=WOOD_D, width=7 * S)
        lantern(d, lx + 30 * S, water_y + 12 * S, 5 * S)
    # 桶 / 缆桩
    bx = x1 - 30 * S
    if not broken:
        d.rectangle([bx - 9 * S, deck_y - 22 * S, bx + 9 * S, deck_y], fill=WOOD, outline=OUTLINE)
        d.line([(bx - 9 * S, deck_y - 14 * S), (bx + 9 * S, deck_y - 14 * S)], fill=WOOD_D, width=2 * S)
        d.line([(bx - 9 * S, deck_y - 7 * S), (bx + 9 * S, deck_y - 7 * S)], fill=WOOD_D, width=2 * S)
        d.ellipse([bx - 9 * S, deck_y - 26 * S, bx + 9 * S, deck_y - 18 * S], fill=WOOD_L, outline=OUTLINE)
    else:
        d.arc([bx - 14 * S, deck_y - 10 * S, bx + 14 * S, deck_y + 8 * S], 200, 340, fill=WOOD_D, width=4 * S)
    # 打烂态：焦黑 + 木屑
    if broken:
        for _ in range(90):
            px = rng.random() * W2
            py = deck_y + rng.random() * (base - deck_y)
            c = CHAR if rng.random() < 0.5 else WOOD_D
            d.line([(px, py), (px + rng.random() * 5 * S, py - rng.random() * 4 * S)], fill=c, width=1)
        d.rectangle([x0, deck_y - 2 * S, x0 + 44 * S, deck_y + 4 * S], fill=CHAR)
    im = grain(im, rng, 8.0, 3.0 if broken else 1.0)
    return im


def save_pair(im, name):
    im1 = im.resize((W1, H1), Image.LANCZOS)
    im1.save(os.path.join(OUT, name + '.png'))
    im.save(os.path.join(OUT, name + '@2x.png'))
    print('  %-22s 1x=%s @2x=%s' % (name, im1.size, im.size))


def main():
    print('码头（木栈桥）')
    save_pair(build(False, 7), 'b13_pier')
    save_pair(build(True, 11), 'b13_pier_broken')
    print('完成：2 态 x (1x + @2x)')


if __name__ == '__main__':
    main()
