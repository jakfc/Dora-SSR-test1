#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把「爆点类」特效图的实体内容挪到画布正中（幂等）。

为什么要挪：`fx_slash` 这类特效的语义是「以 (x, y) 为圆心炸开」。但 AI 生成的图里
内容常常偏在一角（实测 fx_slash 的内容中心比画布中心偏右 28px、偏下 8px）。
引擎按 ART 的 ay 定锚点，于是半圆刀光画出来整体偏右下 —— 就是「特效位置不对」。

配合 ART 里这几条写成 `ay: 0.5`（纵向按内容中心），本工具再把内容挪到正中，
两点都满足后，特效的中心才真的落在调用处给的坐标上。

用法：python tools/center_fx_art.py [--apply]
"""
import io
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 需要「以调用点为圆心」的特效：路径 + 允许的残余偏移（像素）
TARGETS = [
    'assets/sprites/props/fx_slash.png',
    'assets/sprites/props/fx_arrow_hit.png',
    'assets/sprites/props/fx_cannon_hit.png',
    'assets/sprites/props/fx_shockwave.png',
]
TOL = 2


def bbox(im):
    """实体内容外接框（alpha>24）。手写扫描：PIL 的 point+getbbox 在部分图上给错结果。"""
    W, H = im.size
    a = im.getchannel('A').tobytes()
    x0, x1, y0, y1 = W, -1, H, -1
    for y in range(H):
        row = a[y * W:(y + 1) * W]
        found = False
        for x in range(W):
            if row[x] > 24:
                if x < x0:
                    x0 = x
                if x > x1:
                    x1 = x
                found = True
        if found:
            if y < y0:
                y0 = y
            y1 = y
    if x1 < 0:
        return None
    return (x0, x1 + 1, y0, y1 + 1)


def center_one(rel, apply=False):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return '%s  缺文件' % rel
    im = Image.open(p).convert('RGBA')
    W, H = im.size
    b = bbox(im)
    if b is None:
        return '%s  全透明' % rel
    x0, x1, y0, y1 = b
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0
    dx = int(round(W / 2.0 - cx))
    dy = int(round(H / 2.0 - cy))
    if abs(dx) <= TOL and abs(dy) <= TOL:
        return '%s  已居中（偏 %+d,%+d）' % (rel, dx, dy)
    if not apply:
        return '%s  内容 %dx%d 需位移 %+d,%+d' % (rel, x1 - x0, y1 - y0, dx, dy)
    # 整张图平移（裁剪掉溢出部分，不会被拉伸）
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(im, (dx, dy), im)
    out.save(p)
    p2 = p[:-4] + '@2x.png'
    out.resize((W * 2, H * 2), Image.LANCZOS).save(p2)
    return '%s  内容 %dx%d 已位移 %+d,%+d（1x+@2x）' % (rel, x1 - x0, y1 - y0, dx, dy)


def main():
    apply = '--apply' in sys.argv
    lines = []
    for rel in TARGETS:
        lines.append(center_one(rel, apply))
    txt = '\n'.join(lines)
    io.open(os.path.join(ROOT, 'tools', '_fx_center.txt'), 'w', encoding='utf-8').write(txt)
    for l in lines:
        print(l)
    if not apply:
        print('\n（预演模式：加 --apply 才写文件）')


if __name__ == '__main__':
    main()
