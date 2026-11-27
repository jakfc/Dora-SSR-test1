# -*- coding: utf-8 -*-
"""
把 art_src/ 里在 Aseprite 中微调过的工程**原路写回** assets/sprites/。

流程（每个工程一条命令）：
    aseprite -b xxx.aseprite --sheet sheet.png --data sheet.json --format json-array --sheet-type horizontal
再按 JSON 里的帧矩形把每一帧切出来，写回 `_frames.json` 侧车里记的原文件名，
最后重建 @2x（严格 2 倍，避免引擎挑到不一致的 @2x 让角色动画中途变小）。

用法：
    python tools/aseprite_export.py              # 只报告哪些帧有改动（不写回）
    python tools/aseprite_export.py --apply      # 写回 PNG（并重建 @2x）
    python tools/aseprite_export.py --apply --only player_walk
"""
import glob
import io
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART_SRC = os.path.join(PROJ, 'art_src')
ASEPRITE = r'C:\Users\jakfc\AppData\Local\Programs\Aseprite\aseprite.exe'


def export_family(ase_path, tmpdir):
    sheet = os.path.join(tmpdir, 'sheet.png')
    data = os.path.join(tmpdir, 'sheet.json')
    r = subprocess.run([ASEPRITE, '-b', ase_path,
                        '--sheet', sheet, '--data', data,
                        '--format', 'json-array', '--sheet-type', 'horizontal',
                        '--list-tags', '--list-layers'],
                       capture_output=True, text=True, timeout=600)
    if not os.path.exists(data):
        return None, 'EXPORT_FAIL %s %s' % (r.stdout[-300:], r.stderr[-300:])
    return json.load(io.open(data, encoding='utf-8')), None


def main():
    apply = '--apply' in sys.argv
    only = None
    if '--only' in sys.argv:
        only = sys.argv[sys.argv.index('--only') + 1]
    changed, same, problems = [], 0, []
    tmpdir = tempfile.mkdtemp(prefix='asx_')
    for ase in sorted(glob.glob(os.path.join(ART_SRC, '**', '*.aseprite'), recursive=True)):
        side = ase + '.frames.json'
        if not os.path.exists(side):
            problems.append('缺侧车 ' + ase)
            continue
        info = json.load(io.open(side, encoding='utf-8'))
        if only and only not in os.path.basename(ase):
            continue
        data, err = export_family(ase, tmpdir)
        if err:
            problems.append(err)
            continue
        frames = data.get('frames', [])
        if len(frames) != len(info['frames']):
            problems.append('帧数不符 %s：工程 %d vs 侧车 %d' % (ase, len(frames), len(info['frames'])))
            continue
        sheet = Image.open(os.path.join(tmpdir, 'sheet.png')).convert('RGBA')
        for fr, path in zip(frames, info['frames']):
            box = fr['frame']
            img = sheet.crop((box['x'], box['y'], box['x'] + box['w'], box['y'] + box['h']))
            full = os.path.join(PROJ, path)
            old = Image.open(full).convert('RGBA') if os.path.exists(full) else None
            if old is not None and old.size == img.size and old.tobytes() == img.tobytes():
                same += 1
                continue
            changed.append(path)
            if apply:
                img.save(full)
    print('未变 %d 帧，有改动 %d 帧' % (same, len(changed)))
    for c in changed[:40]:
        print('   ~', c)
    if len(changed) > 40:
        print('   ... 共 %d' % len(changed))
    for p in problems[:10]:
        print('  !!', p)
    if apply and changed:
        fx = os.path.join(PROJ, 'tools', 'fix_sprite_frames.py')
        if os.path.exists(fx):
            subprocess.run([sys.executable, fx, '--apply'], cwd=PROJ,
                           capture_output=True, text=True, timeout=900)
            print('已重建 @2x（tools/fix_sprite_frames.py）')
    if not apply:
        print('(只报告；加 --apply 写回)')


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    main()
