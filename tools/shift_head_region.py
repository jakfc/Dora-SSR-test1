# -*- coding: utf-8 -*-
"""
把某一帧的「头/肩区域」整体横向平移，修掉**头偏离躯干**的错位。

为什么需要：走路循环里只要有一帧的头比身体偏出十几像素，看起来就是「一高一低」
那种抽一下的感觉。这种错位**平移头部区域**就能修好，不需要重画，
也**不能**用「裁剪再缩放」——那会把人改小（历史事故）。

做法：
  以内容高 30% 处为「颈线」，颈线以上整体平移 dx；
  颈线附近用 ±5 行的线性斜坡把位移渐变到 0，接缝看不出来（1x 像素画）。
  平移若会让像素出画布，自动把 |dx| 收到刚好不出界。

用法：
  python tools/shift_head_region.py assets/sprites/villagers/villager_kung_fu_walk_02.png -12
  python tools/shift_head_region.py <png> <dx> [--apply]     # 不加 --apply 只报告
"""
import os
import sys

import numpy as np
from PIL import Image

RAMP = 5.0     # 接缝渐变半宽（行）
NECK = 0.30    # 颈线位置：内容高的 30%


def arr_of(path):
    im = Image.open(path).convert('RGBA')
    return im, np.asarray(im).astype(np.int16)


def content_rows(a):
    ys = np.nonzero((a[:, :, 3] > 16).any(axis=1))[0]
    return (int(ys.min()), int(ys.max())) if ys.size else None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    apply_it = '--apply' in sys.argv
    path, dx = args[0], int(args[1])
    im, a = arr_of(path)
    rows = content_rows(a)
    y0, y1 = rows
    neck = y0 + (y1 - y0 + 1) * NECK
    # 位移若把像素推出画布，按实际内容收窄
    head = a[:int(neck) + 1 if False else int(neck) + 1, :, :]
    cols = np.nonzero((head[:, :, 3] > 16).any(axis=0))[0]
    if cols.size:
        lim = cols.max() if dx > 0 else cols.min()
        room = (a.shape[1] - 1 - lim) if dx > 0 else lim
        if abs(dx) > room:
            sys.stdout.write('位移被本体边界收到 %d（原要 %d）\n' % (room, dx))
            dx = room if dx > 0 else -room
    out = a.astype(np.int16).copy()
    moved = 0
    for y in range(0, a.shape[0]):
        if y > neck + RAMP:
            break
        if y <= neck - RAMP:
            k = 1.0
        else:
            k = max(0.0, (neck + RAMP - y) / (2 * RAMP))
        if k <= 0:
            continue
        d = int(round(dx * k))
        if d == 0:
            continue
        row = a[y].astype(np.int16)
        shifted = np.zeros_like(row)
        if d > 0:
            shifted[d:, :] = row[:-d, :]
        else:
            shifted[:d, :] = row[-d:, :]
        out[y] = shifted
        moved += 1
    sys.stdout.write('%s：颈线 y=%.0f（内容 %d~%d），平移 %+d，动了 %d 行\n'
                     % (os.path.basename(path), neck, y0, y1, dx, moved))
    if not apply_it:
        sys.stdout.write('（只报告；加 --apply 写回）\n')
        return
    Image.fromarray(out.astype(np.uint8), 'RGBA').save(path)


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    main()
