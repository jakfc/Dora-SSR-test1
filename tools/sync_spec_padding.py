# -*- coding: utf-8 -*-
"""
把 Assets.ts 里每个素材的 padTop / padBottom 与**实际主稿**对齐。

为什么需要：ART 表里的 h 是「内容在设计像素里的高」（也就是几个人高），
padTop/padBottom 描述的是这张画布上下各留了多少空白。程序按
   画布显示高 = h / (1 - padTop - padBottom)
来显示，所以**一旦美术重画过、留白变了而 padTop 没跟着改**，
这个素材在游戏里就会整体偏大或偏小（例：villager_KUNG_FU 的 padTop
写成 0.318，实际是 0.031 的手误，结果武师在游戏里比村民高 44%）。

本工具只重新量主稿的留白并把两个 pad 写回表里，**不动 h**：
h 是设计意图（人高），pad 是几何事实。

用法：
    python tools/sync_spec_padding.py            # 只报告
    python tools/sync_spec_padding.py --apply    # 写回 Assets.ts
"""
import io
import os
import re
import sys

from PIL import Image

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_TS = os.path.join(PROJ, 'src', 'config', 'Assets.ts')

# 'id': { path: '...', h: 50, padTop: 0.031, padBottom: 0.031 },
ENTRY = re.compile(
    r"'([^']+)':\s*\{([^}]*?)path:\s*'([^']+)'([^}]*?)\}",
    re.S)


def measure(path):
    full = os.path.join(PROJ, path.replace('/', os.sep))
    if not os.path.exists(full):
        return None
    im = Image.open(full).convert('RGBA')
    bb = im.split()[3].point(lambda v: 255 if v > 16 else 0).getbbox()
    if bb is None:
        return None
    _, top, _, bottom = bb
    return im.height, top / im.height, (im.height - bottom) / im.height


def main():
    apply = '--apply' in sys.argv
    src = io.open(ASSETS_TS, encoding='utf-8').read()
    rows = []
    for m in ENTRY.finditer(src):
        sid, head, path, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        body = head + tail
        mt = re.search(r'padTop:\s*([0-9.]+)', body)
        mb = re.search(r'padBottom:\s*([0-9.]+)', body)
        if mt is None or mb is None:
            continue
        got = measure(path)
        if got is None:
            continue
        _, top, bottom = got
        old_t, old_b = float(mt.group(1)), float(mb.group(1))
        if abs(old_t - top) > 0.02 or abs(old_b - bottom) > 0.02:
            rows.append((sid, path, old_t, top, old_b, bottom))
    if not rows:
        print('OK: 所有素材留白与实稿一致')
        return
    print('%-24s %-44s %-16s %-16s' % ('id', 'path', 'padTop 旧->新', 'padBottom 旧->新'))
    for sid, path, ot, nt, ob, nb in rows:
        print('%-24s %-44s %.3f -> %.3f   %.3f -> %.3f' % (sid, path, ot, nt, ob, nb))
    print('共 %d 项需要同步' % len(rows))
    if not apply:
        print('(只报告，未改文件；加 --apply 写回)')
        return
    out = src
    for sid, path, ot, nt, ob, nb in rows:
        pat = re.compile(
            r"('%s':\s*\{[^}]*?padTop:\s*)[0-9.]+([^}]*?padBottom:\s*)[0-9.]+" % re.escape(sid),
            re.S)

        def rep(mo, nt=nt, nb=nb):
            return '%s%.3f%s%.3f' % (mo.group(1), nt, mo.group(2), nb)
        out, n = pat.subn(rep, out, count=1)
        if n != 1:
            print('!! 未能替换 %s' % sid)
    io.open(ASSETS_TS, 'w', encoding='utf-8', newline='\n').write(out)
    print('已写回 %s（%d 项）' % (ASSETS_TS, len(rows)))


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    main()
