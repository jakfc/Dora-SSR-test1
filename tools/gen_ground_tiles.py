# -*- coding: utf-8 -*-
"""重绘地面贴图：滩涂沙地 / 堡内夯土石板路。

之前那版地面是 AI 出的：顶部 29~38 行是透明或天空（所以看着"镂空"），
中间是一片没有纹理的糊色，铺起来就是一排色块。

这一版改成程序化生成：
  · 值噪声三层（大起伏 + 中颗粒 + 细砂粒），在 x 方向严格周期 = 贴图宽，
    左右边缘天然对齐，铺过去没有接缝（镜像铺也对得上）；
  · 沙地：风纹、碎石、贝壳、顶部草簇；
  · 夯土：石板、车辙、裂缝、路肩草簇；
  · 顶部留一条「地平线暗边」，底部 40px 渐暗（那截会被水面盖住）。

按 2x 画，再 LANCZOS 降采样出 1x：引擎优先用 @2x，所以真正上屏的是清晰版。

用法：
    python tools/gen_pier_ground.py        # 覆盖生成 10 张（5 张 1x + 5 张 @2x）
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, 'assets', 'bg')

W2, H2 = 1280, 320          # 2x 画布（1x = 640x160）
W1, H1 = 640, 160


def vnoise(shape, lx, ly, seed):
    """x 方向周期为 lx 的值噪声，返回 shape 的 [0,1] 数组。lx 必须整除画布宽。"""
    h, w = shape
    rng = np.random.default_rng(seed)
    lat = rng.random((ly, lx))
    xs = np.linspace(0, lx, w, endpoint=False)
    ys = np.linspace(0, ly, h, endpoint=False)
    X0 = np.floor(xs).astype(int) % lx
    X1 = (X0 + 1) % lx
    Y0 = np.floor(ys).astype(int) % ly
    Y1 = (Y0 + 1) % ly
    tx = xs - np.floor(xs)
    ty = ys - np.floor(ys)
    tx = tx * tx * (3 - 2 * tx)
    ty = ty * ty * (3 - 2 * ty)
    v00 = lat[np.ix_(Y0, X0)]
    v01 = lat[np.ix_(Y0, X1)]
    v10 = lat[np.ix_(Y1, X0)]
    v11 = lat[np.ix_(Y1, X1)]
    tx2 = tx[None, :]
    ty2 = ty[:, None]
    top = v00 * (1 - tx2) + v01 * tx2
    bot = v10 * (1 - tx2) + v11 * tx2
    return top * (1 - ty2) + bot * ty2


def grain(seed, big=26.0, mid=14.0, fine=8.0):
    n1 = vnoise((H2, W2), 8, 4, seed) - 0.5
    n2 = vnoise((H2, W2), 32, 16, seed + 101) - 0.5
    n3 = vnoise((H2, W2), 128, 64, seed + 202) - 0.5
    return n1 * big + n2 * mid + n3 * fine


def vgrad(top_rgb, bot_rgb):
    t = (np.arange(H2) / float(H2 - 1))[:, None, None]
    top = np.array(top_rgb, dtype=float)[None, None, :]
    bot = np.array(bot_rgb, dtype=float)[None, None, :]
    return np.repeat(top, W2, axis=1) * (1 - t) + np.repeat(bot, W2, axis=1) * t


# --------------------------------------------------------------------- 沙地
def make_beach(seed, wet=0.0):
    top = np.array([216, 192, 154]) * (1 - 0.22 * wet)
    bot = np.array([168, 140, 102]) * (1 - 0.24 * wet)
    img = vgrad(top, bot)
    img += grain(seed, 24, 13, 9)[:, :, None]

    # 风纹：x 方向周期 58 个整波，保证左右无缝；波峰处亮一点
    x = np.arange(W2)[None, :]
    ph = vnoise((H2, W2), 16, 5, seed + 7) * np.pi * 2
    ripple = np.sin(x / float(W2) * 58 * np.pi * 2 + ph)
    img += (ripple * 7.0)[:, :, None]
    img += (ripple * ripple * 3.0)[:, :, None]

    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, 'RGBA')

    def wrap(fn, x, *a, **kw):
        """把同一个图形在 x±W2 也画一遍，保证跨接缝连续。"""
        for dx in (-W2, 0, W2):
            fn(x + dx, *a, **kw)

    rng = np.random.default_rng(seed + 31)
    # 贴图真正露在岸带上的只有顶部 52px（2x），所以碎石/草簇往顶部偏置
    def top_y():
        return (rng.random() ** 1.7) * H2
    # 碎石
    for _ in range(64):
        px = float(rng.random() * W2)
        py = float(top_y())
        r = 2.0 + rng.random() * 4.0
        shade = 96 + rng.random() * 60

        def pebble(x, px=px, py=py, r=r, shade=shade):
            c = (int(shade), int(shade * 0.94), int(shade * 0.86), 235)
            d.ellipse([x - r, py - r * 0.78, x + r, py + r * 0.78], fill=c)
            d.arc([x - r, py - r * 0.78, x + r, py + r * 0.78], 200, 340,
                  fill=(255, 252, 240, 120), width=1)
            d.arc([x - r, py - r * 0.78, x + r, py + r * 0.78], 20, 160,
                  fill=(60, 48, 34, 110), width=1)
        wrap(pebble, px)
    # 贝壳
    for _ in range(16):
        px = float(rng.random() * W2)
        py = float(top_y())
        r = 3.0 + rng.random() * 3.0

        def shell(x, px=px, py=py, r=r):
            d.pieslice([x - r, py - r, x + r, py + r], 180, 360,
                       fill=(244, 238, 226, 240), outline=(150, 132, 110, 200))
            d.line([x, py - r * 0.9, x, py], fill=(176, 158, 136, 220), width=1)
        wrap(shell, px)
    # 顶部草簇：岸带最显眼的就是这一圈草
    for _ in range(58):
        px = float(rng.random() * W2)
        h0 = 6.0 + rng.random() * 14.0

        def tuft(x, px=px, h0=h0):
            col = (78, 104, 58, 235)
            tip = (122, 148, 84, 235)
            for k in (-2, 0, 2):
                d.line([x + k * 0.8, 1, x + k, 1 + h0 * (0.7 + 0.3 * (k == 0))],
                       fill=tip if k == 0 else col, width=2)
        wrap(tuft, px)
    # 稀疏草根
    for _ in range(30):
        px = float(rng.random() * W2)
        py = 6.0 + rng.random() * 34.0

        def root(x, px=px, py=py):
            d.line([x, py, x + 4, py - 5], fill=(84, 108, 62, 200), width=2)
        wrap(root, px)

    im = im.filter(ImageFilter.GaussianBlur(0.4))
    return im


# --------------------------------------------------------------- 夯土石板路
def make_fortress(seed, ruts=2):
    img = vgrad(np.array([104, 86, 62]), np.array([70, 56, 40]))
    img += grain(seed, 22, 12, 8)[:, :, None]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, 'RGBA')
    rng = np.random.default_rng(seed + 77)

    def wrap(fn, x, *a, **kw):
        for dx in (-W2, 0, W2):
            fn(x + dx, *a, **kw)

    # 石板：错缝铺，随机跳过一些（露出夯土）
    cw, ch = 46, 26
    for row, y0 in enumerate(range(-4, H2, ch)):
        off = (cw // 2) if row % 2 else 0
        for col, x0 in enumerate(range(-cw, W2 + cw, cw)):
            if rng.random() < 0.28:
                continue
            jx = (rng.random() - 0.5) * 5
            jy = (rng.random() - 0.5) * 4
            shade = 104 + rng.random() * 44
            bw = cw - 5 + rng.random() * 3
            bh = ch - 5 + rng.random() * 3
            x = float(x0 + off + jx)
            y = float(y0 + jy)

            def stone(x, y=y, bw=bw, bh=bh, shade=shade):
                c = (int(shade), int(shade * 0.96), int(shade * 0.9), 255)
                d.rounded_rectangle([x, y, x + bw, y + bh], radius=5, fill=c)
                d.line([x + 3, y + 2, x + bw - 3, y + 2],
                       fill=(int(shade * 1.18), int(shade * 1.16), int(shade * 1.1), 200), width=1)
                d.line([x + 3, y + bh - 1, x + bw - 3, y + bh - 1],
                       fill=(int(shade * 0.6), int(shade * 0.58), int(shade * 0.54), 220), width=2)
            wrap(stone, x)
    # 车辙：两条横向压暗带，带一点起伏
    for k in range(ruts):
        yb = H2 * (0.52 + 0.22 * k)
        for x in range(0, W2, 16):
            wob = np.sin(x / float(W2) * 26 * np.pi * 2) * 4.0
            d.rectangle([x, yb + wob, x + 16, yb + wob + 11],
                        fill=(44, 34, 24, 64))
    # 裂缝
    for _ in range(4):
        x = float(rng.random() * W2)
        y = float(rng.random() * H2 * 0.8)
        pts = [(x, y)]
        for i in range(1, 7):
            pts.append((x + i * 7 + (rng.random() - 0.5) * 8, y + i * 5 + (rng.random() - 0.5) * 6))
        for dx in (-W2, 0, W2):
            d.line([(px + dx, py) for px, py in pts], fill=(38, 29, 20, 170), width=2)
    # 路肩 / 缝里的草（地面露出来的是顶部一圈，往顶部偏置）
    for _ in range(40):
        px = float(rng.random() * W2)
        if rng.random() < 0.55:
            py = 3.0 + rng.random() * 46.0
        else:
            py = 40.0 + rng.random() * (H2 - 50)

        def weed(x, px=px, py=py):
            for k in (-2, 0, 2):
                d.line([x + k, py, x + k * 1.6, py - 7 - abs(k)],
                       fill=(74, 100, 56, 225), width=2)
        wrap(weed, px)

    im = im.filter(ImageFilter.GaussianBlur(0.35))
    return im


def finish(im2, name):
    """加地平线暗边 + 底部渐暗，然后写 @2x 和 1x。"""
    a = np.asarray(im2).astype(float)
    h = a.shape[0]
    shade = np.ones((h, 1, 1))
    for y in range(0, 3):                      # 地平线极细一道暗线：和天空分开
        shade[y] = 1.0 - 0.06 * (1 - y / 3.0)
    for y in range(3, 16):                     # 紧挨着地平线的受光面，亮一点
        shade[y] = 1.0 + 0.09 * (1 - (y - 3) / 13.0)
    for y in range(h - 90, h):                 # 底部渐暗（会被水面盖）
        shade[y] = 1.0 - 0.30 * ((y - (h - 90)) / 90.0)
    a[:, :, :3] *= shade
    im2 = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    im1 = im2.resize((W1, H1), Image.LANCZOS)
    p2 = os.path.join(BG, name + '@2x.png')
    p1 = os.path.join(BG, name + '.png')
    im2.save(p2)
    im1.save(p1)
    return p1, p2


def main():
    jobs = [
        ('d05_ground_beach', lambda: make_beach(11, 0.0)),
        ('d05_ground_beach_b', lambda: make_beach(29, 0.10)),
        ('d05_ground_beach_c', lambda: make_beach(53, 0.34)),
        ('d04_ground_fortress', lambda: make_fortress(17, 2)),
        ('d04_ground_fortress_b', lambda: make_fortress(41, 1)),
    ]
    for name, fn in jobs:
        im2 = fn()
        p1, p2 = finish(im2, name)
        print('  %-24s 2x=%s  1x=%s' % (name, im2.size, (W1, H1)))
    print('完成：%d 张（每张 1x + @2x）' % (len(jobs) * 2))


if __name__ == '__main__':
    main()
