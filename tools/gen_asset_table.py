#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从 src/config/Assets.ts 的 ART 表生成 docs/素材替换对照表.md。

用法（项目根目录下）：python tools/gen_asset_table.py
"""
import io
import os
import re
import sys

SRC = 'src/config/Assets.ts'
OUT = 'docs/素材替换对照表.md'


def grab(body, key):
    m = re.search(r"(?:^|\{|,)\s*%s:\s*'?([^,'}]*?)'?\s*(?:,|$)" % key, body)
    if not m:
        return None
    v = m.group(1).strip()
    return v or None


def parse():
    s = io.open(SRC, encoding='utf-8').read()
    out = []
    for m in re.finditer(r"\t'([A-Za-z0-9_]+)':\s*\{([^}]*)\}", s):
        body = m.group(2)
        e = {'id': m.group(1)}
        for k in ('path', 'w', 'h', 'stretch', 'padTop', 'padBottom', 'cropTop', 'flipX'):
            v = grab(body, k)
            if v:
                e[k] = v
        out.append(e)
    return out


GROUPS = [
    ('背景 / 天空 / 地面 / 远景', ('sky_', 'night_mask', 'ground_', 'horizon')),
    ('地标建筑与敌台', ('lm_', 'tower_')),
    ('人物（玩家 / 族丁 / 倭寇）', ('player_', 'villager_', 'enemy_')),
    ('投射物 / 工具 / 物资 / 特效', ('proj_', 'tool_', 'salvage_', 'fx_')),
    ('UI 面板 / 按钮 / 图标', ('ui_', 'icon_')),
]

EXTRA = [
    ('盐课司 b03（现为色块）', '`assets/buildings/b03_salt_office.png`，建议 340×300，底边贴地'),
    ('主城墙 b05（现为色块）', '`assets/buildings/b05_main_wall.png`，建议 360×320，底边贴地'),
    ('大罗山远景 b09（现为色块）', '`assets/bg/b09_daluo_mountain.png`，建议 320×760，底边贴地'),
    ('城外盐田与滩涂 b10（现为色块）', '`assets/bg/b10_outer_salt_flat.png`，建议 1120×120'),
    ('东海海岸 b11（现为色块）', '`assets/bg/b11_coast.png`，建议 520×160'),
    ('东门/水门破损态', '`assets/buildings/b06_east_gate_broken.png`、`b04_inner_water_gate_broken.png`（现在用色块表示受损）'),
    ('宗祠 / 敌台升级态', '`b01_shrine_lv2.png`、`b07_tower_arrow_lv2.png`、`b08_tower_cannon_lv2.png`（现在升级只换色）'),
    ('敌人血条 / 塔耐久条 / 族丁状态条', '`ui/e07_bar_health.png` 已有；建议再补空槽与绿色（劳作）、蓝色（修复）两张'),
    ('底部提示气泡', '`ui/e09_prompt_bubble.png` 已有图，尚未挂到 HUD（现为纯文字）'),
    ('按钮 hover / pressed / disabled', '`ui/e04_btn_hover.png` 等已有图，尚未接状态切换'),
    ('鼠标光标', '`ui/e12_cursor.png` 已有图，尚未接入'),
]


def main():
    entries = parse()
    lines = [
        '# 素材替换对照表',
        '',
        '> 本表由 `src/config/Assets.ts` 的 `ART` 表自动生成（`python tools/gen_asset_table.py`）。',
        '> 替换素材**不需要改代码**：把同名文件放到「文件路径」即可（按「设计尺寸」作画，画布建议 2 倍）。',
        '> 文件不存在（标 ❌）时游戏会自动回退成程序化色块，不会报错——所以可以一张一张慢慢补。',
        '',
    ]
    used = set()
    for title, prefixes in GROUPS:
        rows = [e for e in entries if any(e['id'].startswith(p) for p in prefixes) and e['id'] not in used]
        for e in rows:
            used.add(e['id'])
        if not rows:
            continue
        lines += ['## ' + title, '',
                  '| 资源 id | 文件路径 | 设计尺寸 | 备注 | 文件 |',
                  '| --- | --- | --- | --- | --- |']
        for e in rows:
            if e.get('stretch') == 'true':
                size = '拉伸铺满容器'
            elif e.get('w') and e.get('h'):
                size = '%s × %s px' % (e['w'], e['h'])
            elif e.get('w'):
                size = '宽 %s px（高按原比例）' % e['w']
            elif e.get('h'):
                size = '高 %s px（宽按原比例）' % e['h']
            else:
                size = '按原图像素'
            note = []
            if e.get('cropTop'):
                note.append('裁掉顶部 %s（开门态复用同图）' % e['cropTop'])
            if e.get('padTop') or e.get('padBottom'):
                note.append('已按图内留白对齐地平线')
            if e.get('flipX') == 'true':
                note.append('水平翻转')
            path = e.get('path', '')
            ok = '✅' if path and os.path.exists(path) else '❌ 待补'
            lines.append('| `%s` | `%s` | %s | %s | %s |' % (
                e['id'], path or '-', size, '；'.join(note) or '—', ok))
        lines.append('')

    lines += ['## 表格之外还需要的东西', '', '| 用途 | 需要文件 |', '| --- | --- |']
    for a, b in EXTRA:
        lines.append('| %s | %s |' % (a, b))
    lines.append('')

    io.open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
    total = len(entries)
    miss = sum(1 for e in entries if not e.get('path') or not os.path.exists(e['path']))
    sys.stdout.write('OK: %d entries, %d missing -> %s\n' % (total, miss, OUT))


if __name__ == '__main__':
    main()
