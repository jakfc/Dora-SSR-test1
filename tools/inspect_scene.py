#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把游戏跑起来，然后把运行中的场景树倒出来（精灵尺寸/位置 + 文字）。

用途：看不到画面的情况下，核对「美术接入是否真的生效」「某个精灵到底画在哪、多大」。

用法（项目根目录，Windows）：
	python tools/inspect_scene.py                # 默认跑 init_game
	python tools/inspect_scene.py init_art       # 换入口（init.ts / init_game.ts / init_art.ts）

结果会写到 docs/_scene_dump.txt，同时在控制台列出前若干行。
引擎路径默认取安装版；可用环境变量 DORA_EXE 覆盖。
"""
import io
import json
import os
import re
import subprocess
import sys
import time

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DORA = os.environ.get('DORA_EXE', r'C:\Users\jakfc\AppData\Local\Programs\Dora SSR\Dora.exe')
ASSET = os.path.dirname(DORA)
REQ = os.path.join(PROJ, 'tools', '_dump_req.json')
OUT = os.path.join(PROJ, 'docs', '_scene_dump.txt')


def run(args, **kw):
    return subprocess.run([DORA, '--asset', ASSET] + args, cwd=PROJ,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kw)


def main():
    entry = sys.argv[1] if len(sys.argv) > 1 else 'init_game'
    code = io.open(os.path.join(PROJ, 'tools', 'dump_scene.lua'), encoding='utf-8').read()
    io.open(REQ, 'w', encoding='utf-8').write(
        json.dumps({'mode': 'lua', 'code': code, 'timeoutSeconds': 60}))

    preview = subprocess.Popen(
        [DORA, '--asset', ASSET, 'cli', 'agent', 'preview', '-p', PROJ,
         '--entry', entry, '--capture-at', '5,9,10'],
        cwd=PROJ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(7)
    r = run(['cli', 'agent', 'command', '-p', PROJ, '--input', REQ])
    preview.wait()
    raw = r.stdout.decode('utf-8', 'replace')
    try:
        data = json.loads(raw[raw.index('{'):])
    except Exception:
        sys.stdout.write(raw[:2000])
        return 1
    out = data.get('output', '')
    io.open(OUT, 'w', encoding='utf-8').write(out)
    lines = out.splitlines()
    sys.stdout.write('success: %s %s\n' % (data.get('success'), data.get('message', '')))
    sys.stdout.write('场景条目 %d 行 -> %s\n' % (len(lines), OUT))
    spr = [l for l in lines if l.startswith('SPR')]
    sys.stdout.write('精灵 %d 个，文字 %d 条\n' % (len(spr), len(lines) - len(spr) - 1))
    for l in lines[:int(os.environ.get('HEAD', '25'))]:
        sys.stdout.write(l + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
