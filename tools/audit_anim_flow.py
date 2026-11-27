# -*- coding: utf-8 -*-
"""
逐帧动画「一致性 + 流畅性」体检。

对每个多帧素材族，按帧量三件事：

1. **脚底线**（只取角色主体那一块连通区域的最下沿）——脚底不齐 = 走路一高一低
2. **躯干重心 x**（主体中段 30%~70% 高行的像素质心）——左右晃 = 走路左右跳
   （**不拿头/手当尺子**：走路抬臂时「上方 25% 行」会含进手臂，
   把正常摸抬报成「晃」，武师族就被误报过）
3. **内容高**（主体高度）——忽大忽小 = 攻击变小

另外报出：
- **游离碎块**（除主体外面积较大的连通块）：多半是残影/掉出来的手，会让人物看着"发虚"
- **相邻重复帧**（相邻两帧逐像素一样）：会看成卡一下

用法：
    python tools/audit_anim_flow.py             # 全部族
    python tools/audit_anim_flow.py player      # 只看路径含 player 的族
"""
import io
import os
import re
import sys
from collections import defaultdict

import numpy as np
from PIL import Image
from scipy import ndimage

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(PROJ, 'assets', 'sprites')

ALPHA_MIN = 16          # 低于这个 alpha 当透明

# 逐帧显示倍率（src/config/FrameScale.ts）：游戏里每帧会按这个系数放大，
# 体检必须量「实际看到的尺寸」，否则武师那种“半蹲帧”会被误报成“高矮不一致”。
FRAME_SCALE = {}


def load_frame_scale():
    p = os.path.join(PROJ, 'src', 'config', 'FrameScale.ts')
    if not os.path.exists(p):
        return
    for m in re.finditer(r"'([^']+)':\s*([0-9.]+),", io.open(p, encoding='utf-8').read()):
        FRAME_SCALE[m.group(1)] = float(m.group(2))


def displayed(a, k):
    """按引擎的显示方式缩放：以「画布中心 x + 内容底边 y」为原点放大 k 倍。

    锚点就是那两个点，所以脚底位置不变、高于画布的部分会被裁掉（跟引擎一致）。
    """
    h, w = a.shape
    ys = np.nonzero((a > ALPHA_MIN).any(axis=1))[0]
    by = int(ys.max()) if ys.size else h - 1
    cx = (w - 1) / 2.0
    yy, xx = np.mgrid[0:h, 0:w]
    oy = np.round(by + (yy - by) / k).astype(np.int32)
    ox = np.round(cx + (xx - cx) / k).astype(np.int32)
    ok = (oy >= 0) & (oy < h) & (ox >= 0) & (ox < w)
    out = np.zeros_like(a)
    out[yy[ok], xx[ok]] = a[oy[ok], ox[ok]]
    return out
HEAD_ROWS = 0.25        # 头部取主体上方 25% 行
SATELLITE_MIN = 24      # 主体外大于这么多像素的连通块算游离碎块 (也是"要修的")


def frames_of(family_dir):
    """把目录里 `xxx_NN.png` 按族（去 _NN）归拢。"""
    fam = defaultdict(list)
    for name in sorted(os.listdir(family_dir)):
        if not name.endswith('.png') or name.endswith('@2x.png'):
            continue
        m = re.match(r'^(.*)_(\d{2})\.png$', name)
        if m is None:
            continue
        fam[m.group(1)].append(name)
    return {k: v for k, v in fam.items() if len(v) >= 2}


def measure(path):
    im = Image.open(path).convert('RGBA')
    a = np.asarray(im)[:, :, 3]
    k = FRAME_SCALE.get(os.path.relpath(os.path.abspath(path), PROJ).replace(os.sep, '/'),
                        1.0)
    if k != 1.0:
        a = displayed(a, k)
    mask = a > ALPHA_MIN
    if not mask.any():
        return None
    lab, n = ndimage.label(mask, structure=np.ones((3, 3), dtype=int))
    if n == 0:
        return None
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    main_id = int(np.argmax(sizes)) + 1
    main = lab == main_id
    ys, xs = np.nonzero(main)
    top, bottom = int(ys.min()), int(ys.max())
    left, right = int(xs.min()), int(xs.max())
    # 头部中轴：主体上方 25% 行的像素质心 x
    head_cut = top + max(1, int(round((bottom - top + 1) * HEAD_ROWS)))
    hy, hx = np.nonzero(main[:head_cut, :])
    head_x = float(hx.mean()) if hx.size else float((left + right) / 2)
    # 躯干重心：主体中段 30%~70% 行的像素质心 x——眼睛认的「人有没有左右抖」
    body_h = bottom - top + 1
    mid_top = top + max(1, int(round(body_h * 0.30)))
    mid_bot = top + max(2, int(round(body_h * 0.70)))
    my, mx = np.nonzero(main[mid_top:mid_bot, :])
    torso_x = float(mx.mean()) if mx.size else head_x
    sats = int(((sizes >= SATELLITE_MIN) & (np.arange(1, n + 1) != main_id)).sum())
    return dict(foot=bottom, head_x=head_x, torso_x=torso_x, h=bottom - top + 1,
                w=right - left + 1, cx=(left + right) / 2.0, sats=sats,
                canvas=(im.width, im.height), arr=a)


def spread(vals):
    return max(vals) - min(vals)


def main():
    load_frame_scale()
    want = sys.argv[1] if len(sys.argv) > 1 else ''
    report = []
    for root, _dirs, _files in os.walk(SPRITES):
        for prefix, names in sorted(frames_of(root).items()):
            rel = os.path.relpath(root, PROJ).replace(os.sep, '/')
            if want and want not in rel + '/' + prefix:
                continue
            rows = []
            for nm in names:
                got = measure(os.path.join(root, nm))
                if got is not None:
                    rows.append((nm, got))
            if len(rows) < 2:
                continue
            feet = [r[1]['foot'] for r in rows]
            heads = [r[1]['head_x'] for r in rows]
            torsos = [r[1]['torso_x'] for r in rows]
            hs = [r[1]['h'] for r in rows]
            sats = sum(r[1]['sats'] for r in rows)
            dup = 0
            for i in range(1, len(rows)):
                if np.array_equal(rows[i][1]['arr'], rows[i - 1][1]['arr']):
                    dup += 1
            flags = []
            if spread(feet) > 1:
                flags.append('脚底散 %d' % spread(feet))
            if spread(torsos) > 3.0:
                # 阈值 3px：人物在这个项目里高 180px，3px = 1.7% 身高，是肉眼看不出的量；
                # 再往下调会把「本来就没问题」的族也报出来。
                flags.append('躯干晃 %.1f' % spread(torsos))
            # 头/手晃**不作为不合格判据**（见文件头）：走路抬臂时「上方 25% 行」会
            # 把手臂一起算进去，数值大不代表飘。数据仍然打印，供人工看。
            if spread(hs) > 0.22 * max(hs):
                flags.append('高矮 %.0f%%' % (100 * spread(hs) / max(hs)))
            if sats:
                flags.append('碎块 %d' % sats)
            if dup:
                flags.append('重复帧 %d' % dup)
            # 只有**循环动画**（走路）才要求帧间不漂移。
            # 攻击/麒麟步/劳作/倒地这些动作本来就有大幅度位移（出拳、挥锄、
            # 倒地横躺），用同一把尺子量会把正常动作报成问题，所以它们只列数据、
            # 不计入不合格。
            strict_cycle = prefix.endswith('_walk') or prefix.endswith('_walk_r')
            report.append((rel, prefix, len(rows), spread(feet), spread(torsos),
                           spread(hs), sats, dup, flags, rows, strict_cycle))
    bad = [r for r in report if r[8] and r[10]]
    out = []
    out.append('%-30s %-26s %3s %5s %6s %6s %5s %4s' %
               ('目录', '族', '帧', '脚底散', '躯干晃', '高矮散', '碎块', '重复'))
    for rel, prefix, n, f, h, hh, s, d, flags, _rows, strict_cycle in report:
        mark = '  <<<' if (flags and strict_cycle) else ('  (参考)' if flags else '')
        out.append('%-30s %-26s %3d %5d %6.1f %6d %5d %4d%s' %
                   (rel, prefix, n, f, h, hh, s, d, mark))
    out.append('')
    out.append('共 %d 族（其中循环动画 %d 族），不合格 %d 族' %
               (len(report), len([r for r in report if r[10]]), len(bad)))
    for rel, prefix, n, f, h, hh, s, d, flags, _rows, _sc in bad:
        out.append('  %s/%s  %s' % (rel, prefix, '，'.join(flags)))
    text = '\n'.join(out)
    io.open(os.path.join(PROJ, 'tools', '_anim_flow.txt'), 'w',
            encoding='utf-8').write(text + '\n')
    sys.stdout.write(text.encode('utf-8', 'replace').decode('utf-8', 'replace') + '\n')


if __name__ == '__main__':
    main()
