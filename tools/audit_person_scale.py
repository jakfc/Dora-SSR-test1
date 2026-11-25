# -*- coding: utf-8 -*-
"""把所有美术素材的「显示尺寸」换算成「几个人高」，检查比例关系。

人的基准：
  - player_idle 内容高度 = 54 设计像素（王叔杲，略高于常人）
  - 普通村民            = 50 设计像素

换算规则与 Assets.ts 的 fitOf 完全一致：
  h 指定：画布高 = h / (1 - padTop - padBottom) * (1 - cropTop)
  w 指定：画布高 = w * texH / texW * (1 - cropTop)
内容高（真正看得见的部分）再把留白去掉。

用法： python tools/audit_person_scale.py [--art]
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src', 'config', 'Assets.ts')

PERSON = 50.0          # 普通村民
PLAYER = 54.0          # 主角
OUT = io.open(os.path.join(ROOT, 'tools', '_person_scale.txt'), 'w', encoding='utf-8')


def log(s=''):
    OUT.write(s + '\n')


def parse_art():
    text = io.open(SRC, encoding='utf-8').read()
    start = text.index('export const ART: Record<string, ArtSpec> = {')
    end = text.index('\n};', start)
    block = text[start:end]
    entries = []
    for line in block.split('\n'):
        m = re.match(r"\s*'([^']+)':\s*\{(.*)\},?\s*$", line)
        if not m:
            continue
        eid, body = m.group(1), m.group(2)
        fields = {}
        pm = re.search(r"path:\s*'([^']+)'", body)
        if not pm:
            continue
        fields['path'] = pm.group(1)
        for key in ('h', 'w', 'padTop', 'padBottom', 'cropTop'):
            km = re.search(key + r':\s*([0-9.]+)', body)
            if km:
                fields[key] = float(km.group(1))
        for key in ('stretch', 'flipX'):
            if re.search(key + r':\s*true', body):
                fields[key] = True
        entries.append((eid, fields))
    return entries


def tex_dims(rel):
    """取实际会用到的纹理尺寸（优先 @2x）。返回 (w, h)。"""
    base, ext = os.path.splitext(rel)
    for cand in (base + '@2x' + ext, rel):
        p = os.path.join(ROOT, cand)
        if os.path.isfile(p):
            try:
                from PIL import Image
                with Image.open(p) as im:
                    return im.size, cand
            except Exception:
                return None, cand
    return None, rel


def content_h(f, tw, th):
    """内容高度（设计像素）。"""
    pad_top = f.get('padTop', 0.0)
    pad_bot = f.get('padBottom', 0.0)
    crop = f.get('cropTop', 0.0)
    visible = 1.0 - crop
    if 'h' in f:
        canvas = f['h'] / max(0.05, 1 - pad_top - pad_bot) * visible
    elif 'w' in f:
        canvas = f['w'] * (th / float(tw)) * visible
    else:
        canvas = float(th) * visible
    if crop > 0:
        return canvas * 1.0
    return canvas * (1 - pad_top - pad_bot)


def parse_targets():
    """读 Assets.ts 里的 PERSON_TARGET：美术和人应该有的对应关系。"""
    text = io.open(SRC, encoding='utf-8').read()
    start = text.index('export const PERSON_TARGET: Record<string, number> = {')
    end = text.index('\n};', start)
    block = text[start:end]
    out = {}
    for line in block.split('\n'):
        m = re.match(r"\s*'([^']+)':\s*([0-9.]+),?\s*$", line)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out


def main():
    entries = parse_art()
    targets = parse_targets()
    log('id                                    内容高   =几个人  (画布高 纹理)')
    log('-' * 88)
    groups = []
    for eid, f in entries:
        dim, used = tex_dims(f['path'])
        if dim is None:
            groups.append((eid, f, None, None, 0.0))
            continue
        tw, th = dim
        ch = content_h(f, tw, th)
        groups.append((eid, f, (tw, th), used, ch))

    def show(title, pred):
        log('')
        log('== %s ==' % title)
        for eid, f, dim, used, ch in groups:
            if not pred(eid, f):
                continue
            ratio = ch / PERSON
            flag = ''
            if ratio < 0.9:
                flag = '  <<< 比人矮'
            log('%-38s %6.1f  %5.2f 个   (%6.1f  %s) %s'
                % (eid, ch, ratio, f.get('h', 0) or 0, used, flag))

    show('人物（基准）', lambda i, f: any(k in i for k in ('player', 'villager', 'enemy_')))
    show('建筑 / 地标', lambda i, f: i.startswith('lm_') or i.startswith('tower_') or i.startswith('gate_'))
    show('道具 / 特效 / 其他', lambda i, f: not any(k in i for k in ('player', 'villager', 'enemy_'))
         and not (i.startswith('lm_') or i.startswith('tower_') or i.startswith('gate_')))

    # ---- 与 Assets.ts 里的 PERSON_TARGET 对账 ----
    TOL = 0.2  # 人；超过这么多就算「人和素材的比例没对齐」
    bad = []
    checked = 0
    log('')
    log('== 与 PERSON_TARGET 对账（容差 %.1f 人） ==' % TOL)
    for eid, f, dim, used, ch in groups:
        want = targets.get(eid)
        if want is None or dim is None:
            continue
        checked += 1
        got = ch / PERSON
        diff = got - want
        if abs(diff) > TOL:
            bad.append((eid, want, got, diff))
            log('%-38s 目标 %5.2f 实测 %5.2f 差 %+.2f  <<< 不合格' % (eid, want, got, diff))
    log('对账 %d 项，不合格 %d 项' % (checked, len(bad)))

    out = io.open(os.path.join(ROOT, 'tools', '_person_scale.txt'), encoding='utf-8').read()
    print('OK: %d entries -> tools/_person_scale.txt' % len(groups))
    print('对账 %d 项，不合格 %d 项' % (checked, len(bad)))
    if bad:
        sys.exit(1)


if __name__ == '__main__':
    main()
