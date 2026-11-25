# -*- coding: utf-8 -*-
"""审计 assets 里每张美术素材的「上屏清晰度」，找出大小/清晰度不统一的资源。

判据（统一标准，全项目同一把尺子）：
    清晰度 = 贴图有效内容像素 / 上屏像素
    上屏像素 = 设计单位 * zoom
  > 1.0 -> 贴图比屏幕大，缩放后很锐（推荐 >= 1.2）
  0.7~1.0 -> 勉强够
  < 0.7  -> 上屏被放大，糊

zoom 默认取 Screen.WORLD_ZOOM * (1920/1280) 附近的常见值，可用参数覆盖：
    python tools/audit_scale.py 2.66
不传则读取 src/config/Screen.ts 的 WORLD_ZOOM，按 1920x1080 窗口估算。

贴图优先用同目录的 @2x（运行时就是这么取图的）。
"""
import io, os, re, sys
from PIL import Image

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJ)
SRC = io.open('src/config/Assets.ts', encoding='utf-8').read()

ENTRY = re.compile(r"'([A-Za-z0-9_]+)':\s*\{([^}]*)\}")
FIELD = re.compile(r"(\w+):\s*('[^']*'|[-\d.]+|true|false)")

ART = []
for m in ENTRY.finditer(SRC):
    aid, body = m.group(1), m.group(2)
    d = {'id': aid}
    for fm in FIELD.finditer(body):
        k, v = fm.group(1), fm.group(2)
        if v.startswith("'"):
            d[k] = v[1:-1]
        elif v in ('true', 'false'):
            d[k] = (v == 'true')
        else:
            d[k] = float(v)
    if 'path' in d:
        ART.append(d)


def guess_zoom():
    if len(sys.argv) > 1:
        return float(sys.argv[1])
    z = 1.4
    m = re.search(r'WORLD_ZOOM\s*=\s*([-\d.]+)', io.open('src/config/Screen.ts', encoding='utf-8').read())
    if m:
        z = float(m.group(1))
    # 1920x1080 窗口：fit = min(1920/1280, 1080/720) = 1.5
    return z * 1.5


ZOOM = guess_zoom()


def group_of(aid):
    for p, g in (
        ('villager_', '角色·族丁'), ('player_', '角色·主角'), ('enemy_', '角色·倭寇'),
        ('lm_', '建筑·地标'), ('tower_', '建筑·敌台'), ('proj_', '道具·投射'),
        ('salvage_', '道具·拾取'), ('tool_', '道具·工具'), ('fx_', '特效'),
        ('icon_', 'UI·图标'), ('ui_', 'UI·控件'), ('sky_', '背景'), ('ground_', '背景'),
        ('night_mask', '背景'), ('horizon', '背景'), ('mid_houses', '背景'),
        ('title_bg', '背景'), ('over_', '背景'),
    ):
        if aid.startswith(p):
            return g
    return '其他'


def load(path):
    """返回 (1x 尺寸, @2x 尺寸或 None, 实际使用的那张的内容 bbox)。"""
    hi = path[:-4] + '@2x.png' if path.endswith('.png') else ''
    use = hi if hi and os.path.exists(hi) else path
    if not os.path.exists(use):
        return None, None, None, None
    img = Image.open(use)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    bb = img.getchannel('A').getbbox()
    one = Image.open(path).size if os.path.exists(path) else None
    two = Image.open(hi).size if hi and os.path.exists(hi) else None
    return one, two, img.size, bb


rows = []
for e in ART:
    one, two, size, bb = load(e['path'])
    if size is None:
        rows.append((e, 'MISSING', 0.0, None, None))
        continue
    if bb is None:
        bb = (0, 0, size[0], size[1])
    cw, ch = bb[2] - bb[0], bb[3] - bb[1]
    # 设计单位：h/w 有就用，否则用贴图本身（stretch 类按 1x 宽度估）
    if 'h' in e:
        units = float(e['h']) if ch else 1.0
        upx = units * ZOOM
        sharp = ch / upx
        ref = 'h=%g' % e['h']
    elif 'w' in e:
        units = float(e['w'])
        upx = units * ZOOM
        sharp = cw / upx
        ref = 'w=%g' % e['w']
    elif e['id'].startswith(('sky_', 'night_mask', 'title_bg', 'over_', 'ui_top_bar', 'ui_bottom_bar')):
        # 铺满整屏的背景 / 顶底栏：实际被拉伸到窗口宽度（参考窗口 1920）
        upx = 1920.0
        sharp = cw / upx
        ref = '整屏宽'
    else:
        # 其余拉伸类（按钮/弹窗/血条）：尺寸由调用处决定，不做清晰度判定
        upx = 0.0
        sharp = 0.0
        ref = 'stretch'
    rows.append((e, 'ok', sharp, (size[0], size[1], cw, ch), (one, two), ref))


def fmt(e, st, sharp, dims, tex, ref=''):
    tag = ''
    if tex and tex[1]:
        tag = '@2x'
    elif tex:
        tag = '1x '
    if st != 'ok':
        return '%-26s %-44s %s' % (e['id'], e['path'], st)
    W, H, cw, ch = dims
    if ref == 'stretch':
        return '%-26s %-44s %s tex %4dx%-4d content %4dx%-4d 清晰度   --（拉伸，按调用尺寸）' % (
            e['id'], e['path'], tag, W, H, cw, ch)
    warn = ''
    if sharp < 0.7:
        warn = ' <== 糊'
    elif sharp < 1.0:
        warn = ' < 偏软'
    return '%-26s %-44s %s tex %4dx%-4d content %4dx%-4d 清晰度 %5.2f%s' % (
        e['id'], e['path'], tag, W, H, cw, ch, sharp, warn)


lg = sys.argv[2] if len(sys.argv) > 2 else ''
out = ['镜头 zoom = %.2f（清晰度 = 贴图内容像素 / 上屏像素）' % ZOOM, '']

# 按类分组，组内按清晰度排序
groups = {}
for e, st, sharp, dims, tex, ref in rows:
    groups.setdefault(group_of(e['id']), []).append((e, st, sharp, dims, tex, ref))

bad = []
for g in sorted(groups):
    items = sorted(groups[g], key=lambda x: (x[2], x[0]['id']))
    out.append('== %s ==' % g)
    for e, st, sharp, dims, tex, ref in items:
        if lg and not e['id'].startswith(lg):
            continue
        out.append(fmt(e, st, sharp, dims, tex, ref))
        if st == 'ok' and ref != 'stretch' and sharp < 1.0:
            bad.append((sharp, e['id']))
    out.append('')

out.append('== 需要重出的资源（清晰度 < 1.0，共 %d 项）==' % len(bad))
for sharp, aid in sorted(bad):
    out.append('  %5.2f  %s' % (sharp, aid))

txt = '\n'.join(out)
io.open('docs/_asset_scale.txt', 'w', encoding='utf-8').write(txt + '\n')
sys.stdout.write(txt.encode('ascii', 'replace').decode('ascii') + '\n')
