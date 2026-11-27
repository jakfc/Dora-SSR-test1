# -*- coding: utf-8 -*-
"""把角色各动作帧的「内容大小」对齐到同一档，修掉「攻击时角色突然变小」。

症状：同一个角色的帧画布尺寸一样（都是 128x192），但生成时有的动作把人物画小了
（player_idle 内容高 176，player_attack 只有 110），于是 play 到攻击帧整个人缩一圈。

做法：
  1. 每个角色以 **idle 帧** 为基准（比例对账就是按它标定的），内容高 = ref_h，
     底边 = ref_bottom（脚站的线）。
  2. 别的动作帧量出内容高 h 和底边 b；只有偏离超过容差（默认 20%）才动它。
  3. 按 k = ref_h / h 缩放内容，再把它贴回画布，让底边回到 ref_bottom、水平中心不变。
  4. 1x 与 @2x 各自独立跑同一套（@2x 的框正好是 1x 的两倍，k 相同，天然保持严格 2 倍）。

用法：
  python tools/normalize_anim_frames.py            # 只体检，列出需要修的帧
  python tools/normalize_anim_frames.py --apply    # 真的改图
  python tools/normalize_anim_frames.py --apply --tol 0.12
"""
import argparse
import glob
import io
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPR = os.path.join(ROOT, 'assets', 'sprites')
OUT = io.open(os.path.join(ROOT, 'tools', '_anim_norm.txt'), 'w', encoding='utf-8')

# 角色分组：(目录, 站姿前缀, [动作前缀...])
# 站姿帧 = 站姿前缀 + _NN；动作帧 = 动作前缀 + _NN
def _v(role):
    s = 'villager_' + role
    return ('villagers', s, [s + '_walk', s + '_work', s + '_attack'])

ROLES = [
    ('player', 'player_idle', ['player_walk', 'player_attack', 'player_qilin', 'player_hurt']),
    _v('idle'),
    _v('farmer'),
    _v('salt_worker'),
    _v('builder'),
    _v('militia'),
    _v('kung_fu'),
    ('enemies', 'enemy_scout', ['enemy_scout_walk', 'enemy_scout_attack', 'enemy_scout_fall']),
    ('enemies', 'enemy_samurai', ['enemy_samurai_walk', 'enemy_samurai_attack', 'enemy_samurai_fall']),
    ('enemies', 'enemy_boss', ['enemy_boss_walk', 'enemy_boss_attack', 'enemy_boss_fall']),
]

# 这些动作本来就是「躺下/趴下」，比站姿矮是应该的：只对齐底边，不拉高
NO_HEIGHT = ['_fall', '_die', '_death']
# 缩放系数硬边界：超过就说明这一帧不是「画小了」而是别的问题，跳过并报出来
K_MIN, K_MAX = 0.7, 2.1

def log(s=''):
    OUT.write(s + '\n')
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('ascii', 'replace').decode('ascii'))


def frames_of(folder, prefix):
    """某一前缀的帧文件（按编号排序）。"""
    return sorted(glob.glob(os.path.join(SPR, folder, prefix + '_[0-9][0-9].png')))


def bbox_of(path):
    im = Image.open(path).convert('RGBA')
    bb = im.getbbox()
    return im, bb


def _shift_bottom(path, ref_bottom):
    """把整帧内容上下平移，让内容底边落到 ref_bottom（不改大小）。"""
    im = Image.open(path).convert('RGBA')
    bb = im.getbbox()
    if bb is None:
        return
    dy = ref_bottom - bb[3]
    if dy == 0:
        return
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    out.paste(im, (0, dy), im)
    out.save(path)


def normalize_one(path, ref_h, ref_bottom, tol, apply_):
    im, bb = bbox_of(path)
    w, h = im.size
    if bb is None:
        return None
    ch = bb[3] - bb[1]
    if ch <= 0:
        return None
    k = ref_h / float(ch)
    need = abs(1.0 - k) > tol
    if not need:
        return (ch, bb[3], k, False)
    if not apply_:
        return (ch, bb[3], k, True)
    # 裁出内容 → 缩放 → 贴回（底边对齐 ref_bottom，水平中心不变）
    content = im.crop(bb)
    nw = max(1, int(round(content.size[0] * k)))
    nh = max(1, int(round(content.size[1] * k)))
    content = content.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    cx = (bb[0] + bb[2]) // 2
    px = int(round(cx - nw / 2.0))
    py = int(round(ref_bottom - nh))
    # 允许超出画布（后面裁），先贴再裁
    canvas.paste(content, (px, py), content)
    canvas = canvas.crop((0, 0, w, h))
    canvas.save(path)
    return (ch, bb[3], k, True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='真的改图（默认只体检）')
    ap.add_argument('--tol', type=float, default=0.2, help='容差：内容高偏离 idle 超过这个比例才修')
    args = ap.parse_args()

    total_fix = 0
    skipped = 0
    for folder, stand, actions in ROLES:
        if not os.path.isdir(os.path.join(SPR, folder)):
            continue
        stand_files = frames_of(folder, stand)
        if not stand_files:
            log('  %-28s 没有站姿帧，跳过' % stand)
            continue
        _, ibb = bbox_of(stand_files[0])
        if ibb is None:
            continue
        ref_h = ibb[3] - ibb[1]
        ref_bottom = ibb[3]
        log('=== %-24s 基准站姿 内容高 %d 底边 %d ===' % (stand, ref_h, ref_bottom))
        for prefix in [stand] + list(actions):
            is_fall = any(prefix.endswith(s) for s in NO_HEIGHT)
            for f in frames_of(folder, prefix):
                rel = os.path.relpath(f, ROOT).replace(chr(92), '/')
                hi = f[:-4] + '@2x.png'
                act = ('stand' if prefix == stand else prefix.replace(stand + '_', '', 1))
                if is_fall:
                    # 躺着/倒下的帧：只把底边对齐，不改高度
                    im, bb = bbox_of(f)
                    if bb is not None and bb[3] != ref_bottom and args.apply:
                        _shift_bottom(f, ref_bottom)
                        if os.path.exists(hi):
                            _shift_bottom(hi, ref_bottom * 2)
                    log('   %-44s %-8s (倒下帧：只对齐底边)' % (rel, act or 'stand'))
                    continue
                r = normalize_one(f, ref_h, ref_bottom, args.tol, args.apply)
                if r is None:
                    continue
                ch, bottom, k, fixed = r
                if fixed and not (K_MIN <= k <= K_MAX):
                    skipped += 1
                    log('   %-44s %-8s 内容高 %3d (%.2fx) k=%.2f 超出 [%.1f,%.1f]，跳过'
                        % (rel, act or 'stand', ch, ch / float(ref_h), k, K_MIN, K_MAX))
                    continue
                if fixed:
                    total_fix += 1
                    log('   %-44s %-8s 内容高 %3d (%.2fx) 底边 %3d -> 缩放 %.3f'
                        % (rel, act or 'stand', ch, ch / float(ref_h), bottom, k))
                    if os.path.exists(hi):
                        normalize_one(hi, ref_h * 2, ref_bottom * 2, args.tol, args.apply)
                else:
                    log('   %-44s %-8s 内容高 %3d (%.2fx) 合格' % (rel, act or 'stand', ch, ch / float(ref_h)))
    log('')
    log('%s：需要修/已修 %d 帧，跳过 %d 帧' % ('已应用' if args.apply else '体检', total_fix, skipped))


if __name__ == '__main__':
    main()
