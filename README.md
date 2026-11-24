# 永昌堡：铁血筑城

一款以明代温州**永昌堡**抗倭为背景的横版**经营 + 塔防**小游戏，使用 [Dora SSR](https://github.com/IppClub/Dora-SSR) 引擎 + TypeScript 开发。

白天招募族丁、耕作煮盐、修城造炮；入夜倭寇自东海登陆，凭城墙与敌台御敌。撑过 **8 个昼夜**即为通关。

```
白天 45 秒：经营、建设、招募       黄昏警示 → 入夜：倭寇数波来袭
资源：白银 / 粮草 / 人口            地标：宗祠 · 盐课司 · 内城水门 · 主城墙 · 东门瓮城
角色：王叔杲（主角）· 农夫 · 灶丁 · 工匠 · 民兵 · 拳师
```

## 快速开始

### 1. 安装引擎

下载并安装 **Dora SSR**（Windows 安装版即可）：

- 官方发布页：<https://github.com/IppClub/Dora-SSR/releases>
- 安装后从开始菜单启动 `Dora SSR`，它会同时开一个本机网页 IDE：<http://localhost:8866>

### 2. 放置工程

把本仓库克隆到引擎的工程目录下（目录名随意，例如 `yongchangbao`）：

```bash
cd "%AppData%\IppClub\DoraSSR"
git clone https://github.com/jakfc/Dora-SSR-test1.git yongchangbao
```

### 3. 编译并运行

首次运行前必须先把 TypeScript 编译成 Lua（`.lua` 是构建产物，不在仓库里）：

```bash
# Windows：在引擎安装目录下执行（或用开始菜单里的 dora 命令行）
dora cli build -p "%AppData%\IppClub\DoraSSR\yongchangbao"
dora cli buildrun -p "%AppData%\IppClub\DoraSSR\yongchangbao" --entry init
```

也可以直接打开 <http://localhost:8866>，在文件树里选中工程后点 **编译 / 运行**，入口选 `init`。

### 4. 操作

| 按键 | 作用 |
| --- | --- |
| `A` / `D` | 左右移动 |
| `E` | 交互（招募族丁、拾取工具、采集物资） |
| `J` | 麒麟步（突进） |
| `K` | 鸣鼓集结（族丁归位） |
| 鼠标点击/触摸 | 移动到指定位置 |

## 目录结构

```
init.ts                  游戏入口（先编译再运行）
tsconfig.json            TS 配置
src/
  config/GameConfig.ts   所有数值的唯一来源（时长、地图、波次、颜色……）
  config/GameState.ts    运行时状态（资源、昼夜、进度）
  config/Screen.ts       分辨率适配（按实际视口换算，勿再写死 1280x720）
  config/Assets.ts       美术资源接入层：所有贴图路径 + 目标尺寸都在这里
  entities/              Player / Villager / Enemy / DefenseTower
  scenes/                SceneManager / TitleScene / GameScene / GameOverScene
  ui/HudLayer.ts         HUD（顶栏、底栏、按钮、图标）
assets/                  美术资源（不含空白底，直接可用）
  bg/  buildings/  sprites/{player,villagers,enemies,props,tools}  ui/  ui/icons/
  gemini/                AI 出图原始稿（美术溯源自留，不影响运行）
docs/                    设计规范与素材文档
tools/                   素材生成、处理、校验脚本
API/Dora.d.ts            引擎导出的类型声明（提供编辑器补全）
```

## 开发流程

1. 改 `src/**/*.ts`；
2. **编译**：`dora cli build -p <工程路径>`（只改一个文件时可用 `-f src/xxx.ts` 增量编译）；
3. 运行看效果，或抓帧核对：`dora cli agent preview -p <工程路径> --entry init --capture-at 1,4,9`；
4. 提交。**只提交 `.ts`，不要提交 `.lua`**。

> 没改完就别提交 `.lua`；如果本地出现「改了代码但游戏没变化」，先删掉对应的 `.lua` 重新编译。

## 美术资源怎么接

所有贴图的路径、目标尺寸、对齐方式都集中在 **`src/config/Assets.ts`**：

- **换图不用改代码**：把同名文件放到对应路径即可（例如 `assets/sprites/player/player_idle_01.png`）；
- **文件缺失不报错**：会自动回退成程序化色块，所以可以一张一张慢慢补；
- 想改尺寸/对齐，改 `Assets.ts` 里对应条目的 `w` / `h` / `padTop` / `padBottom` / `cropTop`。

素材规格与待补清单：

- [`docs/美术素材清单与AI生成规范.md`](docs/美术素材清单与AI生成规范.md) —— 尺寸、色板、风格总规范
- [`docs/素材替换对照表.md`](docs/素材替换对照表.md) —— 全部 70+ 个资源 id ↔ 文件路径（`python tools/gen_asset_table.py` 自动生成）
- [`docs/待补美术资源清单.md`](docs/待补美术资源清单.md) —— 还缺哪些图、按什么规格画

## 参与开发

见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。简单说：从 `main` 切分支 → 提交前跑 `python tools/lint_assets.py` → 开 PR 等一个人 review。

## 授权

- 代码：MIT，见 [`LICENSE`](LICENSE)
- 美术素材（`assets/`、`docs/` 内图片）：CC BY-NC-SA 4.0，署名「永昌堡项目组」
- `参考/` 目录的资料来自公开出版物与地方文献，**仅供内部参考，不随仓库分发**
