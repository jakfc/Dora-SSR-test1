# tools 目录说明

这些脚本都是「改代码 / 换素材之后自检」用的，不参与游戏运行。全部用系统 Python 3（需要 `Pillow`：
`pip install pillow`）。命令都在**项目根目录**执行。

| 脚本 | 干什么 | 什么时候跑 |
| --- | --- | --- |
| `gen_asset_table.py` | 读 `src/config/Assets.ts` 的 `ART` 表，生成 `docs/素材替换对照表.md`（id → 文件路径 → 设计尺寸） | 增删素材 id 之后。CI 会校验文档与代码一致 |
| `lint_assets.py` | 检查「代码里引用的素材 id 是否都在 `ART` 表里」+「`ART` 表里的文件是否真的存在」+ 列出没用到的图 | 提交前，CI 也会跑 |
| `audit_padding.py` | 重新算每张图的真实留白，和 `padTop/padBottom` 对照，列出需要校准的条目 | **重画素材之后**（尺寸一变留白就变了） |
| `ascii_preview.py` | 把 PNG 的轮廓打成 ASCII 图，用来在没有看图工具时判断构图/朝向 | 收到新图、想知道它长什么样时 |
| `inspect_scene.py` | 启动游戏 → 把**运行中**的场景树倒出来（精灵尺寸/坐标 + 文字）到 `docs/_scene_dump.txt` | 想确认「素材到底有没有被画出来、画在哪、多大」时 |
| `dump_scene.lua` | 上面那个脚本用的 Lua 片段（也可自己用 `cli agent command` 跑） | 一般不用手改 |
| `generate_all_assets.py` | 早期批量生成占位素材的脚本（保留做参考） | 基本不用 |
| `generate_missing_abc.py`、`redraw_yongchang_assets.py` | 生成 / 重画 A/B/C 组素材的脚本（保存 prompt 与参数） | 想重跑生成时 |
| `process_gemini_sprites.py`、`process_flow_batch.py` | 把外部生成的大图切帧、去背、缩放成项目要的尺寸 | 拿到 AI 生成的新图之后 |

## 常用自检流程（换素材之后）

```bash
python tools/lint_assets.py        # 1. 素材 id / 文件是否对得上
python tools/audit_padding.py      # 2. 留白是否需要重新校准
python tools/inspect_scene.py      # 3. 跑起来，倒出场景树核对
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
