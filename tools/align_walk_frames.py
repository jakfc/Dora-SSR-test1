# -*- coding: utf-8 -*-
"""
走路族逐帧「横向归位」——只平移，绝不缩放裁剪。

为什么要重写：旧版用 np.roll 平移，内容贴边时会把像素**绕回另一侧**，
于是下一次测量又看到偏移、再推一次 —— 反复运行会**越推越偏**（实测玩家走路
被推了两次、每次 -1~-6px）。这一版：

1. **目标唯一**：以族内基准帧（文件名最小的那一帧）为准，先把基准帧自己的
   偏移量定为 0，所有帧都对齐到它，所以**跑第二遍就是 0 改动**（幂等）。
2. **不绕回**：平移用切片搬，会掉出画布的像素先检查是不是透明；只要会丢内容
   就把这次平移量收小，收不动就跳过这一帧并报告。
3. **有收益才动**：只有当平移能让该帧与基准帧的重合度（IoU）真的提高
   ≥0.02、且位移 ≥2px 时才写回。

用法：
    python tools/align_walk_frames.py            # 只报告
    python tools/align_walk_frames.py --apply    # 写回 png
    python tools/align_walk_frames.py --apply player enemies   # 只处理路径含这些词的族
"""
import io
import os
import re
import sys

import numpy as np
from PIL import Image

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(PROJ, 'assets', 'sprites')
ALPHA_MIN = 16
GAIN_MIN = 0.02      # 重合度至少要提高这么多
MIN_SHIFT = 2        # 位移小于 2px 不值得动
MAX_SHIFT = 12


def alpha_of(path):
    im = Image.open(path).convert('RGBA')
    return np.asarray(im)[:, :, 3].astype(np.int16)


def shift_nowrap(a, dx):
    """把 a 整体水平平移 dx（正数向右），出界的像素丢弃。"""
    if dx == 0:
        return a
    out = np.zeros_like(a)
    if dx > 0:
        out[:, dx:] = a[:, :-dx]
    else:
        out[:, :dx] = a[:, -dx:]
    return out


def lost(a, dx):
    """这样平移会丢多少不透明像素。"""
    if dx == 0:
        return 0
    if dx > 0:
        band = a[:, -dx:]
    else:
        band = a[:, :-dx]
    return int((band > ALPHA_MIN).sum())


def iou(a, b):
    ma = a > ALPHA_MIN
    mb = b > ALPHA_MIN
    u = int((ma | mb).sum())
    return (int((ma & mb).sum()) / u) if u else 1.0


def best_dx(src, ref):
    """找让 src 与 ref 重合度最高的水平位移。"""
    best, best_v = 0, iou(src, ref)
    for dx in range(-MAX_SHIFT, MAX_SHIFT + 1):
        if dx == 0:
            continue
        v = iou(shift_nowrap(src, dx), ref)
        if v > best_v + 1e-6:
            best, best_v = dx, v
    return best, best_v


def families(want):
    fam = {}
    for root, _d, files in os.walk(SPRITES):
        for n in files:
            if not n.endswith('.png') or n.endswith('@2x.png'):
                continue
            m = re.match(r'(.+)_walk(_r)?_(\d+)\.png$', n)
            if m is None:
                continue
            key = (root, m.group(1) + '_walk' + (m.group(2) or ''))
            fam.setdefault(key, []).append(os.path.join(root, n))
    out = {}
    for (root, key), ps in fam.items():
        if len(ps) < 3:
            continue
        if want and not any(w in root for w in want):
            continue
        ps.sort(key=lambda p: int(re.search(r'_(\d+)\.png$', p).group(1)))
        out[(root, key)] = ps
    return out


def main():
    argv = sys.argv[1:]
    apply_it = '--apply' in argv
    want = [a for a in argv if not a.startswith('--')]
    lines = []
    changed = 0
    for (root, key), ps in sorted(families(want).items()):
        arrs = [alpha_of(p) for p in ps]
        ref = arrs[0]                      # 基准：文件号最小的那一帧
        row, done = [], []
        for i, (p, a) in enumerate(zip(ps, arrs)):
            if i == 0:
                row.append('  0')
                continue
            dx, v0 = best_dx(a, ref)
            if abs(dx) < MIN_SHIFT or v0 - iou(a, ref) < GAIN_MIN:
                row.append('  0')
                continue
            # 收小平移量，避免丢掉出界的内容
            while dx != 0 and lost(a, dx) > 0:
                dx -= 1 if dx > 0 else -1
            if abs(dx) < MIN_SHIFT:
                row.append(' xx')
                continue
            row.append('%+3d' % dx)
            done.append((p, dx))
        if done:
            changed += len(done)
            lines.append('%-46s %d帧  %s' % (
                os.path.relpath(root, SPRITES).replace('\\', '/') + '/' + key,
                len(ps), ' '.join(row)))
            for p, dx in done:
                lines.append('       %+d  %s' % (dx, os.path.relpath(p, PROJ).replace('\\', '/')))
            if apply_it:
                for p, dx in done:
                    im = Image.open(p).convert('RGBA')
                    a = np.asarray(im)
                    out = np.zeros_like(a)
                    if dx > 0:
                        out[:, dx:] = a[:, :-dx]
                    else:
                        out[:, :dx] = a[:, -dx:]
                    Image.fromarray(out, 'RGBA').save(p)
    text = '\n'.join(lines) if lines else 'OK: 所有走路族已经在一条线上（无需平移）'
    print(text)
    io.open(os.path.join(PROJ, 'tools', '_anim_align.txt'), 'w',
            encoding='utf-8').write(text + '\n')
    if apply_it:
        print('\n已写回 %d 帧' % changed)
    else:
        print('\n(只报告，未改文件；加 --apply 写回)')


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    main()
