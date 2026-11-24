# 参与开发

感谢一起做《永昌堡：铁血筑城》！下面是最少必要的一套规矩，照做就能顺畅协作。

## 分工与权限

| 角色 | 能做什么 | 建议权限 |
| --- | --- | --- |
| 维护者（@jakfc） | 合并 PR、发版、改仓库设置 | Admin |
| 策划 / 程序 | 切分支、提 PR、开 issue | Write |
| 美术 | 只提交 `assets/` 与 `docs/` 下的图 | Write（或只提 PR） |
| 外部围观 | 提 issue、评论、fork | Read |

**不要在 `main` 上直接改东西。** `main` 已设为受保护分支，只接受 PR。

## 一次改动的完整流程

```bash
git clone https://github.com/jakfc/Dora-SSR-test1.git
cd Dora-SSR-test1
git checkout -b feat/night-wave-balance     # 分支名见下

# ……改代码 / 换素材……

dora cli build -p "<本仓库绝对路径>"          # 必须先编译，确认 0 error
python tools/lint_assets.py                  # 改了素材或 Assets.ts 就跑一下

git add -A
git commit -m "fix: 第 5 夜倭寇数量过高"
git push -u origin feat/night-wave-balance
# 然后在 GitHub 上开 Pull Request
```

分支命名：`feat/xxx`（新功能）、`fix/xxx`（修 bug）、`art/xxx`（换美术）、`docs/xxx`、`chore/xxx`。

提交信息：`feat: / fix: / art: / docs: / refactor: / chore:` 开头，一行说清做了什么。

## 硬性规矩

1. **不要提交 `.lua`**。它是 TS 编译产物，`.gitignore` 已忽略；交上去会导致别人跑的是旧代码。
2. **不要直接改 `GameConfig.ts` 里的数值去「临时试一下」**。要调平衡就改数值说明 + 在 PR 描述里给出前后对比。
3. **不要写死 1280×720**。画面尺寸一律走 `src/config/Screen.ts`（`Screen.width/height`），否则高分屏会错位。
4. **新增贴图必须登记进 `src/config/Assets.ts`**，不要在别处硬编码路径。
5. **不要提交** `参考/`（文献照片，有版权）和 `raw_assets/*.tar.gz`（第三方素材包，来源待确认）。
6. 大头文件（>5 MB）先问维护者，避免仓库膨胀。

## 美术同学怎么提交

只需要图，不用碰代码：

1. 把文件按 [`docs/待补美术资源清单.md`](docs/待补美术资源清单.md) 里的**「丢到哪」路径**放好（命名必须一致）；
2. 若要新增一个全新的资源，在 issue 里说明用途与尺寸，由维护者在 `Assets.ts` 里加一行 id；
3. 提 PR：标题写 `art: 补盐课司与主城墙`，描述里贴一张游戏内截图（或把图发到 issue 里）。

**换图不需要改代码、不需要重编译**——文件放对位置就生效，缺图会自动回退成色块。

## PR 检查清单

- [ ] `dora cli build` 编译 0 error
- [ ] 游戏能正常跑起来，改动处已截图/抓帧确认
- [ ] 没有提交 `.lua`、`参考/`、`raw_assets/*.tar.gz`
- [ ] 新增数值写进了 `GameConfig.ts`，没有散落在逻辑里
- [ ] 改了 `Assets.ts` 时，跑过 `python tools/gen_asset_table.py` 和 `tools/lint_assets.py`
- [ ] 至少一位维护者 review 通过

## 有想法 / 发现 bug

用 issue 模板提（`.github/ISSUE_TEMPLATE/`）：
**美术资源**（要画什么）、**功能需求**（想要什么玩法）、**缺陷**（哪里不对）。
美术需求建议直接用「美术资源」模板，写明用途、位置、尺寸、参考图。
