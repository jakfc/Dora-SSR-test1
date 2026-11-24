#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 PNG 的 alpha 轮廓打成 ASCII 图，便于在看不到图的环境里判断构图。

用法：python tools/ascii_preview.py <宽字符数> <文件...>
"""
import sys
from PIL import Image

COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 56
CHARS = ' .:-=+*#%@'


def dump(path):
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    rows = max(4, int(round(COLS * h / w / 2.1)))
    small = im.resize((COLS, rows))
    px = small.load()
    print('=== %s  %dx%d -> %dx%d' % (path, w, h, COLS, rows))
    for y in range(rows):
        line = ''
        for x in range(COLS):
            r, g, b, a = px[x, y]
            if a < 20:
                line += ' '
            else:
                lum = (r * 0.299 + g * 0.587 + b * 0.114) / 255.0
                idx = int(lum * (len(CHARS) - 1) * (a / 255.0))
                line += CHARS[idx]
        print('|%s|' % line)
    print('')


for p in sys.argv[2:]:
    dump(p)
