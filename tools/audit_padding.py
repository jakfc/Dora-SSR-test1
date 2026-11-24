#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""校对 src/config/Assets.ts 里每个素材的 padTop / padBottom 与实际图内留白是否一致。

素材重画之后尺寸/留白会变，跑一遍这个脚本就知道哪些要重新校准。
用法（项目根目录）：python tools/audit_padding.py
"""
import io
import os
import re
import sys

from PIL import Image

SRC = 'src/config/Assets.ts'


def parse():
    text = io.open(SRC, encoding='utf-8').read()
    out = []
    for m in re.finditer(r"\t'([A-Za-z0-9_]+)':\s*\{([^}]*)\}", text):
        body = m.group(2)
        e = {'id': m.group(1)}
        for key in ('path', 'padTop', 'padBottom', 'cropTop', 'w', 'h'):
            mm = re.search(r"(?:^|\{|,)\s*%s:\s*'?([^,'}]*?)'?\s*(?:,|$)" % key, body)
            if mm and mm.group(1).strip():
                e[key] = mm.group(1).strip()
        out.append(e)
    return out


def actual(path):
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    bb = im.split()[-1].getbbox()
    if bb is None:
        return w, h, None
    return w, h, {'padTop': bb[1] / h, 'padBottom': (h - bb[3]) / h,
                  'contentW': (bb[2] - bb[0]) / w}


def main():
    bad = 0
    checked = 0
    for e in parse():
        path = e.get('path')
        if not path or not os.path.exists(path):
            continue
        if 'padTop' not in e and 'padBottom' not in e:
            continue
        w, h, act = actual(path)
        if act is None:
            continue
        checked += 1
        rows = []
        for key in ('padTop', 'padBottom'):
            if key in e:
                want = float(e[key])
                got = act[key]
                if abs(want - got) > 0.004:
                    rows.append('%s: 代码 %.3f → 实际 %.3f' % (key, want, got))
        if rows:
            bad += 1
            sys.stdout.write('%-24s %4dx%-4d %s\n' % (e['id'], w, h, '; '.join(rows)))
    sys.stdout.write('\n校对 %d 条，需要调整 %d 条\n' % (checked, bad))


if __name__ == '__main__':
    main()
