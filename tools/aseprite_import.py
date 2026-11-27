# -*- coding: utf-8 -*-
"""
把 assets/sprites 下的全部游戏素材导入成 Aseprite 工程（art_src/），
方便在 Aseprite 里用时间轴 + 洋葱皮逐帧微调。

- 逐帧序列（`xxx_01.png`、`xxx_02.png` ...）→ 一个多帧 .aseprite（时间轴里就是一套动画）
- 单张素材（建筑、道具、地面…）→ 一个单帧 .aseprite
- 每个工程旁边放 `_frames.json`，记录「第几帧 = 原来的哪个文件」，
  这样 Aseprite 里改完可以用 tools/aseprite_export.py 原路写回 PNG。

导入后会**逐帧回读校验**：帧数、画布、每帧内容框都要和原 PNG 一致，
不一致会报出来（保证「导入是无损的」，微调不会被导入环节污染）。

用法：
    python tools/aseprite_import.py            # 导入 + 校验
    python tools/aseprite_import.py --check    # 只校验已导入的工程
"""
import glob
import io
import json
import os
import re
import subprocess
import sys

from PIL import Image

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(PROJ, 'assets', 'sprites')
ART_SRC = os.path.join(PROJ, 'art_src')
ASEPRITE = r'C:\Users\jakfc\AppData\Local\Programs\Aseprite\aseprite.exe'
SEQ = re.compile(r'^(?P<base>.+?)_(?P<num>\d{2,3})$')


def to_proj_path(p):
    return os.path.relpath(p, PROJ).replace(os.sep, '/')


def scan_families():
    """扫描 assets/sprites，按「同族」分组。"""
    files = [p for p in glob.glob(os.path.join(SPRITES, '**', '*.png'), recursive=True)
             if '@2x' not in os.path.basename(p)]
    groups = {}
    for p in sorted(files):
        stem = os.path.splitext(os.path.basename(p))[0]
        d = os.path.dirname(p)
        m = SEQ.match(stem)
        # 同族还要画布尺寸一致才合并：decal_grass_01 是 24x14、_02 是 20x11，
        # 硬合并会让 Aseprite 把第 2 帧裁/缩到第 1 帧的画布上（导入就不是无损了）。
        sz = Image.open(p).size
        if m:
            key = (d, m.group('base'), sz, True)
            groups.setdefault(key, []).append((int(m.group('num')), p))
        else:
            key = (d, stem, sz, False)
            groups.setdefault(key, []).append((0, p))
    out = []
    for (d, base, sz, is_seq), items in sorted(groups.items()):
        items.sort()
        first = items[0][1]
        single = len(items) < 2
        # 单张素材用完整文件名命名，避免「同族但尺寸不同」分裂出的两个工程重名
        name = os.path.splitext(os.path.basename(first))[0] if single else base
        out.append({
            'name': name,
            'dir': os.path.relpath(d, PROJ).replace(os.sep, '/'),
            'seq': is_seq and not single,
            'src': to_proj_path(first),
            'files': [to_proj_path(p) for _, p in items],
            'out': to_proj_path(os.path.join(ART_SRC, os.path.relpath(d, SPRITES).replace(os.sep, '/'), name + '.aseprite')),
        })
    return out


def bbox_of(path):
    im = Image.open(path).convert('RGBA')
    bb = im.split()[3].point(lambda v: 255 if v > 16 else 0).getbbox()
    return (im.width, im.height, bb)


def main():
    check_only = '--check' in sys.argv
    fams = scan_families()
    seqs = [f for f in fams if f['seq'] and len(f['files']) > 1]
    singles = [f for f in fams if not (f['seq'] and len(f['files']) > 1)]
    print('素材族 %d 个：多帧序列 %d，单帧 %d' % (len(fams), len(seqs), len(singles)))

    if not check_only:
        os.makedirs(ART_SRC, exist_ok=True)
        for f in fams:
            os.makedirs(os.path.dirname(os.path.join(PROJ, f['out'])), exist_ok=True)
        lua = ['return {']
        for f in fams:
            lua.append('  {src="%s", out="%s", want=%d},' % (f['src'], f['out'], len(f['files'])))
        lua.append('}')
        io.open(os.path.join(ART_SRC, '_import_tasks.lua'), 'w', encoding='utf-8', newline='\n').write('\n'.join(lua) + '\n')
        r = subprocess.run([ASEPRITE, '-b', '--script',
                            os.path.join(PROJ, 'tools', 'aseprite', 'import_families.lua')],
                           capture_output=True, text=True, timeout=1800)
        if r.returncode != 0:
            print('aseprite 退出码', r.returncode, r.stdout[-2000:], r.stderr[-2000:])

    logp = os.path.join(ART_SRC, '_import_log.txt')
    if not os.path.exists(logp):
        print('没有导入日志，先跑一次导入')
        return
    log = io.open(logp, encoding='utf-8').read().splitlines()
    bad = []
    frames_report = {}
    for line in log:
        parts = line.split('\t')
        if parts[0] != 'OK':
            bad.append(line)
            continue
        src, out, nf, cv = parts[1], parts[2], parts[3], parts[4]
        boxes = []
        for cell in parts[5:]:
            if not cell.startswith('f') or 'empty' in cell:
                continue
            _, v = cell.split('=', 1)
            boxes.append(tuple(int(t) for t in v.split(',')))
        frames_report[out] = boxes
        # 与原 PNG 逐帧比对
        fam = [f for f in fams if f['out'] == out]
        if not fam:
            bad.append('未知工程 ' + out)
            continue
        fam = fam[0]
        if len(boxes) != len(fam['files']):
            bad.append('帧数不符 %s：工程 %d 帧 vs 素材 %d 张' % (out, len(boxes), len(fam['files'])))
            continue
        for i, (p, box) in enumerate(zip(fam['files'], boxes)):
            w, h, bb = bbox_of(os.path.join(PROJ, p))
            want = (bb[0], bb[1], bb[2], bb[3])
            if want != box:
                bad.append('第 %d 帧内容框不符 %s：工程 %s vs 实图 %s' % (i + 1, p, box, want))

    print('校验：%d 个工程，%d 个问题' % (len(frames_report), len(bad)))
    for b in bad[:20]:
        print('  !!', b)
    # 写侧车（帧 -> 原文件）
    if not check_only:
        for f in fams:
            side = os.path.join(PROJ, f['out'] + '.frames.json')
            io.open(side, 'w', encoding='utf-8', newline='\n').write(json.dumps({
                'aseprite': f['out'],
                'canvas_src': f['src'],
                'frames': f['files'],
            }, ensure_ascii=False, indent=1) + '\n')
        print('已写入 %d 个工程到 art_src/（含 _frames.json 侧车）' % len(fams))


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    main()
