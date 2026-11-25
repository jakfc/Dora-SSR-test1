# tools 目录说明

这些脚本都是「改代码 / 换素材之后自检」用的，不参与游戏运行。全部用系统 Python 3
（需要 `Pillow`、`numpy`、`scipy`：`pip install pillow numpy scipy`）。命令都在**项目根目录**执行。

| 脚本 | 干什么 | 什么时候跑 |
| --- | --- | --- |
| `gen_asset_table.py` | 读 `src/config/Assets.ts` 的 `ART` 表，生成 `docs/素材替换对照表.md`（id → 文件路径 → 设计尺寸） | 增删素材 id 之后。CI 会校验文档与代码一致 |
| `lint_assets.py` | 检查「代码里引用的素材 id 是否都在 `ART` 表里」+「`ART` 表里的文件是否真的存在」+ 列出没用到的图 | 提交前，CI 也会跑 |
| `audit_padding.py` | 重新算每张图的真实留白，和 `padTop/padBottom` 对照，列出需要校准的条目 | **重画素材之后**（尺寸一变留白就变了） |
| `audit_scale.py` | 列每张图「显示尺寸 ÷ 素材像素」的 px/unit，看比例是否统一（角色同高、建筑同一比例） | 调整 `ART` 表尺寸 / 换素材后 |
| `audit_2x.py` | 盘点哪些图有 `@2x` 主稿、哪些只有 1x（附逐帧动画帧数统计） | 补主稿后；决定「下一批画什么」时 |
| `ascii_preview.py` | 把 PNG 的轮廓打成 ASCII 图，用来在没有看图工具时判断构图/朝向 | 收到新图、想知道它长什么样时 |
| `inspect_scene.py` | 启动游戏 → 把**运行中**的场景树倒出来（精灵尺寸/坐标 + 文字）到 `docs/_scene_dump.txt` | 想确认「素材到底有没有被画出来、画在哪、多大」时 |
| `dump_scene.lua` | 上面那个脚本用的 Lua 片段（也可自己用 `cli agent command` 跑） | 一般不用手改 |
| `generate_all_assets.py` | 早期批量生成占位素材的脚本（保留做参考） | 基本不用 |
| `generate_missing_abc.py`、`redraw_yongchang_assets.py` | 生成 / 重画 A/B/C 组素材的脚本（保存 prompt 与参数） | 想重跑生成时 |
| `process_gemini_sprites.py`、`process_flow_batch.py` | 把外部生成的大图切帧、去背、缩放成项目要的尺寸 | 拿到 AI 生成的新图之后 |
| `regen_bg_ai.py` | 重出背景层（天空 / 地面 / 远景）：白底抠图 → 去白边 → 边缘补色 → 1x + `@2x`。已有原图时加 `--post` 可以**只重跑后处理、不重新调 AI**（改抠图/裁切参数后常用） | 想重画背景、或重新处理手头的背景原图时 |
| `upgrade_bg_pro.py` | 背景层的 AI 生成脚本（保存着每张背景的提示词与参数，比 `regen_bg_ai.py` 更激进的一套重出流程） | 想按提示词重出背景时 |
| `redo_all_walks_from_video.py` | 从参考视频逐帧抽出行走动作，对齐底座后写成 6 帧 `*_walk_01..06.png`（1x + @2x） | 想重做/加帧行走动画时 |
| `generate_audio_assets.py` | 合成全部 BGM / 音效（`.wav`，写到 `assets/audio/`），参数与清单都在脚本里 | 想重出/改音频时 |
| `_probe_audio.py` | 音频运行时自检：逐个 `Content.exist` + 真的开播，报告缺失/播不出的文件 | 换音频之后 |

## 常用自检流程（换素材之后）

```bash
python tools/lint_assets.py        # 1. 素材 id / 文件是否对得上
python tools/audit_padding.py      # 2. 留白是否需要重新校准
python tools/audit_scale.py        # 3. 显示比例（px/unit）是否统一
python tools/audit_2x.py           # 4. 还缺哪些 @2x 主稿
python tools/inspect_scene.py      # 5. 跑起来，倒出场景树核对
python tools/_probe_audio.py       # 6. 音频自检：文件在不在、能不能开播
```

`inspect_scene.py` 需要引擎可执行文件路径，默认用安装版
`C:\Users\jakfc\AppData\Local\Programs\Dora SSR\Dora.exe`；装在别处就设环境变量：

```bash
set DORA_EXE=D:\Dora SSR\Dora.exe
python tools/inspect_scene.py
```

第二个参数可以换启动入口（默认 `init_game`）：

```bash
python tools/inspect_scene.py init      # 从标题页开始
python tools/inspect_scene.py init_art   # 只跑美术预览入口
```

输出里 `SPR tex 320x760 draw 160.0x380.0 pos 80,160` 表示「这张 320×760 的图被画成
160×380，中心点在世界坐标 (80,160)」——就是对素材是否生效、尺寸是否正确的直接证据。
