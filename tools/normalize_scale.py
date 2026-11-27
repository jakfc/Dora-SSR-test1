#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""逐帧「量与对齐」工具：把角色动作帧统一到站立帧的基准上。

只做两件事，都是安全操作：
  1) 走路帧**逐帧**归一化到站立帧的内容高（走路时身高不该变；实测倭寇走路帧
     有 57px / 100px 两档，画面上就是「一高一低」）；
  2) 所有帧把**内容底部贴到站立帧的脚底线**、**横向中心贴到站立帧的中轴**
     （原先 scout 走路帧脚底悬空 40px，就是这一步缺失）。

绝不做的两件事（都踩过坑，别再改回去）：
  * 不按「躯干高度」裁剪再缩放 —— 会把出拳/冲锋帧的整个人裁小 13%；
  * 不给 attack / work / qilin / hurt / fall 这些**姿势会变**的组做缩放 ——
    半蹲出拳本来就矮，硬拉成站立高度就是「攻击变大」。

用法：python tools/normalize_scale.py            # 干跑，只出报告
      python tools/normalize_scale.py --apply    # 落盘（1x + 严格 2 倍 @2x）
报告：tools/_normalize_scale.txt
"""
import io
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, 'tools', '_normalize_scale.txt')

SCALE_MIN, SCALE_MAX = 0.50, 1.80   # 缩放上下限：宁可少缩放，绝不把拳脚切掉
SCALE_TOL = 0.15                    # 非走路组：与站立帧差 15% 以内不动（姿势差异）
WALK_TOL = 0.02                     # 走路组：身高必须恒定，只容忍 5%
ACTIONS = ['walk', 'attack', 'work', 'fall', 'hurt', 'qilin']
SCALE_ACTIONS = ['walk']            # 只有走路做逐帧归一化（身高必须恒定）

FAMILIES = [
    ('player', 'assets/sprites/player', 'player'),
    ('villager_idle', 'assets/sprites/villagers', 'villager_idle'),
    ('villager_farmer', 'assets/sprites/villagers', 'villager_farmer'),
    ('villager_salt_worker', 'assets/sprites/villagers', 'villager_salt_worker'),
    ('villager_builder', 'assets/sprites/villagers', 'villager_builder'),
    ('villager_militia', 'assets/sprites/villagers', 'villager_militia'),
    ('villager_kung_fu', 'assets/sprites/villagers', 'villager_kung_fu'),
    ('enemy_scout', 'assets/sprites/enemies', 'enemy_scout'),
    ('enemy_samurai', 'assets/sprites/enemies', 'enemy_samurai'),
    ('enemy_boss', 'assets/sprites/enemies', 'enemy_boss'),
]


def content_box(im):
    """内容外接框 (x0, y0, x1, y1)，右下开区间；全透明返回 None。"""
    W, H = im.size
    a = im.load()
    x0, x1, y0, y1 = W, -1, H, -1
    for y in range(H):
        for x in range(W):
            if a[x, y][3] > 24:
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
    return (x0, y0, x1 + 1, y1 + 1)


def group_of(stem, pref):
    """帧名归组：player_walk_03 -> walk；enemy_boss_r_01 -> idle(r)；enemy_boss_walk_r_02 -> walk(r)"""
    rest = stem[len(pref) + 1:]
    right = False
    m = re.match(r'^(.*?)_r_(\d+)$', rest)
    if m:
        right = True
        rest = m.group(1)
    if re.match(r'^\d+$', rest):
        return ('idle', right)
    for act in ACTIONS:
        if rest == act or rest.startswith(act + '_'):
            return (act, right)
    return ('idle', right)


def frames_of(d, pref):
    return [f for f in sorted(os.listdir(d))
            if f.endswith('.png') and '@2x' not in f and f.startswith(pref + '_')]


def idle_ref(dirrel, pref):
    """该族站立帧的内容高/脚底/中轴（作为整族基准）。"""
    d = os.path.join(ROOT, dirrel)
    best = None
    for f in frames_of(d, pref):
        if group_of(f[:-4], pref)[0] != 'idle':
            continue
        im = Image.open(os.path.join(d, f)).convert('RGBA')
        b = content_box(im)
        if b is None:
            continue
        if best is None or (b[3] - b[1]) > best[1]:
            best = (f, b[3] - b[1], b)
    return best


def process(dirrel, pref, log, apply_it, ref_override=None):
    d = os.path.join(ROOT, dirrel)
    if not os.path.isdir(d):
        return 0
    fs = frames_of(d, pref)
    if not fs:
        return 0

    info = {}
    for f in fs:
        im = Image.open(os.path.join(d, f)).convert('RGBA')
        b = content_box(im)
        if b is not None:
            info[f] = (im, b)
    if not info:
        return 0

    # 基准 = 站立帧里内容最高的那张（朝右的站立帧也参与候选）
    idle = [(f, v) for f, v in info.items() if group_of(f[:-4], pref)[0] == 'idle']
    if not idle:
        idle = list(info.items())[:1]
    idle.sort(key=lambda kv: kv[1][1][3] - kv[1][1][1])
    ibox = idle[-1][1][1]
    ref_h = ibox[3] - ibox[1]
    ref_foot = ibox[3]
    ref_cx = (ibox[0] + ibox[2]) / 2.0
    base_name = idle[-1][0]
    if ref_override is not None:
        # 村民共用 ART 的 h=50，屏幕上必须一样高：统一拿 villager_idle 当尺子
        ref_h = ref_override[1]
        ref_foot = ref_override[2][3]
        ref_cx = (ref_override[2][0] + ref_override[2][2]) / 2.0
        base_name += '  ← 基准借用 %s' % ref_override[0]

    log.append('=== %s  基准（站立）%s  内容高 %d  脚底 y=%d  中轴 x=%.1f ===' % (
        pref, base_name, ref_h, ref_foot, ref_cx))
    # 各姿势组的中位高，用来报告异常
    bygroup = {}
    for f, (im, b) in info.items():
        bygroup.setdefault(group_of(f[:-4], pref)[0], []).append(b[3] - b[1])
    for g, hs in sorted(bygroup.items()):
        hs.sort()
        med = hs[len(hs) // 2]
        flag = ''
        if g not in SCALE_ACTIONS and abs(med - ref_h) > ref_h * 0.45:
            flag = '  << 与站立帧差 %d%%（姿势差异，不缩放）' % (100 * (med - ref_h) // max(1, ref_h))
        log.append('   组 %-7s %2d 帧  内容高 %d~%d  中位 %d%s' % (g, len(hs), hs[0], hs[-1], med, flag))

    for f in sorted(info.keys()):
        im, b = info[f]
        W, H = im.size
        g = group_of(f[:-4], pref)
        h = b[3] - b[1]
        s = 1.0
        note = '仅对齐'
        if g[0] in SCALE_ACTIONS:
            s_raw = ref_h / float(h)
            if abs(s_raw - 1.0) <= WALK_TOL:
                note = '走路高一致'
            else:
                s = max(SCALE_MIN, min(SCALE_MAX, s_raw))
                note = '走路归一化 ×%.3f'
        src = im.crop(b)
        if s != 1.0:
            nw = max(1, int(round(src.size[0] * s)))
            nh = max(1, int(round(src.size[1] * s)))
            if nw > W or nh > H:
                note = '放不下，退回仅对齐'
                s = 1.0
                src = im.crop(b)
            else:
                src = src.resize((nw, nh), Image.LANCZOS)
        # 内容底部贴脚底线、横向中心贴中轴
        cx_off = int(round(ref_cx - src.size[0] / 2.0))
        bx = max(0, min(W - src.size[0], cx_off))
        by = max(0, min(H - src.size[1], ref_foot - src.size[1]))
        new = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        new.paste(src, (bx, by), src)
        if apply_it:
            new.save(os.path.join(d, f), 'PNG')
            new.resize((W * 2, H * 2), Image.LANCZOS).save(os.path.join(d, f[:-4] + '@2x.png'), 'PNG')
        log.append('   %-36s %-7s 高%3d->%3d 位移(%+d,%+d) %s' % (
            f, g[0] + ('(r)' if g[1] else ''), h, src.size[1], bx - b[0], by - b[1],
            note % s if '%' in note else note))
    log.append('   共 %d 帧 %s' % (len(info), '(已落盘)' if apply_it else '(干跑，加 --apply 落盘)'))
    log.append('')
    return len(info)


def main():
    apply_it = '--apply' in sys.argv
    log = []
    total = 0
    refs = {}
    for _, dirrel, pref in FAMILIES:
        refs[pref] = idle_ref(dirrel, pref)
    villager_ref = refs.get('villager_idle')
    for _, dirrel, pref in FAMILIES:
        ov = villager_ref if (pref.startswith('villager_') and pref != 'villager_idle') else None
        total += process(dirrel, pref, log, apply_it, ov)
    io.open(REPORT, 'w', encoding='utf-8').write('\n'.join(log))
    for l in log:
        if l.startswith('===') or l.startswith('   组 ') or '共 ' in l:
            print(l)
    print('OK: %d 帧, %d 行 -> %s' % (total, len(log), REPORT))


if __name__ == '__main__':
    main()
