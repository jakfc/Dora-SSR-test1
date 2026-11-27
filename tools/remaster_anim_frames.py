#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把角色动画帧「修齐」：统一身体大小 + 统一落脚线 + 统一朝向。

用 tools/audit_anim_frames.py 量出来的三宗罪：

 1. 出拳/麒麟步时角色变小 —— 攻击帧的「躯干高」只有 156，站立帧 176，
    缩了 11%。引擎按「画布尺寸 + ART 里的 padTop/padBottom」定缩放，
    这个缩放逐帧一样，所以身体在画布里画小了，上场就真的矮一截。
 2. 走路一上一下、左右乱滑 —— 各帧躯干高差 4~24 px，落脚线也不在同一条线上。
 3. 朝向两套标准 —— 主角/武士/头目朝右，足轻/多个村民朝左；代码只按一套
    规则翻转，于是总有一半角色是倒着走的。

处理办法（按「家族」= 一个角色）：
 * 朝向：家族内所有帧的头脸偏移取平均，向左偏超过 3px 就整族镜像成朝右；
   已处理过的家族记在状态文件里，重复运行不会翻回去。
 * 大小/定位：以家族所属「参照家族」的基准帧为准（村民共用一个参照，
   因为它们在 ART 里同一个 h，屏幕上本来就该一样高），把每一帧缩放到
   躯干高一致，再把「躯干底部中心」平移回参照的落脚线与身体中心。
 * @2x：按同一套几何变换（尺寸 ×2）处理，保持严格 2 倍。

原始文件先备份到 raw_assets/_anim_backup/（该目录不进版本库）。

用法：
    python tools/remaster_anim_frames.py            # 只报告
    python tools/remaster_anim_frames.py --apply    # 真正改写
"""
import io
import json
import os
import re
import shutil
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP = os.path.join(ROOT, 'raw_assets', '_anim_backup')
STATE = os.path.join(ROOT, 'tools', '_anim_remaster_state.json')
REPORT = os.path.join(ROOT, 'tools', '_anim_remaster.txt')

VILLAGER_DIR = 'assets/sprites/villagers'
ENEMY_DIR = 'assets/sprites/enemies'
PLAYER_DIR = 'assets/sprites/player'

# (家族, 目录, 参照家族)。参照家族的基准帧决定躯干高 / 落脚线 / 身体中心。
# 村民在 ART 里共用 h=50，所以在屏幕上必须一样高，统一拿 villager_idle 当尺子；
# kung_fu 的 padTop 是 0.318（画布留白完全不同，自带放大），单独当参照。
FAMILIES = [
    ('villager_idle', VILLAGER_DIR, 'villager_idle'),
    ('villager_farmer', VILLAGER_DIR, 'villager_idle'),
    ('villager_salt_worker', VILLAGER_DIR, 'villager_idle'),
    ('villager_builder', VILLAGER_DIR, 'villager_idle'),
    ('villager_militia', VILLAGER_DIR, 'villager_idle'),
    ('villager_kung_fu', VILLAGER_DIR, 'villager_kung_fu'),
    ('player', PLAYER_DIR, 'player'),
    ('enemy_scout', ENEMY_DIR, 'enemy_scout'),
    ('enemy_samurai', ENEMY_DIR, 'enemy_samurai'),
    ('enemy_boss', ENEMY_DIR, 'enemy_boss'),
]

CORE_HALF_RATIO = 0.14
CORE_HALF_MIN = 6
SCALE_MIN, SCALE_MAX = 0.88, 1.22
FACE_MIN_BIAS = 3.0
ALPHA_MIN = 24


def content_bbox(px, W, H, x0=0, x1=None):
    x1 = W - 1 if x1 is None else x1
    minx, maxx, miny, maxy = W, -1, H, -1
    for y in range(H):
        hit = False
        for x in range(x0, x1 + 1):
            if px[x, y][3] > ALPHA_MIN:
                if x < minx:
                    minx = x
                if x > maxx:
                    maxx = x
                hit = True
        if hit:
            if y < miny:
                miny = y
            maxy = y
    if maxx < 0:
        return None
    return (minx, maxx, miny, maxy)


def measure(im):
    """返回 (内容框, 躯干框, 头脸偏移)。偏移 > 0 表示朝右。"""
    W, H = im.size
    px = im.load()
    b = content_bbox(px, W, H)
    if b is None:
        return None, None, 0.0
    cx = (b[0] + b[1]) // 2
    half = max(CORE_HALF_MIN, int((b[1] - b[0] + 1) * CORE_HALF_RATIO))
    core = content_bbox(px, W, H, max(0, cx - half), min(W - 1, cx + half)) or b
    fcx = (b[0] + b[1]) / 2.0
    hb = b[2] + int((b[3] - b[2] + 1) * 0.30)
    n = sxm = 0
    for y in range(b[2], hb + 1):
        for x in range(b[0], b[1] + 1):
            if px[x, y][3] > ALPHA_MIN:
                sxm += x
                n += 1
    head_bias = (sxm / n) - fcx if n else 0.0
    esx = en = 0
    for y in range(b[2], hb + 1):
        for x in range(b[0] + 1, b[1]):
            r, g, bb, a = px[x, y]
            if a > 120 and r > 135 and g > 95 and r > bb + 22:
                esx += x
                en += 1
    skin_bias = (esx / en) - fcx if en else 0.0
    bias = head_bias + skin_bias
    if head_bias * skin_bias < 0:
        bias = head_bias if abs(head_bias) > abs(skin_bias) else skin_bias
    return b, core, bias


def frame_files(fam, dirrel):
    """家族下所有帧文件名（不含 @2x），按帧号排序。"""
    dirpath = os.path.join(ROOT, dirrel)
    if not os.path.isdir(dirpath):
        return []
    out = []
    for f in os.listdir(dirpath):
        if not f.endswith('.png') or '@2x' in f or not f.startswith(fam):
            continue
        m = re.match(r'^%s(_[a-z]+)?_(\d+)\.png$' % re.escape(fam), f)
        if m:
            out.append((m.group(1) or '', int(m.group(2)), f))
    # 只留同一「家族前缀」的：villager_idle 不会被 villager_idle_x 之外的东西污染
    return [f for _, _, f in sorted(out)]


def ref_name(frames, fam):
    for cand in (fam + '_01.png', fam + '_idle_01.png'):
        if cand in frames:
            return cand
    return frames[0]


def main():
    apply_changes = '--apply' in sys.argv
    state = {}
    if os.path.exists(STATE):
        state = json.load(io.open(STATE, encoding='utf-8'))
    mirrored = state.get('mirrored', [])
    lines = []

    # ---- 第一遍：量朝向，定镜像（不落盘）----
    fams = {}
    for fam, dirrel, gref in FAMILIES:
        frames = frame_files(fam, dirrel)
        if not frames:
            continue
        ref = ref_name(frames, fam)
        imgs = {}
        biases = []
        for f in frames:
            im = Image.open(os.path.join(ROOT, dirrel, f)).convert('RGBA')
            imgs[f] = im
            _, _, bias = measure(im)
            biases.append(bias)
        avg = sum(biases) / max(1, len(biases))
        already = fam in mirrored
        do_mirror = (not already) and avg < -FACE_MIN_BIAS
        fams[fam] = {
            'dir': dirrel, 'ref': ref, 'imgs': imgs, 'bias': avg,
            'mirror': do_mirror, 'mirrored_before': already, 'gref': gref,
        }

    # ---- 第二遍：参照家族的量尺 ----
    def targets(gref):
        d = fams[gref]
        im = d['imgs'][d['ref']]
        if d['mirror']:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        b, core, _ = measure(im)
        return {
            'core_h': core[3] - core[2] + 1,
            'foot': b[3],
            'cx': (core[0] + core[1]) / 2.0,
            'canvas': im.size,
            'ref': d['ref'],
        }

    SCALE_TOLERANCE = 0.06
    todo = []
    for fam, dirrel, gref in FAMILIES:
        if fam not in fams:
            continue
        d = fams[fam]
        t = targets(gref)
        lines.append('=== %s  基准 %s(%s)  %dx%d ===' % (
            fam, d['ref'], gref, d['imgs'][d['ref']].size[0], d['imgs'][d['ref']].size[1]))
        lines.append('   家族朝向偏移 %+.1f → %s' % (
            d['bias'],
            '整族镜像成朝右' if d['mirror'] else ('跳过（已镜像过）' if d['mirrored_before'] else '朝右，不动')))
        lines.append('   量尺：躯干高 %d  落脚线 y=%d  身体中心 x=%.1f' % (
            t['core_h'], t['foot'], t['cx']))
        W, H = d['imgs'][d['ref']].size
        for f in sorted(d['imgs']):
            im = d['imgs'][f]
            if im.size != (W, H):
                lines.append('   !! %s 画布 %dx%d 与基准 %dx%d 不一致，跳过' % (
                    f, im.size[0], im.size[1], W, H))
                continue
            mm = im.transpose(Image.FLIP_LEFT_RIGHT) if d['mirror'] else im
            b, core, _ = measure(mm)
            core_h = core[3] - core[2] + 1
            if f == d['ref'] and gref == fam:
                lines.append('   %-34s 躯干高 %3d  本组量尺，不动' % (f, core_h))
                continue
            # 只在姿势明显偏离时才缩放（蹲姿/倒地不宜按躯干高硬拉），
            # 而且缩放上限卡在「画布装得下」——宁可少缩放，绝不切掉拳脚
            s_raw = t['core_h'] / float(core_h)
            content_h = b[3] - b[2] + 1
            s_cap = (H - 1) / float(content_h)
            if '_fall' in f or '_crouch' in f or abs(s_raw - 1.0) <= SCALE_TOLERANCE:
                s = 1.0
                tag = '不缩放'
            else:
                s = max(SCALE_MIN, min(s_raw, s_cap, SCALE_MAX))
                tag = '×%.3f' % s
            nw = max(1, int(round((b[1] - b[0] + 1) * s)))
            nh = max(1, int(round((b[3] - b[2] + 1) * s)))
            # x 用「躯干中心」，y 用「脚底/内容底」——躯干定左右，脚底定落地
            core_cx = ((core[0] + core[1]) / 2.0 - b[0]) * s
            foot_in = (b[3] - b[2]) * s
            dx = t['cx'] - core_cx
            dy = t['foot'] - foot_in
            over = (max(0, -dx) + max(0, dx + nw - W) + max(0, -dy) + max(0, dy + nh - H))
            lines.append('   %-34s 躯干高 %3d %-8s 位移 %+5.1f,%+5.1f  出界 %d px'
                         % (f, core_h, tag, dx, dy, int(round(over))))
            todo.append((fam, dirrel, f, s, dx, dy, d['mirror']))
        lines.append('')

    io.open(REPORT, 'w', encoding='utf-8').write('\n'.join(lines))
    print('OK: %d 行 -> %s' % (len(lines), REPORT))
    print('   镜像家族 %d 个，需重排 %d 帧' % (
        sum(1 for f in fams if fams[f]['mirror']), len(todo)))
    for l in lines:
        if l.startswith('===') or '朝向偏移' in l or '量尺' in l or '!!' in l:
            sys.stdout.write(l.encode('ascii', 'replace').decode() + '\n')

    if not apply_changes:
        print('(report only; pass --apply to write)')
        return

    os.makedirs(BACKUP, exist_ok=True)

    def backup(p):
        dst = os.path.join(BACKUP, os.path.relpath(p, ROOT))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            shutil.copy2(p, dst)

    # 先镜像（1x 与 @2x 同时），再逐帧重排
    for fam in fams:
        if not fams[fam]['mirror']:
            continue
        d = fams[fam]
        for f in sorted(d['imgs']):
            p = os.path.join(ROOT, d['dir'], f)
            backup(p)
            Image.open(p).convert('RGBA').transpose(Image.FLIP_LEFT_RIGHT).save(p)
            hi = p[:-4] + '@2x.png'
            if os.path.exists(hi):
                backup(hi)
                Image.open(hi).convert('RGBA').transpose(Image.FLIP_LEFT_RIGHT).save(hi)
        mirrored.append(fam)

    for (fam, dirrel, f, s, dx, dy, mir) in todo:
        p = os.path.join(ROOT, dirrel, f)
        backup(p)
        im = Image.open(p).convert('RGBA')
        b, core, _ = measure(im)
        crop = im.crop((b[0], b[2], b[1] + 1, b[3] + 1))
        crop = crop.resize((max(1, int(round(crop.width * s))),
                            max(1, int(round(crop.height * s)))), Image.LANCZOS)
        new = Image.new('RGBA', im.size, (0, 0, 0, 0))
        new.paste(crop, (int(round(dx)), int(round(dy))), crop)
        new.save(p)
        hi = p[:-4] + '@2x.png'
        if os.path.exists(hi):
            backup(hi)
            him = Image.open(hi).convert('RGBA')
            hb, _, _ = measure(him)
            hc = him.crop((hb[0], hb[2], hb[1] + 1, hb[3] + 1))
            hc = hc.resize((max(1, int(round(hc.width * s))),
                            max(1, int(round(hc.height * s)))), Image.LANCZOS)
            hn = Image.new('RGBA', (im.size[0] * 2, im.size[1] * 2), (0, 0, 0, 0))
            hn.paste(hc, (int(round(dx * 2)), int(round(dy * 2))), hc)
            hn.save(hi)

    state['mirrored'] = mirrored
    json.dump(state, io.open(STATE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已应用。原图备份：raw_assets/_anim_backup/')


if __name__ == '__main__':
    main()
