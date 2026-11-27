# -*- coding: utf-8 -*-
"""按 art_src/_import_log.txt 生成 docs/美术工程清单.md（素材族索引）。"""
import collections
import io
import os
import sys

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(PROJ, 'art_src', '_import_log.txt')
OUT = os.path.join(PROJ, 'docs', '美术工程清单.md')


def main():
    fam = collections.OrderedDict()
    for ln in io.open(LOG, encoding='utf-8', errors='replace').read().splitlines():
        p = ln.split('\t')
        if len(p) < 5 or p[0] != 'OK':
            continue
        src, proj, fr, canvas = p[1], p[2], p[3].replace('frames=', ''), p[4]
        d = os.path.dirname(proj.replace('\\', '/')).replace('art_src/', '')
        key = (d, os.path.basename(proj))
        e = fam.setdefault(key, {'n': fr, 'canvas': canvas, 'src': []})
        e['src'].append(os.path.basename(src))
    lines = [
        '# 美术工程清单（Aseprite）',
        '',
        '每个 `.aseprite` = 一个素材族：**多帧族**是走路/攻击这类逐帧动画，'
        '**单帧族**是一个静态素材。工程目录由 `tools/aseprite_import.py` 从'
        '`assets/sprites/` 生成（目录被 git 忽略，可随时重建）。',
        '改完用 `tools/aseprite/导出回游戏.bat` 写回游戏（会同时重建 @2x、跑一遍无损校验）。',
        '',
        '| 目录 | 工程文件 | 帧 | 画布 | 源图 |',
        '| --- | --- | --- | --- | --- |',
    ]
    for (d, f), e in fam.items():
        srcs = '、'.join(e['src'][:3]) + ('…' if len(e['src']) > 3 else '')
        lines.append('| %s | `%s/%s` | %s | %s | %s |' % (d, d, f, e['n'], e['canvas'], srcs))
    lines += ['', '共 %d 个素材族。' % len(fam), '']
    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
    print('OK: %d 个族 -> %s' % (len(fam), OUT))


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    main()
