# 《永昌堡：铁血筑城》游戏美术素材库与生成流水线说明

本文档记录根据 [美术素材清单与AI生成规范.md](file:///C:/Users/jakfc/AppData/Roaming/IppClub/DoraSSR/test/docs/美术素材清单与AI生成规范.md) 完成的美术素材生成与自动化处理管线。

---

## 1. 现已生成的素材总览

所有素材均已存放在 [assets/](file:///C:/Users/jakfc/AppData/Roaming/IppClub/DoraSSR/test/assets) 目录中，符合 1.3 统一色板、1.5 军规及 32 位透明 PNG 规范：

### 1.1 角色与单位 (`assets/sprites/`)
- **主角 王叔杲**:
  - [player_idle_01.png](file:///C:/Users/jakfc/AppData/Roaming/IppClub/DoraSSR/test/assets/sprites/player/player_idle_01.png) (128×192，AI 生成并经泛洪抠图 + 底部中心对齐 + 留安全边)
  - [player_idle_01@2x.png](file:///C:/Users/jakfc/AppData/Roaming/IppClub/DoraSSR/test/assets/sprites/player/player_idle_01@2x.png) (256×384 高清源文件)
- **六职业族丁** (`assets/sprites/villagers/`，128×192，正侧视向右):
  - `villager_idle_01.png` (闲置，识别色 `#CBD5E0`)
  - `villager_farmer_01.png` (水田农夫，斗笠 + 锄头，识别色 `#48BB78`)
  - `villager_salt_worker_01.png` (盐场灶户，围裙 + 盐铲，识别色 `#ECC94B`)
  - `villager_builder_01.png` (筑城工匠，木锤，识别色 `#ED8936`)
  - `villager_militia_01.png` (永嘉场乡兵，罩甲 + 长枪，识别色 `#4299E1`)
  - `villager_kung_fu_01.png` (王家拳武师，红绸束腕 + 拳架，识别色 `#E53E3E`)
- **敌方倭寇** (`assets/sprites/enemies/`，正侧视朝左):
  - `enemy_scout_01.png` (浪人斥候，128×192，紫饰 `#9F7AEA` + 细太刀)
  - `enemy_samurai_01.png` (倭刀精锐，128×192，胴丸 + 鬼面，识别色 `#C53030`)
  - `enemy_boss_01.png` (倭酋统领，192×256，双刀 + 阵羽织，识别色 `#742A2A`)
- **掉落道具与物资** (`assets/sprites/tools/`，48×48):
  - `tool_hoe.png` (锄头)
  - `tool_shovel.png` (盐铲)
  - `tool_hammer.png` (木锤)
  - `tool_spear.png` (长枪)
  - `tool_manual.png` (红绸拳谱)
  - `salvage_salt_bag.png` (盐包)
  - `salvage_driftwood.png` (漂流木料)
- **投射物与特效** (`assets/sprites/props/`):
  - `proj_arrow.png` (箭矢，32×16)
  - `proj_cannonball.png` (炮弹，24×24)
  - `fx_shockwave.png` (震击波，224×64)
  - `fx_halo_loyalty.png` (忠义光环，512×512)
  - `fx_torch_glow.png` (火把光晕，128×128)

### 1.2 建筑与地标 (`assets/buildings/`)
- `b01_shrine.png` (王氏宗祠，360×360)
- `b02_paddy.png` (堡内水田，440×88)
- `b04_inner_water_gate.png` (内城水门与作坊，260×380)
- `b06_east_gate_barbican.png` (环海楼与东门瓮城，280×440)
- `b07_tower_arrow.png` (敌台箭楼，112×210)
- `b08_tower_cannon.png` (佛郎机炮台，112×210)

### 1.3 场景与背景 (`assets/bg/`)
- `d01_sky_day.png` (天空·白昼，1280×720，`#4A6FA5` 渐变)
- `d02_sky_dusk.png` (天空·黄昏，1280×720，`#7A5C3E` 过渡)
- `d03_sky_night.png` (天空·黑夜，1280×720，`#101829` 渐变星空)
- `d04_ground_fortress.png` (地面·堡内，640×160，夯土 + 石板无缝平铺)
- `d05_ground_beach.png` (地面·城外滩涂，640×160，泥滩芦苇)
- `d06_horizon_silhouette.png` (城墙远景地平线，1280×160，屋脊城垛剪影)
- `d07_night_mask.png` (夜色遮罩，1280×720，40% 透明度 `#0B1426`)

### 1.4 UI 素材与图标 (`assets/ui/`)
- `e01_top_bar.png` (顶栏底板，1280×64)
- `e02_bottom_bar.png` (底栏底板，1280×76)
- `e03_modal_dialog.png` (弹窗底板，700×380，带四角云纹金边)
- `e04_btn_normal/hover/pressed/disabled.png` (按钮四态，200×56)
- `e07_bar_health.png` (血条，64×16)
- `e08_bar_stamina.png` (耐久条，64×16)
- `e09_prompt_bubble.png` (交互提示气泡，96×96)
- `e12_cursor.png` (国风鼠标指针，32×32)
- **图标集 (48×48)** (`assets/ui/icons/`):
  - 白银、粮草、人口、宗祠、东门、水门、敌台、白天、黑夜
  - 6 大职业图标 (`icon_role_*`)
  - 4 大操作图标 (`icon_op_*`)

---

## 2. 自动化批处理与后续出图脚本

在 [tools/generate_all_assets.py](file:///C:/Users/jakfc/AppData/Roaming/IppClub/DoraSSR/test/tools/generate_all_assets.py) 提供了全套素材的自动绘制与尺寸适配逻辑。

若使用 Midjourney / Stable Diffusion / ComfyUI 出图后，可以使用以下自动化脚本进行一键透明抠图并归位：

```python
# 示例：快速将外部生成的 JPG/PNG 处理为透明对齐的游戏素材
from PIL import Image
import numpy as np
from collections import deque

def auto_key_and_align(src_path, dst_path, target_size=(128, 192), padding_bottom=8):
    # 边缘泛洪白底剔除 + 底部中心对齐 + 导出透明 PNG
    ...
```
