#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把一组动画帧「对到同一把尺子」上：脚落地、身子居中、个头一致。

为什么需要它
------------
引擎（Assets.ts 的 fitOf）是按 **整张画布的内容高** 缩放每一帧的：
    h = spec.h / (1 - padTop - padBottom)
也就是说一帧里只要有胳膊/刀尖冒出去，画布内容就变高，**身子反而被压小**；
画布里人物偏下，屏幕上人「浮」在半空；偏左/偏右，走起来就「滑」。

本工具对每一族动画（以站直的那张为基准帧）做三件事：
  1) 缩放：每帧「躯干高」对齐基准帧；上限卡在「画布装得下」，绝不切掉拳脚
  2) 竖直：每帧内容底边 = 基准帧脚底线
  3) 水平：每帧躯干中轴 = 基准帧躯干中轴
输出：原地覆盖 1x PNG，并按「严格 2 倍」重写 @2x PNG（引擎优先用 @2x）。
干跑只看报告：默认干跑；真正落盘：加 --apply。

用法：python tools/remaster_anim_canvas.py [--apply]
"""
import io
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'tools', '_anim_canvas.txt')

# 每一族：目录、帧前缀、基准帧（必须是站直的那张，不能用攻击/干活帧当基准）
FAMILIES = [
    ('assets/sprites/player', 'player', 'player_idle_01'),
    ('assets/sprites/villagers', 'villager_idle', 'villager_idle_01'),
    ('assets/sprites/villagers', 'villager_farmer', 'villager_farmer_01'),
    ('assets/sprites/villagers', 'villager_salt_worker', 'villager_salt_worker_01'),
    ('assets/sprites/villagers', 'villager_builder', 'villager_builder_01'),
    ('assets/sprites/villagers', 'villager_militia', 'villager_militia_01'),
    ('assets/sprites/villagers', 'villager_kung_fu', 'villager_kung_fu_01'),
    ('assets/sprites/enemies', 'enemy_scout', 'enemy_scout_01'),
    ('assets/sprites/enemies', 'enemy_samurai', 'enemy_samurai_01'),
    ('assets/sprites/enemies', 'enemy_boss', 'enemy_boss_01'),
]

ALPHA_CUT = 24
SCALE_TOLERANCE = 0.05   # 躯干高差 5% 以内不动，免得来回缩
# 【重要】绝不放大于 1.0：放大后内容会超出画布，被引擎裁掉（「攻击动作被吞一截」的真凶）。
# 宁可让姿势小幅偏小，也不切掉拳脚。
SCALE_MAX = 1.00
SCALE_MIN = 1.00
HEAD_BAND = 0.30         # 上臂/武器「横向突出」判定用的内容高度比例
WIDE_RATIO = 1.6
TORSO_LO, TORSO_HI = 0.35, 0.65   # 躯干（腰胯）竖直区间，用来定中轴
RE_FRAME = re.compile(r'^.+_\d+$')   # 帧名：player_walk_03 / villager_farmer_work_02


def content_bbox(im):
    W, H = im.size
    px = im.load()
    minx, maxx, miny, maxy = W, -1, H, -1
    for y in range(H):
        hit = False
        for x in range(W):
            if px[x, y][3] > ALPHA_CUT:
                if x < minx:
                    minx = x
                if x > maxx:
                    maxx = x
                hit = True
        if hit:
            if y < miny:
                miny = y
            if y > maxy:
                maxy = y
    if maxx < 0:
        return None
    return (minx, miny, maxx, maxy)


def band_stats(im, box, y0f, y1f):
    """内容框内某竖直区间的水平宽度分布 -> (平均宽, 最宽, 次宽行数)。"""
    x0, y0, x1, y1 = box
    h = y1 - y0 + 1
    px = im.load()
    widths = []
    for y in range(y0 + int(h * y0f), y0 + max(1, int(h * y1f))):
        xs = [x for x in range(x0, x1 + 1) if px[x, y][3] > ALPHA_CUT]
        widths.append((xs[-1] - xs[0] + 1) if xs else 0)
    if not widths:
        return (0, 0, 0)
    avg = sum(widths) / float(len(widths))
    peak = max(widths)
    near = len([w for w in widths if w >= peak * 0.7])
    return (avg, peak, near)


def analyze(im, box):
    """返回 {core_h 躯干高, core_top, torso_cx 躯干中轴}。宽手臂/刀剑姿势自动退化。"""
    x0, y0, x1, y1 = box
    ch = y1 - y0 + 1
    a, p, n = band_stats(im, box, 0.0, 0.15)
    c0 = y0 + int(ch * 0.15) if (n >= 3 and p >= a * WIDE_RATIO) else y0
    a2, p2, n2 = band_stats(im, box, 0.85, 1.0)
    c1 = y1 - int(ch * 0.15) if (n2 >= 3 and p2 >= a2 * WIDE_RATIO) else y1
    if c1 <= c0:
        c0, c1 = y0, y1
    # 躯干中轴：取腰胯区间的水平中心
    px = im.load()
    txs = []
    for y in range(y0 + int(ch * TORSO_LO), y0 + max(1, int(ch * TORSO_HI))):
        xs = [x for x in range(x0, x1 + 1) if px[x, y][3] > ALPHA_CUT]
        if xs:
            txs.append((xs[0] + xs[-1] + 1) / 2.0)
    torso_cx = sum(txs) / float(len(txs)) if txs else (x0 + x1 + 1) / 2.0
    return {'core_h': c1 - c0 + 1, 'core_top': c0, 'torso_cx': torso_cx}


def frames_of(dirpath, prefix):
    out = []
    for f in sorted(os.listdir(dirpath)):
        if not f.startswith(prefix + '_') or f.endswith('@2x.png') or not f.endswith('.png'):
            continue
        part = f[len(prefix) + 1:-4]
        if RE_FRAME.match(part) is not None:
            out.append(f[:-4])
    return out


def process_family(dirrel, prefix, base_stem, log, apply_changes):
    dirpath = os.path.join(ROOT, dirrel)
    base_path = os.path.join(dirpath, base_stem + '.png')
    if not os.path.isfile(base_path):
        log.append('!! 缺基准帧 %s，跳过整族' % base_path)
        return 0
    base = Image.open(base_path).convert('RGBA')
    W, H = base.size
    bbox = content_bbox(base)
    if bbox is None:
        log.append('!! 基准帧全透明，跳过 %s' % base_stem)
        return 0
    bst = analyze(base, bbox)
    ground = bbox[3]
    cx_ref = bst['torso_cx']
    core_h = bst['core_h']
    log.append('=== %s  基准 %s  %dx%d ===' % (prefix, base_stem, W, H))
    log.append('   基准：躯干高 %d  脚底 y=%d  躯干中轴 x=%.1f' % (core_h, ground, cx_ref))

    stems = frames_of(dirpath, prefix)
    if base_stem not in stems:
        stems.append(base_stem)
    changed = 0
    for stem in sorted(set(stems)):
        p = os.path.join(dirpath, stem + '.png')
        if not os.path.isfile(p):
            continue
        im = Image.open(p).convert('RGBA')
        if im.size != (W, H):
            log.append('   %-40s 画布 %dx%d 与基准不一致，跳过' % (stem + '.png', im.size[0], im.size[1]))
            continue
        bx = content_bbox(im)
        if bx is None:
            log.append('   %-40s 全透明，跳过' % (stem + '.png'))
            continue
        st = analyze(im, bx)
        is_base = (stem == base_stem)
        # ① 缩放
        s_raw = st['core_h'] / float(core_h)
        content_h = bx[3] - bx[1] + 1
        s_cap = (H - 1) / float(content_h)
        if is_base or abs(s_raw - 1.0) <= SCALE_TOLERANCE:
            s, tag = 1.0, '不动'
        elif '_fall' in stem:
            s, tag = 1.0, '倒地不缩放'
        else:
            s = max(SCALE_MIN, min(s_raw, s_cap, SCALE_MAX))
            tag = '×%.3f%s' % (s, '(封顶)' if s < min(s_raw, SCALE_MAX) - 1e-6 else '')
        # ②③ 裁出内容 -> 缩放 -> 按脚底线与躯干中轴贴回
        crop = im.crop((bx[0], bx[1], bx[2] + 1, bx[3] + 1))
        if abs(s - 1.0) > 1e-6:
            crop = crop.resize((max(1, int(round(crop.size[0] * s))),
                                max(1, int(round(crop.size[1] * s)))), Image.LANCZOS)
        if is_base:
            dx = bx[0]
        else:
            dx = int(round(cx_ref - (st['torso_cx'] - bx[0]) * s))
        dy = ground - (crop.size[1] - 1)
        # 贴回时必须整张塞进画布：宁可中轴偏一点，也不能把拳脚切出画布
        dx = max(0, min(W - crop.size[0], dx))
        dy = max(0, min(H - crop.size[1], dy))
        out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        out.paste(crop, (dx, dy), crop)
        over = 0
        if dx < 0:
            over += -dx
        elif dx + crop.size[0] > W:
            over += dx + crop.size[0] - W
        if dy < 0:
            over += -dy
        elif dy + crop.size[1] > H:
            over += dy + crop.size[1] - H
        nb = content_bbox(out)
        now = analyze(out, nb) if nb else st
        log.append('   %-40s 躯干%3d→%3d %-14s 位移 %+4d,%+4d  出界 %2d px  中轴偏差 %+.1f'
                   % (stem + '.png', st['core_h'], now['core_h'], tag, dx, dy, over,
                      now['torso_cx'] - cx_ref))
        if apply_changes:
            out.save(p)
            hi = out.resize((W * 2, H * 2), Image.NEAREST)
            hi.save(os.path.join(dirpath, stem + '@2x.png'))
            changed += 1
    log.append('')
    return changed


def main():
    apply_changes = '--apply' in sys.argv
    log = []
    total = 0
    for dirrel, prefix, base_stem in FAMILIES:
        total += process_family(dirrel, prefix, base_stem, log, apply_changes)
    log.append('改动帧数：%d  %s' % (total, '(已落盘)' if apply_changes else '(干跑：加 --apply 才落盘)'))
    io.open(REPORT, 'w', encoding='utf-8').write('\n'.join(log))
    print('OK: -> %s' % REPORT)
    for l in log:
        print(l)


if __name__ == '__main__':
    main()
