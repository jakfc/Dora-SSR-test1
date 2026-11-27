#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""码头美术：完好 / 半毁 / 已毁 三态，1x + @2x 严格 2 倍。

栈桥自画布右侧岸上伸向左侧水面（西岸码头就是朝左伸出去的；
东岸码头在场景里整体镜像，所以同一张图两边通用）。

    b13_pier.png          完好：桥面整齐、栏杆齐、桩脚入水
    b13_pier_damaged.png  半毁：闯断一半，桥板翘起、栏杆断、桩倾斜、木屑
    b13_pier_broken.png   已毁：桥面只剩靠岸一小截，外侧只剩断桩、水面漂着碎板

用法：python tools/gen_pier.py
"""
import io
import math
import os
import random

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'buildings')  # GameScene/Assets.ts 读的就是这里

W, H = 260, 170              # 1x 画布
WATER_Y = 108                # 水面线（桥面下沿再往下就是水面）
DECK_Y = 92                  # 桥面上表面

WOOD_LIGHT = (150, 116, 72)
WOOD = (122, 92, 56)
WOOD_DARK = (86, 63, 38)
WOOD_WET = (74, 56, 34)
CHAR = (38, 30, 24)          # 烧焦/泡黑的断口
CHAR_HI = (70, 56, 44)
ROPE = (196, 166, 118)
WATER = (26, 52, 80)
WATER_HI = (54, 92, 128)


def jitter(c, rng, amt=14):
    return tuple(max(0, min(255, v + rng.randint(-amt, amt))) for v in c)


def plank(dr, x0, y0, x1, y1, rng, base=WOOD):
    dr.rectangle([x0, y0, x1, y1], fill=jitter(base, rng))
    # 上沿高光 / 下沿阴影，做出木板的厚度
    dr.line([x0, y0, x1, y0], fill=jitter(WOOD_LIGHT, rng, 10))
    dr.line([x0, y1, x1, y1], fill=jitter(WOOD_DARK, rng, 8))


def pile(dr, x, top, bottom, rng, w=9, tilt=0):
    """桩：上宽下略窄，入水部分颜色变深。"""
    for i in range(bottom - top):
        y = top + i
        t = i / float(max(1, bottom - top))
        xx = x + int(tilt * t)
        ww = max(4, int(w * (1 - 0.25 * t)))
        c = WOOD if y < WATER_Y else WOOD_WET
        dr.rectangle([xx - ww // 2, y, xx + ww // 2, y], fill=jitter(c, rng, 10))
    # 桩顶切面
    dr.rectangle([x - w // 2, top - 2, x + w // 2, top + 1], fill=jitter(WOOD_LIGHT, rng, 8))


def snapped_pile(dr, rng, x, top, bottom, w=9, tilt=0):
    """断桩：下半截还在水里，顶上是被砸断的毛茬（浅木色爆开 + 焦黑）。"""
    for i in range(bottom - top):
        y = top + i
        t = i / float(max(1, bottom - top))
        xx = x + int(tilt * t)
        ww = max(4, int(w * (1 - 0.25 * t)))
        c = CHAR if y < top + 6 else (WOOD if y < WATER_Y else WOOD_WET)
        dr.rectangle([xx - ww // 2, y, xx + ww // 2, y], fill=jitter(c, rng, 8))
    # 毛茿：参差不齐的一排小尖
    for k in range(-w // 2, w // 2 + 1):
        h = rng.randint(2, 9)
        dr.line([x + k, top - h, x + k, top], fill=jitter(CHAR_HI, rng, 8))


def rubble_in_water(dr, rng, cx, cy, n, spread):
    """水里漂的碎板 + 剩余的绳子。"""
    for _ in range(n):
        x = cx + rng.randint(-spread, spread)
        y = cy + rng.randint(-8, 16)
        w = rng.randint(8, 26)
        h = rng.randint(2, 5)
        c = WOOD_DARK if rng.random() < 0.55 else WOOD
        dr.rectangle([x, y, x + w, y + h], fill=jitter(c, rng, 12))
        if rng.random() < 0.4:
            dr.line([x + 2, y - rng.randint(1, 4), x + w - 2, y - 1], fill=jitter(CHAR_HI, rng, 8))
    for _ in range(2):
        x = cx + rng.randint(-spread, spread)
        y = cy + rng.randint(-6, 10)
        dr.line([x, y, x + 18, y + 6], fill=jitter(ROPE, rng, 10))


def waterline(dr, rng, x0, x1):
    """桥下水面：暗水 + 几道横向高光。"""
    dr.rectangle([x0, WATER_Y, x1, H - 1], fill=WATER)
    for i in range(7):
        y = WATER_Y + 6 + i * 9
        if y >= H:
            break
        xa = x0 + rng.randint(0, 30)
        xb = x1 - rng.randint(0, 60)
        if xb - xa < 12:
            continue
        dr.line([xa, y, xb, y], fill=WATER_HI)


def deck(dr, rng, x_left, x_right, broken_span=None):
    """桥面：一块块木板铺到 x_right（岸）；broken_span 区间内不铺板。"""
    y0, y1 = DECK_Y, DECK_Y + 16
    x = x_left
    while x < x_right:
        pw = rng.randint(16, 24)
        xa, xb = x, min(x + pw - 2, x_right)
        if broken_span is None or not (xa < broken_span[1] and xb > broken_span[0]):
            plank(dr, xa, y0, xb, y1, rng)
        x += pw
    # 桥面下沿的横梁
    dr.rectangle([x_left, y1 + 1, x_right, y1 + 4], fill=jitter(WOOD_DARK, rng, 6))
    return y1 + 4


def rail(dr, rng, x0, x1, top=44, broken_at=None):
    """栏杆：立柱 + 上下两道横杆；broken_at 之后不画（半毁/已毁）。"""
    end = x1 if broken_at is None else broken_at
    for x in range(x0, end, 34):
        dr.rectangle([x - 3, top, x + 3, DECK_Y], fill=jitter(WOOD, rng, 8))
        dr.rectangle([x - 4, top - 3, x + 4, top], fill=jitter(WOOD_LIGHT, rng, 8))
    if end - x0 > 10:
        for dy in (0, 13):
            y = top + dy
            for x in range(x0, end - 1):
                dr.rectangle([x, y, x + 1, y + 2], fill=jitter(WOOD_LIGHT if dy == 0 else WOOD, rng, 6))


def debris(dr, rng, cx, cy, n, spread=40):
    for _ in range(n):
        x = cx + rng.randint(-spread, spread)
        y = cy + rng.randint(-6, 10)
        w = rng.randint(5, 16)
        h = rng.randint(2, 4)
        dr.rectangle([x, y, x + w, y + h], fill=jitter(WOOD_DARK if rng.random() < 0.5 else WOOD, rng, 12))


def splinters(dr, rng, x, y):
    for _ in range(7):
        dx = rng.randint(-6, 8)
        dr.line([x, y, x + dx, y - rng.randint(4, 12)], fill=jitter(WOOD_LIGHT, rng, 12))


def lantern(dr, x, y):
    dr.rectangle([x - 2, y - 12, x + 2, y], fill=(60, 46, 30))
    dr.rectangle([x - 6, y - 4, x + 6, y + 10], fill=(196, 108, 62))
    dr.rectangle([x - 6, y + 9, x + 6, y + 11], fill=(120, 70, 44))


def gen(state):
    rng = random.Random({'ok': 11, 'damaged': 23, 'broken': 37}[state])
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    shore_x = W - 34

    if state == 'ok':
        waterline(dr, rng, 0, W - 1)
        for i, x in enumerate(range(16, shore_x - 10, 30)):
            pile(dr, x, 120, 152, rng, 9, tilt=rng.choice((-2, -1, 0)))
        deck(dr, rng, 8, shore_x)
        rail(dr, rng, 8, shore_x - 6)
        lantern(dr, shore_x - 26, 78)
    elif state == 'damaged':
        waterline(dr, rng, 0, W - 1)
        # 内侧还撑着，外侧倾斜
        for i, x in enumerate(range(16, shore_x - 10, 30)):
            tilt = -6 if x < 90 else -2
            pile(dr, x, 120, 152, rng, 9, tilt=tilt)
        deck(dr, rng, 92, shore_x, broken_span=(92, 150))
        deck(dr, rng, 150, shore_x)
        # 断口：主梁被砍开一个缺口，露出焦黑的木茬
        dr.polygon([(92, DECK_Y), (92, DECK_Y + 20), (104, DECK_Y + 30), (108, DECK_Y + 6)],
                   fill=jitter(WOOD_DARK, rng, 8))
        dr.line([92, DECK_Y, 104, DECK_Y + 4], fill=jitter(CHAR_HI, rng, 10))
        for k in range(4):
            dr.line([96 + k * 4, DECK_Y + 2, 96 + k * 4, DECK_Y - rng.randint(2, 8)], fill=jitter(CHAR_HI, rng, 8))
        # 断口翘起的桥板
        bre = Image.new('RGBA', (14, 60), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bre)
        plank(bd, 0, 0, 12, 58, rng)
        im.alpha_composite(bre.rotate(24, expand=True, resample=Image.BICUBIC), (96, 74))
        rail(dr, rng, 150, shore_x - 6, broken_at=None)
        rail(dr, rng, 96, 150, broken_at=112)
        debris(dr, rng, 126, WATER_Y + 24, 10, 44)
        debris(dr, rng, 110, DECK_Y + 4, 9)
        splinters(dr, rng, 120, DECK_Y)
        lantern(dr, shore_x - 26, 78)
    else:  # broken
        waterline(dr, rng, 0, W - 1)
        # 靠岸一小截还立着（人还能从这走上岸）
        for i, x in enumerate(range(150, shore_x - 10, 30)):
            pile(dr, x, 120, 152, rng, 9)
        deck(dr, rng, 150, shore_x)
        rail(dr, rng, 158, shore_x - 6, broken_at=196)
        lantern(dr, shore_x - 26, 78)
        # 断口：一截主梁头部斜抽在水面上，旁边是断桩
        dr.polygon([(150, DECK_Y - 2), (150, DECK_Y + 16), (112, DECK_Y + 26), (108, DECK_Y + 8)],
                   fill=jitter(WOOD_DARK, rng, 8))
        dr.polygon([(108, DECK_Y + 8), (112, DECK_Y + 26), (104, DECK_Y + 30), (100, DECK_Y + 14)],
                   fill=jitter(CHAR, rng, 6))
        dr.line([150, DECK_Y - 2, 112, DECK_Y + 8], fill=jitter(WOOD_LIGHT, rng, 10))
        splinters(dr, rng, 146, DECK_Y + 4)
        for x in (44, 78, 116):
            top = 122 + rng.randint(0, 8)
            snapped_pile(dr, rng, x, top, 148, 9, tilt=rng.choice((-12, 9, 11)))
        # 水面漂着的东西：碎板、绳子、沉下一半的灯笼
        rubble_in_water(dr, rng, 86, WATER_Y + 20, 16, 66)
        rubble_in_water(dr, rng, 56, WATER_Y + 40, 9, 42)
        rubble_in_water(dr, rng, 124, WATER_Y + 58, 7, 32)
        fy = WATER_Y + 52
        dr.rectangle([28, fy - 4, 38, fy + 8], fill=(150, 82, 52))
        dr.rectangle([26, fy + 7, 40, fy + 10], fill=(96, 56, 36))
        dr.line([33, fy - 4, 33, fy - 12], fill=(54, 42, 28))
    # 岸（右侧一小段土坡），三态都在
    dr.polygon([(shore_x + 4, DECK_Y - 14), (W - 1, DECK_Y - 18), (W - 1, H - 1), (shore_x - 2, H - 1)],
               fill=(74, 62, 44))
    dr.polygon([(shore_x + 4, DECK_Y - 14), (W - 1, DECK_Y - 18), (W - 1, DECK_Y - 6), (shore_x - 2, DECK_Y + 2)],
               fill=(96, 82, 56))
    return im


def main():
    for state in ('ok', 'damaged', 'broken'):
        im = gen(state)
        name = 'b13_pier' if state == 'ok' else 'b13_pier_' + state
        p1 = os.path.join(OUT, name + '.png')
        p2 = os.path.join(OUT, name + '@2x.png')
        im.save(p1)
        im.resize((W * 2, H * 2), Image.LANCZOS).save(p2)
        # 统计：不透明占比、木色像素质心高度
        px = im.load()
        n = 0
        for y in range(H):
            for x in range(W):
                if px[x, y][3] > 24:
                    n += 1
        print('%-22s %dx%d  不透明 %.1f%%' % (name, W, H, 100.0 * n / (W * H)))
    print('OK -> %s' % OUT)


if __name__ == '__main__':
    main()
