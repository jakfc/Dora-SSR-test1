# -*- coding: utf-8 -*-
"""
把走路族的逐帧**左右位置**对齐，消掉"走路左右跳"。

做法（只平移，绝不缩放、绝不裁剪构图）：
1. 全族先按脚底线（主体连通块最下沿）对齐到同一 baseline —— @2x 会重建，不在这里碰；
2. 用全族剪影的**平均轮廓**当参照；
3. 每帧在 dx ∈ [-CAP, CAP] 里找让「上半身（上面 60% 行）」重叠最大（XOR 最小）的平移量；
   只比上半身，是为了排除腿脚摆动带来的假偏移；
4. dx 还会被夹住，保证平移后内容不越出画布左右边界。

参照用平均轮廓（而不是"相对上一帧"）就不会逐帧累积漂移。

用法：
    python tools/align_walk_frames.py            # 只报告
    python tools/align_walk_frames.py --apply    # 写回 png
    python tools/align_walk_frames.py --apply player enemies   # 只看路径含这些词的族
"""
import io
import os
import re
import sys
from collections import defaultdict

import numpy as np
from PIL import Image

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(PROJ, 'assets', 'sprites')

ALPHA_MIN = 16
CAP = 6             # 单帧最多左右平移多少像素（再大就不是微移而是美术问题，留给重绘）
UPPER = 0.60        # 只比上半身
MIN_GAIN = 1        # 至少要减少这么多像素差才认为值得动
WALK_RE = re.compile(r'_walk$|_walk_r$|_walk$')


def families(root, want):
    fam = defaultdict(list)
    for name in sorted(os.listdir(root)):
        if not name.endswith('.png') or name.endswith('@2x.png'):
            continue
        m = re.match(r'^(.*)_(\d{2})\.png$', name)
        if m:
            fam[m.group(1)].append(name)
    rel = os.path.relpath(root, PROJ).replace(os.sep, '/')
    if want and not any(w in rel for w in want):
        return {}
    return {k: v for k, v in fam.items() if len(v) >= 3 and (k.endswith('_walk') or k.endswith('_walk_r'))}


def alpha_of(path):
    im = Image.open(path).convert('RGBA')
    return np.asarray(im)[:, :, 3].astype(np.int16), im.size


def foot_of(a):
    rows = np.nonzero((a > ALPHA_MIN).any(axis=1))[0]
    return int(rows.max()) if rows.size else a.shape[0] - 1


def head_axis(a):
    m = a > ALPHA_MIN
    ys, _xs = np.nonzero(m)
    if not ys.size:
        return 0.0
    top, bottom = int(ys.min()), int(ys.max())
    cut = top + max(1, int(round((bottom - top + 1) * 0.25)))
    _hy, hx = np.nonzero(m[:cut, :])
    return float(hx.mean()) if hx.size else float(np.nonzero(m)[1].mean())


def main():
    argv = [a for a in sys.argv[1:]]
    apply = '--apply' in argv
    want = [a for a in argv if not a.startswith('--')]
    changed = []
    report = []
    for root, _d, _f in os.walk(SPRITES):
        for prefix, names in sorted(families(root, want).items()):
            paths = [os.path.join(root, n) for n in names]
            arrs = []
            base = None
            for p in paths:
                a, size = alpha_of(p)
                foot = foot_of(a)
                if base is None:
                    base = foot
                # 先按脚底线平移到同一 baseline
                arrs.append(np.roll(a, base - foot, axis=0) if base != foot else a)
            before = [head_axis(a) for a in arrs]
            # 对齐目标：全族「头/上身中轴」的中位数。
            # 为什么不用「和平均剪影最像」当初值：那样只能求局部最优，
            # 走路左右跳的观感主要由头轴左右摆幅决定，直接把头轴拉齐最有效。
            mids = sorted(before)
            target = mids[len(mids) // 2] if mids else 0.0
            shifts = []
            out_arrs = []
            for a in arrs:
                dx = int(round(target - head_axis(a)))
                dx = max(-CAP, min(CAP, dx))
                mask = a > ALPHA_MIN
                cols = np.nonzero(mask.any(axis=0))[0]
                lo, hi = (int(cols.min()), int(cols.max())) if cols.size else (0, a.shape[1] - 1)
                # 平移不许让内容出画布（会被切掉手指/刀尖）
                while dx > 0 and hi + dx > a.shape[1] - 1:
                    dx -= 1
                while dx < 0 and lo + dx < 0:
                    dx += 1
                shifts.append(dx)
                out_arrs.append(np.roll(a, dx, axis=1))
            after = [head_axis(a) for a in out_arrs]
            rel = os.path.relpath(root, PROJ).replace(os.sep, '/')
            report.append((rel, prefix, len(paths),
                           max(before) - min(before), max(after) - min(after),
                           shifts))
            if apply and any(shifts):
                for p, dx in zip(paths, shifts):
                    if dx == 0:
                        continue
                    im = Image.open(p).convert('RGBA')
                    new = Image.new('RGBA', im.size, (0, 0, 0, 0))
                    new.paste(im, (dx, 0))
                    new.save(p)
                    changed.append((p, dx))
    out = ['%-30s %-26s %3s %8s %8s  %s' %
           ('目录', '族', '帧', '头晃(前)', '头晃(后)', '各帧平移')]
    for rel, prefix, n, b, a, shifts in report:
        out.append('%-30s %-26s %3d %8.1f %8.1f  %s' %
                   (rel, prefix, n, b, a, ' '.join('%+d' % s for s in shifts)))
    out.append('')
    if apply:
        out.append('已平移 %d 帧' % len(changed))
        for p, dx in changed:
            out.append('   %+3d  %s' % (dx, os.path.relpath(p, PROJ).replace(os.sep, '/')))
    else:
        out.append('(只报告，未改文件；加 --apply 写回)')
    text = '\n'.join(out)
    io.open(os.path.join(PROJ, 'tools', '_anim_align.txt'), 'w',
            encoding='utf-8').write(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
