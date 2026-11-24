#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""素材接入校验（不需要引擎，可在 CI 里跑）。

检查三件事：
  1. 代码里用字符串引用的资源 id，必须在 src/config/Assets.ts 的 ART 表里存在；
  2. ART 表里的路径是否真的存在文件（缺失只提示，因为缺图会自动回退色块）；
  3. assets/ 下有没有「没被任何 ART 条目引用」的图片（提示清理）。

用法：python tools/lint_assets.py
出错（第 1 项）返回 1，便于 CI 拦截。
"""
import io
import os
import re
import sys

SRC = 'src/config/Assets.ts'
SRC_DIRS = ['src', 'init.ts']
CALLS = ('artAt', 'artInto', 'artStretch', 'artSprite', 'artSize', 'artReady', 'artHide')
# 这些 id 是模板拼出来的（如 `lm_${id}`），不做字面量检查
DYNAMIC_PREFIX = ('lm_', 'villager_', 'tool_', 'enemy_')

# assets/ 下允许存在但不参与 ART 的文件
ALLOW_UNREFERENCED = re.compile(r'assets/gemini/')


def parse_art():
    s = io.open(SRC, encoding='utf-8').read()
    art = {}
    for m in re.finditer(r"\t'([A-Za-z0-9_]+)':\s*\{([^}]*)\}", s):
        body = m.group(2)
        p = re.search(r"(?:^|\{|,)\s*path:\s*'([^']+)'", body)
        art[m.group(1)] = p.group(1) if p else ''
    return art


def iter_sources():
    for root, _dirs, files in os.walk('src'):
        for f in files:
            if f.endswith('.ts'):
                yield os.path.join(root, f)
    if os.path.exists('init.ts'):
        yield 'init.ts'


def main():
    art = parse_art()
    errors, warns = [], []

    # --- 1. 代码引用的 id 必须在表里 ---
    for path in iter_sources():
        text = io.open(path, encoding='utf-8').read()
        for m in re.finditer(r"\b(%s)\((?:[^,()]*,\s*)?'([A-Za-z0-9_]+)'" % '|'.join(CALLS), text):
            rid = m.group(2)
            line = text[:m.start()].count('\n') + 1
            if rid not in art:
                errors.append('%s:%d 资源 id `%s` 不在 ART 表里' % (path, line, rid))

    # --- 2. ART 缺文件（提示） ---
    missing = sorted(k for k, v in art.items() if not v or not os.path.exists(v))
    for k in missing:
        warns.append('缺图：%s -> %s（将回退为色块）' % (k, art[k] or '(无路径)'))

    # --- 3. assets/ 里未引用的图 ---
    used = set(os.path.normpath(v) for v in art.values() if v)
    for root, _dirs, files in os.walk('assets'):
        for f in files:
            p = os.path.normpath(os.path.join(root, f))
            if p in used or ALLOW_UNREFERENCED.search(p):
                continue
            # 同名的 @2x 高清版算已引用
            if p.replace('@2x', '') in used:
                continue
            warns.append('未被引用的素材：%s' % p)

    sys.stdout.write('ART 条目 %d 个；缺图 %d 个；未引用 %d 个\n'
                     % (len(art), len(missing), len([w for w in warns if w.startswith('未被')])))
    for w in warns:
        sys.stdout.write('  [提示] %s\n' % w)
    for e in errors:
        sys.stdout.write('  [错误] %s\n' % e)
    if errors:
        sys.stdout.write('\n校验失败：%d 个错误\n' % len(errors))
        return 1
    sys.stdout.write('\n校验通过。\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
