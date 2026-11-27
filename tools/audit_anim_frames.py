#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""逐帧体检：走路/攻击/干活动画到底哪里「没做好」。

对每一组动画（player_idle / player_walk / player_attack / villager_*_walk ...）报告：
  * 画布尺寸、帧数
  * 每一帧「实体内容」的外接框（去掉四周透明留白）
  * 内容高度、脚底留白、水平中心偏移 —— 这三项在帧间跳动，画面上就是
    人物上下抖、左右滑、忽大忽小
  * 朝向线索：上半身皮肤色像素质心相对内容中心的偏左/偏右

用法（项目根目录）：python tools/audit_anim_frames.py
结果写到 tools/_anim_frames.txt
"""
import io
import os
import re

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'tools', '_anim_frames.txt')

# 关注的动画：目录 + 前缀
GROUPS = [
    ('assets/sprites/player', ['player_idle', 'player_walk', 'player_attack', 'player_qilin']),
    ('assets/sprites/villagers', ['villager_farmer', 'villager_salt_worker', 'villager_builder_hall']),
    ('assets/sprites/enemies', ['enemy_scout', 'enemy_samurai', 'enemy_boss']),
]
SUFFIXES = ['_idle', '_walk', '_attack', '_work', '_fall', '_qilin']


def content_bbox(im):
    """返回实体内容外接框 (x0, x1, y0, y1)；全透明返回 None。"""
    W, H = im.size
    px = im.load()
    minx, maxx, miny, maxy = W, -1, H, -1
    for y in range(H):
        row_has = False
        for x in range(W):
            if px[x, y][3] > 24:
                if x < minx:
                    minx = x
                if x > maxx:
                    maxx = x
                row_has = True
        if row_has:
            if y < miny:
                miny = y
            maxy = y
    if maxx < 0:
        return None
    return (minx, maxx, miny, maxy)


def facing_cue(im, box):
    """用皮肤色像素质心判断脸朝哪边。返回 -1 朝左 / 1 朝右 / 0 看不出来。"""
    x0, x1, y0, y1 = box
    h = y1 - y0 + 1
    px = im.load()
    sx = sy = n = 0
    for y in range(y0, y0 + int(h * 0.45)):
        for x in range(x0, x1 + 1):
            r, g, b, a = px[x, y]
            if a > 120 and r > 140 and g > 100 and b < 170 and r > b + 25 and g > b + 5:
                sx += x
                sy += y
                n += 1
    if n < 8:
        return 0
    cx = (x0 + x1) / 2.0
    off = (sx / n) - cx
    if abs(off) < 1.5:
        return 0
    return -1 if off < 0 else 1


def frames_of(dirpath, prefix):
    out = []
    for f in sorted(os.listdir(dirpath)):
        if not f.startswith(prefix + '_'):
            continue
        m = re.match(r'^%s_(\d+)\.png$' % re.escape(prefix), f)
        if m:
            out.append((int(m.group(1)), os.path.join(dirpath, f)))
    return [p for _, p in sorted(out)]


def main():
    lines = []
    for dirrel, prefixes in GROUPS:
        dirpath = os.path.join(ROOT, dirrel)
        if not os.path.isdir(dirpath):
            continue
        for base in prefixes:
            for suf in SUFFIXES:
                prefix = base + suf if suf != '_idle' else base
                fs = frames_of(dirpath, prefix)
                if not fs:
                    continue
                lines.append('=== %s  %d 帧 ===' % (prefix, len(fs)))
                hs = []
                recs = []
                for p in fs:
                    im = Image.open(p).convert('RGBA')
                    box = content_bbox(im)
                    if box is None:
                        lines.append('   %-42s 全透明！' % os.path.basename(p))
                        continue
                    x0, x1, y0, y1 = box
                    W, H = im.size
                    ch = y1 - y0 + 1
                    cw = x1 - x0 + 1
                    face = facing_cue(im, box)
                    hs.append(ch)
                    recs.append((os.path.basename(p), W, H, cw, ch, H - 1 - y1, x0, W - 1 - x1,
                                 (x0 + x1) / 2.0 - W / 2.0, face))
                if not hs:
                    continue
                hmin, hmax = min(hs), max(hs)
                lines.append('   内容高 min=%d max=%d 跳动=%d (%.0f%%)' % (
                    hmin, hmax, hmax - hmin, 100.0 * (hmax - hmin) / max(1, hmin)))
                for (nm, W, H, cw, ch, bottom, l, r, coff, face) in recs:
                    lines.append('   %-40s %dx%d 内容 %dx%d 脚底留白 %d 左右留白 %d/%d 中心偏 %+.1f 朝向 %s'
                                 % (nm, W, H, cw, ch, bottom, l, r, coff,
                                    {-1: '左', 1: '右', 0: '?'}[face]))
                faces = set(r[9] for r in recs)
                if 1 in faces and -1 in faces:
                    lines.append('   !! 帧间朝向不一致：%s' % sorted(faces))
                lines.append('')

    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
    print('OK: %d 行 -> %s' % (len(lines), OUT))
    for l in lines:
        if l.startswith('===') or '跳动' in l or '!!' in l or '全透明' in l:
            print(l)


if __name__ == '__main__':
    main()
