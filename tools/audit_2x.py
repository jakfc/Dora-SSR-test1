#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""盘点 assets/ 里哪些图有 @2x 主稿、哪些只有 1x。

规则（见 docs/美术素材清单与AI生成规范.md 第 1 章）：
	主稿一律按设计尺寸 ×2 出图，命名 `<name>@2x.png`；
	`<name>.png` 是给老代码/老素材兜底的 1x 副本。
	代码优先读 @2x（Assets.ts 的 hiPathOf），所以缺 @2x 的图在大屏 / 镜头拉近后会糊。

输出：docs/_2x_gap.txt（docs/_*.txt 已在 .gitignore 里）
用法：python tools/audit_2x.py
"""
import collections
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def posix(p):
    return '/'.join(p.split(os.sep))


def main():
    out = []
    no2x = []
    have2x = 0
    total = 0
    for dp, dn, fn in os.walk('assets'):
        for f in sorted(fn):
            if not f.endswith('.png') or f.endswith('@2x.png'):
                continue
            total += 1
            p = posix(os.path.join(dp, f))
            if os.path.exists(p[:-4] + '@2x.png'):
                have2x += 1
            else:
                no2x.append(p)

    out.append('1x 图 %d 张；带 @2x 主稿 %d 张；缺 @2x %d 张' % (total, have2x, len(no2x)))
    out.append('')
    out.append('== 缺 @2x 的按目录统计 ==')
    cnt = collections.Counter(os.path.dirname(p) for p in no2x)
    for k in sorted(cnt):
        out.append('  %-34s %d' % (k, cnt[k]))

    pref = collections.defaultdict(list)
    for dp, dn, fn in os.walk('assets/sprites'):
        for f in sorted(fn):
            if not f.endswith('.png') or f.endswith('@2x.png'):
                continue
            m = re.match(r'(.+)_(\d\d)\.png$', f)
            if m:
                pref[posix(os.path.join(dp, m.group(1)))].append(int(m.group(2)))

    out.append('')
    out.append('== 逐帧动画（帧号是探测到的连续编号）==')
    for k in sorted(pref):
        frames = sorted(set(pref[k]))
        hi = sum(1 for i in frames if os.path.exists('%s_%02d@2x.png' % (k, i)))
        out.append('  %-56s %2d 帧   @2x %d/%d' % (k, len(frames), hi, len(frames)))

    out.append('')
    out.append('== 缺 @2x 清单 ==')
    out.extend('  ' + p for p in no2x)

    txt = '\n'.join(out)
    io.open('docs/_2x_gap.txt', 'w', encoding='utf-8').write(txt + '\n')
    print(txt.encode('ascii', 'replace').decode('ascii'))


if __name__ == '__main__':
    main()
