# -*- coding: utf-8 -*-
"""把地面贴图顶部「不是土」的那一条补成土。

地面贴图是横截面风格：贴着地平线往下铺，屏幕上真正看得见的就是**贴图最上面那一小条**
（岸带 26px 左右）。原来两张 beach 贴图最上面 30 行 alpha=0（镂空），fortress 贴图最上面
40 行是偏蓝的「天/水」色 —— 铺上去就是一条空洞/一条灰蓝，看着像地面被掏了个口子。

做法：找到第一条「实心土」的行 r0，把 r0 的颜色往上延伸成 r0 行，并向上轻微压暗，
让地平线处有一条自然的暗边。1x / @2x 各自处理，尺寸不变（不破坏 @2x 严格 2 倍的关系）。

用法： python tools/fix_ground_top.py [--check]
"""
import glob
import io
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = os.path.join(ROOT, 'assets', 'bg')


def luma(p):
    return (p[0] * 299 + p[1] * 587 + p[2] * 114) // 1000


def is_dirt_row(pts):
    """一行是不是「土」：整体不透明、不是偏蓝的天/水色、亮度不过高。"""
    a = sum(p[3] for p in pts) / len(pts)
    if a < 250:
        return False
    r = sum(p[0] for p in pts) / len(pts)
    b = sum(p[2] for p in pts) / len(pts)
    l = sum(luma(p) for p in pts) / len(pts)
    if b > r + 4:      # 偏蓝 → 天/水
        return False
    if l > 185:        # 太亮 → 雪/天空
        return False
    return True


def row_of(px, w, y):
    step = max(1, w // 32)
    return [px[x, y] for x in range(0, w, step)]


def find_ground_start(im):
    w, h = im.size
    px = im.load()
    for y in range(0, min(h, int(h * 0.5))):
        if is_dirt_row(row_of(px, w, y)) and (
            y + 1 >= h or is_dirt_row(row_of(px, w, y + 1))
        ):
            return y
    return 0


def repair(path, apply=True):
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    px = im.load()
    r0 = find_ground_start(im)
    if r0 <= 0:
        return (path, im.size, 0, 'OK 本来就是土，没动')
    if not apply:
        return (path, im.size, r0, '需补 %d 行' % r0)
    src = [px[x, r0] for x in range(w)]
    for y in range(r0 - 1, -1, -1):
        # 越靠上越暗一点点：地平线处形成一条自然的暗边，不会是一块死板的平色
        k = 1.0 - 0.16 * (1.0 - y / float(r0))
        for x in range(w):
            p = src[x]
            px[x, y] = (
                max(0, min(255, int(p[0] * k))),
                max(0, min(255, int(p[1] * k))),
                max(0, min(255, int(p[2] * k))),
                255,
            )
    im.save(path)
    return (path, im.size, r0, '已补 %d 行' % r0)


def main():
    check = '--check' in sys.argv
    files = sorted(glob.glob(os.path.join(BG, '*ground*.png')))
    out = io.open(os.path.join(ROOT, 'tools', '_ground_top.txt'), 'w', encoding='utf-8')
    fixed = 0
    for f in files:
        rel = os.path.relpath(f, ROOT).replace('\\', '/')
        path, size, r0, msg = repair(f, apply=not check)
        line = '%-46s %4dx%-4d 顶部非土 %3d 行  %s' % (rel, size[0], size[1], r0, msg)
        print(line)
        out.write(line + '\n')
        if r0 > 0 and not check:
            fixed += 1
    out.close()
    print('共 %d 张，%s %d 张' % (len(files), '需要修' if check else '已修', fixed if not check else sum(
        1 for f in files if find_ground_start(Image.open(f).convert('RGBA')) > 0)))


if __name__ == '__main__':
    main()
