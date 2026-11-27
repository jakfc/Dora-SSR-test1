#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把同一角色族的逐帧图统一到「同一个人高」。

背景（为什么必须做）
--------------------
引擎不会读图里的像素来定大小，它按 `Assets.ts` 里该 id 的 `h`(设计人高)
和 `padTop/padBottom` 反推出显示尺寸 —— 也就是**假定这一族的图画布上
人物都占同样高**。可是 AI 生成的攻击/麒麟步/行走帧经常把人物画成
idle 的 6~7 成（画布一样是 128x192，人却只画 118px 高，而 idle 是 176px），
结果就是：
  * 攻击时人突然变小（118/176 = 0.67 倍）
  * 走路帧一大一小（同一族里有 180 也有 126）
  * 族里 idle 是 125 而 walk 是 180 -> 一走路人就变大

本工具只做一件事：**等比缩放**，把低于参照人高 85% 的帧放大回参照人高，
锚点保持「脚底线不动、内容水平中线不动」。不做裁剪、不做非等比拉伸。

参照人高 = 该族所有"站立类动作"(idle/walk/attack/qilin/hurt) 里最高的内容高。
排除 `fall`(倒地)、`work`(弯腰干活) 这类本来就该趴/弯的姿势 —— 它们矮是对的。

用法:
    python tools/match_family_scale.py            # 只报告，不改文件
    python tools/match_family_scale.py --apply    # 真的改
"""
import glob
import io
import os
import re
import sys

from PIL import Image

BASE = 'assets/sprites'
ALPHA_THR = 24
CONSIDER = ('idle', 'walk', 'attack', 'qilin', 'hurt')
SKIP_GROUPS = ('fall', 'die', 'work')
# 低于参照人高的这个比例才算「画小了」（85% 以上当成正常蹲姿的形变）
LOW = 0.85
# 缩放后内容左右至少留这么多像素，否则算「重绘」而不是硬缩
MIN_EDGE = 3

PAT_ACTION = re.compile(r'^(.*)_(idle|walk|attack|qilin|hurt|fall|die|work)_(\d\d)$')
PAT_IDLE = re.compile(r'^(.*)_(\d\d)$')


def parse(stem):
    """stem -> (family, group, index)。剥掉朝右标记 _r 再解析。"""
    s = stem
    if s.endswith('_r'):
        s = s[:-2]
    s = re.sub(r'_(idle|walk|attack|qilin|hurt|fall|die|work)_r_(\d\d)$', r'_\1_\2', s)
    m = PAT_ACTION.match(s)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    m = PAT_IDLE.match(s)
    if m:
        return m.group(1), 'idle', int(m.group(2))
    return None


def content_box(path, thr=ALPHA_THR):
    im = Image.open(path).convert('RGBA')
    box = im.split()[3].point(lambda a: 255 if a > thr else 0).getbbox()
    return im, box


def main():
    apply = '--apply' in sys.argv
    frames = {}   # family -> list[(path, group, idx, box, h)]
    for d in sorted(os.listdir(BASE)):
        full = os.path.join(BASE, d)
        if not os.path.isdir(full):
            continue
        for f in sorted(glob.glob(os.path.join(full, '*.png'))):
            name = os.path.basename(f)
            if '@2x' in name:
                continue
            p = parse(name[:-4])
            if p is None:
                continue
            fam, grp, idx = p
            if grp in SKIP_GROUPS:
                continue
            im, box = content_box(f)
            if box is None:
                continue
            frames.setdefault(fam, []).append((f, grp, idx, box, box[3] - box[1]))

    print(f"{'族/帧':44s} {'内容高':>6s} {'参照':>5s} {'倍数':>6s}  处理")
    todo = []
    need = []
    for fam in sorted(frames):
        items = frames[fam]
        ref = max(h for _, _, _, _, h in items)
        for f, grp, idx, box, h in sorted(items):
            k = ref / h if h > 0 else 1.0
            tag = ''
            if h < ref * LOW:
                im = Image.open(f)
                cw, chh = im.size
                nw = int(round((box[2] - box[0]) * k))
                if nw + MIN_EDGE * 2 > cw:
                    tag = '需重绘(放大后超出画布宽 %d>%d)' % (nw, cw)
                    need.append((f, h, ref, k, nw, cw))
                else:
                    tag = '放大 x%.2f' % k
                    todo.append((f, box, k))
            elif h > ref * 1.0:
                tag = '(比参照还高，保持)'
            print(f"{os.path.relpath(f, BASE):44s} {h:6d} {ref:5d} {k:6.2f}  {tag}")

    print()
    print('需要缩放 %d 帧，需要重绘 %d 帧' % (len(todo), len(need)))
    for f, h, ref, k, nw, cw in need:
        print('   重绘: %s  内容高 %d(参照 %d) 需要 x%.2f -> 宽 %d > 画布 %d'
              % (os.path.relpath(f, BASE), h, ref, k, nw, cw))
    if not apply:
        print('(只报告，未改文件；加 --apply 执行)')
        return

    for f, box, k in todo:
        x2 = f[:-4] + '@2x.png'
        src = x2 if os.path.exists(x2) else f
        im = Image.open(src).convert('RGBA')
        scale = 1 if src == f else 2  # 有 @2x 就在 2 倍图上干活，糊得少
        bx = (box[0] * scale, box[1] * scale, box[2] * scale, box[3] * scale)
        crop = im.crop(bx)
        tw = max(1, int(round(crop.width * k)))
        th = max(1, int(round(crop.height * k)))
        new = crop.resize((tw, th), Image.LANCZOS)
        W, H = im.width, im.height
        canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        cx = (bx[0] + bx[2]) // 2
        px = cx - tw // 2
        py = bx[3] - th
        canvas.alpha_composite(new, (px, py))
        canvas.save(x2)
        canvas.resize((W // 2, H // 2), Image.LANCZOS).save(f)
        print('   改: %s x%.2f (%dx%d -> %dx%d)'
              % (os.path.relpath(f, BASE), k, crop.width, crop.height, tw, th))


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
