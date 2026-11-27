#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把每个角色的动画帧「对齐到同一个地基上」，并顺手修掉跑偏的 @2x 高清图。

背景（用户反馈「村民和怪物左右走的动画没做好」「攻击时角色会变小」）：

1. 引擎按 spec 的「内容高度」把每帧缩放到固定显示高度，而**落脚点**、
   **躯干中轴**完全由贴图里人物画在哪决定。AI 生成的帧各画各的，
   于是同一套走路动画里人物会忽上忽下（怪物原地飘 13 个单位）、左右滑。

2. 引擎优先加载 `@2x`。若某张 `@2x` 画的内容不是 1x 的严格 2 倍
   （例如 `enemy_scout_attack_02@2x` 只有 1x 的一半大），那这帧在屏幕上
   就会突然缩小一半 —— 表现为「攻击的时候角色变小」。

本工具做两件事（都可重复执行，幂等）：
  --align  把同一组动画的每一帧平移，使「内容最低行 = 基准帧的最低行」、
           「内容水平中心 = 基准帧的中心」，画布尺寸不变（缩放在引擎侧恒定）
  --fix2x  所有 <x>.png 的 @2x 若不是严格的 2 倍画布 + 2 倍内容，就用 1x 重做

用法：
  python tools/fix_sprite_frames.py            # 只体检，不写文件
  python tools/fix_sprite_frames.py --apply    # 写入
"""
import io
import os
import re
import sys

from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(ROOT, 'assets', 'sprites')
REPORT = os.path.join(ROOT, 'tools', '_sprite_frames.txt')

ALPHA = 24             # 不算内容的透明阈值
MAX_DRIFT = 2          # 平移 0..2 px 视为已对齐
# 【重要】只平移，不缩放。曾经为了让"攻击帧的躯干和站姿一样高"而缩放帧，
# 结果把出拳帧放大 1.6 倍、手臂捅出画布被切掉（用户：攻击又被截断了）。
# 姿势天生比站姿矮是画法问题，只能重画，不许用缩放去"修"。
SCALE_MIN = 1.0        # 锁定：禁止缩小
SCALE_MAX = 1.0        # 锁定：禁止放大
POSE_RATIO = 0.45      # 内容高不足基准帧 45% 的，认定为倒地/受击等特殊姿势，只对基不缩放
RE_FRAME = re.compile(r'^(.+)_(\d+)$')

# 角色动画族：族名 -> 基准帧（族名 + 后缀）。族内所有帧共用一块画布。
FAMILIES = [
    ('player', 'player_idle_01'),
    ('villager_idle', 'villager_idle_01'),
    ('villager_farmer', 'villager_farmer_01'),
    ('villager_salt_worker', 'villager_salt_worker_01'),
    ('villager_builder', 'villager_builder_01'),
    ('villager_militia', 'villager_militia_01'),
    ('villager_kung_fu', 'villager_kung_fu_01'),
    ('enemy_scout', 'enemy_scout_01'),
    ('enemy_samurai', 'enemy_samurai_01'),
    ('enemy_boss', 'enemy_boss_01'),
]
DIRS = ['player', 'villagers', 'enemies']


def load(p):
    return Image.open(p).convert('RGBA')


def content_box(im):
    """(x0, x1, y0, y1)；全透明返回 None。"""
    W, H = im.size
    px = im.load()
    x0, x1, y0, y1 = W, -1, H, -1
    for y in range(H):
        for x in range(W):
            if px[x, y][3] > ALPHA:
                if x < x0:
                    x0 = x
                if x > x1:
                    x1 = x
                if y < y0:
                    y0 = y
                if y > y1:
                    y1 = y
    if x1 < 0:
        return None
    return (x0, x1, y0, y1)


def members(dirpath, fam):
    """族里的全部帧文件名（不含扩展名），按后缀再按序号排序。"""
    out = []
    if not os.path.isdir(dirpath):
        return out
    for f in os.listdir(dirpath):
        if not f.endswith('.png') or '@2x' in f:
            continue
        stem = f[:-4]
        if stem == fam or stem.startswith(fam + '_'):
            out.append(stem)
    return sorted(out)


def align_family(dirpath, fam, lines, apply_it):
    base = None
    for d in DIRS:
        cand = os.path.join(SPRITES, d, FAMILIES_LOOKUP.get(fam, fam) + '.png')
        if os.path.exists(cand):
            base = cand
            break
    if base is None or not os.path.exists(base):
        lines.append('!! %s 找不到基准帧' % fam)
        return 0, 0
    bim = load(base)
    bbox = content_box(bim)
    if bbox is None:
        lines.append('!! %s 基准帧是空白' % fam)
        return 0, 0
    bW, bH = bim.size
    bx0, bx1, by0, by1 = bbox
    b_gnd = by1
    b_cx = (bx0 + bx1) / 2.0
    b_ch = by1 - by0 + 1
    lines.append('=== %s  基准 %s %dx%d  落脚 y=%d  中轴 x=%.1f  内容高 %d ==='
                 % (fam, os.path.basename(base), bW, bH, b_gnd, b_cx, b_ch))
    changed = 0
    skipped = 0
    for stem in members(dirpath, fam):
        p = os.path.join(dirpath, stem + '.png')
        im = load(p)
        W, H = im.size
        if W != bW or H != bH:
            lines.append('   %-38s 画布 %dx%d != 基准 %dx%d  → 跳过（需重画）'
                         % (stem, W, H, bW, bH))
            skipped += 1
            continue
        box = content_box(im)
        if box is None:
            lines.append('   %-38s 全透明 → 跳过' % stem)
            skipped += 1
            continue
        x0, x1, y0, y1 = box
        ch = y1 - y0 + 1
        # 铁律：逐帧只许平移，絶不允许按「内容高」缩放。
        # （按内容高缩放会把出拳半蹲这类本来就矮的帧拉大、把高的帧压小，
        #   历史上就是它把攻击/麒麟步帧整体缩了 13%。要放大某帧请用 FrameScale 表。）
        s = 1.0
        _ = ch  # 内容高仅用于报告，不参与缩放
        if s != 1.0:
            nw = max(1, int(round(W * s)))
            nh = max(1, int(round(H * s)))
            im = im.resize((nw, nh), Image.Resampling.LANCZOS)
            x0, x1, y0, y1 = (int(x0 * s), int(x1 * s), int(y0 * s), int(y1 * s))
            W2, H2 = im.size
        else:
            W2, H2 = W, H
        dx = int(round(b_cx - (x0 + x1) / 2.0))
        dy = int(round(b_gnd - y1))
        if s == 1.0 and abs(dx) <= MAX_DRIFT and abs(dy) <= MAX_DRIFT:
            lines.append('   %-38s 内容高 %3d  已对齐' % (stem, ch))
            continue
        tag = ('×%.3f ' % s) if s != 1.0 else ''
        lines.append('   %-38s 内容高 %3d→%3d  %s平移 %+d,%+d'
                     % (stem, ch, int(ch * s), tag, dx, dy))
        if apply_it:
            out = Image.new('RGBA', (bW, bH), (0, 0, 0, 0))
            out.paste(im, (dx, dy))
            out.save(p, 'PNG')
            save_2x(out, p)
        changed += 1
    return changed, skipped


FAMILIES_LOOKUP = {}


def save_2x(im, one_x_path):
    hi = one_x_path[:-4] + '@2x.png'
    im.resize((im.size[0] * 2, im.size[1] * 2), Image.Resampling.NEAREST).save(hi, 'PNG')


def fix_2x(lines, apply_it):
    """@2x 必须是**严格 2 倍画布 + 逐像素等于 1x 的 2 倍最近邻放大**，否则用 1x 重做。

    为什么不只比画布和内容框：引擎优先用 @2x 渲染，1x 只当上下文。
    只挪动帧内元素（头/手微调）时，整体内容框不变，
    但像素已经变了——旧版用「内容框偏移 > 24px」当判据会漏掉这类，
    结果就是「1x 改了、游戏里看不见」。所以改成逐像素对比。
    """
    bad = 0
    total = 0
    for d, _, files in os.walk(SPRITES):
        for f in sorted(files):
            if not f.endswith('.png') or '@2x' in f:
                continue
            p = os.path.join(d, f)
            hi = p[:-4] + '@2x.png'
            im = load(p)
            W, H = im.size
            box = content_box(im)
            total += 1
            reason = ''
            if not os.path.exists(hi):
                reason = '缺 @2x'
            else:
                him = load(hi)
                hbox = content_box(him)
                if him.size != (W * 2, H * 2):
                    reason = '画布 %dx%d != 2x %dx%d' % (him.size[0], him.size[1], W * 2, H * 2)
                elif box is not None and hbox is not None:
                    off = (abs(hbox[0] - box[0] * 2) + abs(hbox[1] - box[1] * 2)
                           + abs(hbox[2] - box[2] * 2) + abs(hbox[3] - box[3] * 2))
                    if off > 24:
                        reason = '内容偏移 %d px（1x 内容 %dx%d，@2x 内容 %dx%d）' % (
                            off, box[1] - box[0] + 1, box[3] - box[2] + 1,
                            hbox[1] - hbox[0] + 1, hbox[3] - hbox[2] + 1)
                    elif ImageChops.difference(
                            him.convert('RGBA'),
                            im.convert('RGBA').resize((W * 2, H * 2),
                                                      Image.Resampling.NEAREST)).getbbox() is not None:
                        reason = '像素与 1x 不一致（1x 改过，@2x 没跟上）'
            if reason == '':
                continue
            bad += 1
            lines.append('   %-46s %s' % (f, reason))
            if apply_it:
                save_2x(im, p)
    lines.append('')
    lines.append('@2x 体检：%d 张 1x，其中 %d 张 @2x 不合格' % (total, bad))
    return bad


def main():
    apply_it = '--apply' in sys.argv
    # 默认只重建 @2x（安全：永远不动 1x）。
    # 1x 对基是「会改画面」的操作，必须显式 --align 才会跑，
    # 否则它会把 align_walk_frames.py 刚做好的横向对齐又挪回去。
    only = '2x'
    if '--fix2x' in sys.argv:
        only = '2x'
    if '--align' in sys.argv:
        only = 'align'
    if '--all' in sys.argv:
        only = None
    lines = []
    if only in (None, 'align'):
        for d in DIRS:
            for fam, base in FAMILIES:
                FAMILIES_LOOKUP[fam] = base
        lines.append('########## 动画帧对基 ##########')
        for d in DIRS:
            for fam, base in FAMILIES:
                dp = os.path.join(SPRITES, d)
                if not os.path.exists(os.path.join(dp, base + '.png')):
                    continue
                c, s = align_family(dp, fam, lines, apply_it)
                if c or s:
                    lines.append('   → 平移 %d 帧，跳过 %d 帧' % (c, s))
                lines.append('')
        lines.append('')
    if only in (None, '2x'):
        lines.append('########## @2x 体检 ##########')
        fix_2x(lines, apply_it)
    io.open(REPORT, 'w', encoding='utf-8').write('\n'.join(lines))
    print('OK: %d 行 -> %s' % (len(lines), REPORT))
    print('模式：%s' % ('写入' if apply_it else '只体检（加 --apply 才写）'))


if __name__ == '__main__':
    main()
