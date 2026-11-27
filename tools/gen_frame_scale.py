#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""逐帧显示倍率表生成器 -> src/config/FrameScale.ts

问题
----
引擎不看图里像素，它按 `Assets.ts` 的 `h`(设计人高) + `padTop/padBottom`
反推显示尺寸，前提是**同一族所有帧的人物在画布上一样高**。
可 AI 生成时经常不是：

    player   idle/walk 人物高 176px，attack 只有 118/110/120px  -> 攻击时人缩成 0.67
    villager_kung_fu  idle 只有 125px，walk 却有 180px           -> 一走路人就变大 44%
    enemy_scout idle/walk 156px，attack 只有 96/81px             -> 攻击缩成 0.6

于是同一个人在不同动作下身高在 0.5~1.4 倍之间跳，游戏里就是
「攻击变小」「走路一高一低」。

办法
----
按族测出每帧内容高，**以该族 idle 帧为人高基准**（idle 才是
Assets.ts 的 h + padTop/padBottom 的标定依据），凡偏离基准超过 12% 的帧，
写一条倍率 k = 基准/该帧（可放大也可缩小）。引擎在造帧精灵时乘上 k，
于是「同一族任意动作、任意帧，屏幕上的人一样大」。
这只解决**大小一致性**，不解决「图被画布切掉」——那是美术要重绘的部分。

注意
----
- 只纠正「站立类动作」(idle/walk/attack/qilin/hurt)。
  `fall`(倒地) 本来就应该矮，绝不能用身高去归一，否则倒地被拉成站立。
- 阈值 12% 是为了放过「下蹲出拳」这种**本来就该略矮**的姿势。
- 缩小的方向是安全的；放大不会把画布外的像素找回来（那要重绘）。

用法:
    python tools/gen_frame_scale.py            # 写 src/config/FrameScale.ts
    python tools/gen_frame_scale.py --check    # 只校验是否最新（CI 用）
    python tools/gen_frame_scale.py --report   # 打印明细，不写文件
"""
import glob
import io
import os
import re
import sys

from PIL import Image

BASE = ['assets/sprites/player', 'assets/sprites/villagers', 'assets/sprites/enemies']
OUT = 'src/config/FrameScale.ts'
ALPHA_THR = 24
CONSIDER = ('idle', 'walk', 'attack', 'qilin', 'hurt')   # 站立类动作
MIN_DIFF = 0.12        # 偏离基准 12% 以内不动，免得抖
MAX_K = 2.2
MIN_K = 1 / MAX_K
PAT_ACTION = re.compile(r'^(.*)_(idle|walk|attack|qilin|hurt|fall|die|work)_(\d\d)$')
PAT_IDLE = re.compile(r'^(.*)_(\d\d)$')
PAT_REV = re.compile(r'_r_(\d\d)$')          # xxx_walk_r_02 -> xxx_walk_02


def parse(stem):
    """('player', 'walk', 2) —— `_r`(朝右)帧并入同一族同一动作。"""
    s = PAT_REV.sub(r'_\1', stem)
    m = PAT_ACTION.match(s)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    m = PAT_IDLE.match(s)
    if m:
        return m.group(1), 'idle', int(m.group(2))
    return None


def content_h(path, thr=ALPHA_THR):
    im = Image.open(path).convert('RGBA')
    box = im.split()[3].point(lambda a: 255 if a > thr else 0).getbbox()
    return 0 if box is None else box[3] - box[1]


def scan():
    fam = {}
    for d in BASE:
        for f in sorted(glob.glob(os.path.join(d, '*.png'))):
            name = os.path.basename(f)
            if '@2x' in name:
                continue
            p = parse(name[:-4])
            if p is None:
                continue
            family, grp, idx = p
            if grp not in CONSIDER:
                continue
            h = content_h(f)
            if h > 0:
                fam.setdefault(family, []).append((f.replace('\\', '/'), grp, idx, h))
    return fam


def median(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def ref_of(items):
    """人高基准 = 该族 idle 帧的内容高中位数。

    为什么是 idle：Assets.ts 的 h + padTop/padBottom 就是从 idle 图上量的，
    它才是「此人设计多高」的官方口径。没有 idle 时才退到 walk。
    """
    for grp in ('idle', 'walk'):
        pool = [h for _, g, _, h in items if g == grp]
        if pool:
            return median(pool)
    return median([h for _, _, _, h in items])


def build():
    fam = scan()
    table = {}
    lines = []
    for family in sorted(fam):
        items = fam[family]
        ref = ref_of(items)
        for f, grp, idx, h in sorted(items):
            k = ref / float(h)
            if abs(k - 1.0) < MIN_DIFF:
                continue
            k = max(MIN_K, min(k, MAX_K))
            table[f] = round(k, 3)
            lines.append("  '%s': %s, // %s 高%d / 人高基准%d"
                         % (f, ('%.3f' % k).rstrip('0').rstrip('.'), grp, h, round(ref)))
    body = '\n'.join(sorted(lines))
    ts = (
        '// 本文件由 tools/gen_frame_scale.py 生成，请勿手改。\n'
        '// 素材换新后跑一次: python tools/gen_frame_scale.py\n'
        '// 作用：同一角色族的所有动作帧在屏幕上保持同一个人高。\n'
        '// 原因：引擎按 Assets.ts 的 h + padTop/padBottom 反推显示尺寸，\n'
        '// 而 AI 出的帧经常把攻击/走路画成 idle 的 6~7 成高（或反过来大 4 成），\n'
        '// 不补这一刀，游戏里就会出现「攻击变小」「走路一高一低」。\n'
        '// 倒地帧(fall)故意不归一：躺下本来就该矮。\n'
        '\n'
        '/** 帧路径 -> 显示倍率（1 表示无需修正）。 */\n'
        'export const FRAME_SCALE: Record<string, number> = {\n'
        + body + ('\n' if body else '') +
        '};\n'
        '\n'
        '/** 取某帧的显示倍率；表里没有就是 1。 */\n'
        'export function frameScaleOf(path: string): number {\n'
        '\tconst k = FRAME_SCALE[path];\n'
        '\treturn k === undefined ? 1 : k;\n'
        '}\n'
    )
    return ts, table


def main():
    ts, table = build()
    check = '--check' in sys.argv
    report = '--report' in sys.argv
    if report:
        for k in sorted(table):
            print('  %6.3f  %s' % (table[k], k))
        print('共 %d 帧需要显示倍率' % len(table))
        return
    old = ''
    if os.path.exists(OUT):
        with io.open(OUT, encoding='utf-8') as fp:
            old = fp.read()
    if check:
        if old != ts:
            print('FAIL: %s 不是最新，跑 python tools/gen_frame_scale.py' % OUT)
            sys.exit(1)
        print('OK: %s 已是最新（%d 帧）' % (OUT, len(table)))
        return
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as fp:
        fp.write(ts)
    print('OK: %d 帧写入 %s' % (len(table), OUT))


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
