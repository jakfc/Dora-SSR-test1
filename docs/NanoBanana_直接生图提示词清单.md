# 《永昌堡：铁血筑城》Nano Banana 直接生图提示词清单

> **使用说明**：
> 1. 本清单每一条都是**完整、独立、可直接复制粘贴**给 Nano Banana（Gemini 网页版 / Google AI Studio / `generate_image`）的最终提示词，已内置**风格圣经、1.3 统一色板、正侧视防偏转约束（避免生成 3/4 视角）、纯白底无阴影约束（方便一键抠图）**。
> 2. **出图建议**：先出每个角色/建筑的**基础标准图（第 1 步）**；出动画帧或变体（行走、攻击、受损、关门）时，**在同一个对话里把标准图作为参考图上传**，再用下文提供的【连帧/变体追问模板】生成，可保持 100% 角色与画风一致性。
> 3. **画布比例**：已按目标尺寸标注推荐比例（如 `2:3`、`1:1`、`16:9`），出图后放到项目目录，配合 `tools/` 脚本即可自动抠白底 + 底部中心对齐 + 缩放到代码尺寸。

---

## 一、A 组：角色与单位（128×192，BOSS 192×256）

### A01 王叔杲（主角 · 筑堡总指挥）
- **画布比例**：`2:3`（目标尺寸 128×192，已生成参考图：`player_idle_01.png`）
- **标准立绘提示词（Idle）**：
```text
A 2D side-scrolling game character sprite of a dignified Ming dynasty Chinese gentleman-commander in his 40s, neat trimmed beard and resolute expression. Wearing a black wusha winged official hat, a finely detailed dark ink-blue lamellar armor overcoat with dark red trim over an ochre-brown (#D97706) long robe, a pale-gold (#FEFCBF) waist sash, dark cloth boots, and a long Chinese sword in a scabbard at his waist. Strict 90-degree pure orthographic side-profile view facing right (NOT 3/4 view), full body standing in a neutral idle pose, centered and bottom-aligned. Hand-painted flat semi-shaded Chinese guofeng 2D game art style, clean crisp 1.5px dark charcoal outline (#1A202C), maximum 3 flat shading tones per surface, warm earthy palette, consistent light from upper-left, no glossy anime highlights, no 3D render, no oil brushstrokes, no drop shadow, no ground shadow, no text, no scenery. Isolated on a completely uniform pure solid white background.
```

---

### A02 闲置族丁（IDLE）
- **画布比例**：`2:3`（目标尺寸 128×192）
- **标准立绘提示词**：
```text
A 2D side-scrolling game character sprite of a Ming dynasty Chinese coastal villager, sturdy build, wearing a simple short hemp tunic in muted gray-brown, rolled trousers, cloth shoes, empty hands, and a light gray-blue (#CBD5E0) cloth headband and waist tie. Strict 90-degree pure orthographic side-profile view facing right (NOT 3/4 view), full body standing in a neutral idle pose, centered and bottom-aligned. Hand-painted flat semi-shaded Chinese guofeng 2D game art style, clean crisp 1.5px dark charcoal outline (#1A202C), maximum 3 flat shading tones per surface, warm earth palette, consistent light from upper-left, no glossy highlights, no 3D render, no drop shadow, no ground shadow, no text, no scenery. Isolated on a completely uniform pure solid white background.
```

---

### A03 水田农夫（FARMER）
- **画布比例**：`2:3`（目标尺寸 128×192）
- **标准立绘提示词**：
```text
A 2D side-scrolling game character sprite of a Ming dynasty Chinese peasant farmer, sturdy village build, wearing a bamboo straw conical hat (douli), rolled-up short hemp tunic sleeves, carrying a traditional wooden-handled iron hoe resting on his shoulder, with a grass-green (#48BB78) cloth waist band. Strict 90-degree pure orthographic side-profile view facing right (NOT 3/4 view), full body standing in a neutral idle pose, centered and bottom-aligned. Hand-painted flat semi-shaded Chinese guofeng 2D game art style, clean crisp 1.5px dark charcoal outline (#1A202C), maximum 3 flat shading tones per surface, warm earth palette, consistent light from upper-left, no glossy highlights, no 3D render, no drop shadow, no ground shadow, no text, no scenery. Isolated on a completely uniform pure solid white background.
```

---

### A04 盐场灶户（SALT_WORKER）
- **画布比例**：`2:3`（目标尺寸 128×192）
- **标准立绘提示词**：
```text
A 2D side-scrolling game character sprite of a Ming dynasty Chinese coastal salt pan worker, sturdy build, wearing a short rough hemp tunic, coarse cloth apron, holding a wide wooden salt shovel in hand with a small wooden salt bucket at his feet, wearing a warm yellow (#ECC94B) headband and waist band. Strict 90-degree pure orthographic side-profile view facing right (NOT 3/4 view), full body standing in a neutral idle pose, centered and bottom-aligned. Hand-painted flat semi-shaded Chinese guofeng 2D game art style, clean crisp 1.5px dark charcoal outline (#1A202C), maximum 3 flat shading tones per surface, warm earth palette, consistent light from upper-left, no glossy highlights, no 3D render, no drop shadow, no ground shadow, no text, no scenery. Isolated on a completely uniform pure solid white background.
```

---

### A05 筑城工匠（BUILDER）
- **画布比例**：`2:3`（目标尺寸 128×192）
- **标准立绘提示词**：
```text
A 2D side-scrolling game character sprite of a Ming dynasty Chinese fortress stonemason and carpenter, sturdy build, wearing a short work tunic with an orange (#ED8936) waist sash and headband, a wooden mallet tucked into his belt and holding a wooden carpenter square ruler. Strict 90-degree pure orthographic side-profile view facing right (NOT 3/4 view), full body standing in a neutral idle pose, centered and bottom-aligned. Hand-painted flat semi-shaded Chinese guofeng 2D game art style, clean crisp 1.5px dark charcoal outline (#1A202C), maximum 3 flat shading tones per surface, warm earth palette, consistent light from upper-left, no glossy highlights, no 3D render, no drop shadow, no ground shadow, no text, no scenery. Isolated on a completely uniform pure solid white background.
```

---

### A06 永嘉场乡兵（MILITIA）
- **画布比例**：`2:3`（目标尺寸 128×192）
- **标准立绘提示词**：
```text
A 2D side-scrolling game character sprite of a Ming dynasty Chinese coastal militia soldier, determined expression, wearing cloth tunic under simple iron-and-leather lamellar chest armor (zhaojia), navy blue (#4299E1) headband and arm wraps, holding a long wooden-shafted Ming spear upright with a red tassel. Strict 90-degree pure orthographic side-profile view facing right (NOT 3/4 view), full body standing in a neutral ready pose, centered and bottom-aligned. Hand-painted flat semi-shaded Chinese guofeng 2D game art style, clean crisp 1.5px dark charcoal outline (#1A202C), maximum 3 flat shading tones per surface, warm earth palette, consistent light from upper-left, no glossy highlights, no 3D render, no drop shadow, no ground shadow, no text, no scenery. Isolated on a completely uniform pure solid white background.
```

---

### A07 王家拳武师（KUNG_FU）
- **画布比例**：`2:3`（目标尺寸 128×192）
- **标准立绘提示词**：
```text
A 2D side-scrolling game character sprite of a Ming dynasty Chinese martial artist, muscular athletic build, bare-chested or wearing a sleeveless open short martial tunic, crimson-red (#E53E3E) cloth wrist wraps and waist sash, standing in a low traditional southern Chinese kung fu fist stance. Strict 90-degree pure orthographic side-profile view facing right (NOT 3/4 view), full body centered and bottom-aligned. Hand-painted flat semi-shaded Chinese guofeng 2D game art style, clean crisp 1.5px dark charcoal outline (#1A202C), maximum 3 flat shading tones per surface, warm earth palette, consistent light from upper-left, no glossy highlights, no 3D render, no drop shadow, no ground shadow, no text, no scenery. Isolated on a completely uniform pure solid white background.
```

---

### A08 浪人斥候（SCOUT，敌方朝左）
- **画布比例**：`2:3`（目标尺寸 128×192）
- **标准立绘提示词**：
```text
A 2D side-scrolling game enemy sprite of a 16th-century Japanese wokou pirate scout, gaunt and furtive, wearing a tattered dark ragged cloak, bare feet, dull violet (#9F7AEA) cloth belt and ragged accents, holding a thin katana sword in one hand. Strict 90-degree pure orthographic side-profile view facing LEFT (NOT facing right, NOT 3/4 view), full body in a crouched stealthy ready pose, centered and bottom-aligned. Hand-painted flat semi-shaded Chinese guofeng 2D game art style, clean crisp 1.5px dark charcoal outline (#1A202C), maximum 3 flat shading tones per surface, dark muted earth palette, consistent light from upper-left, no glossy highlights, no 3D render, no drop shadow, no ground shadow, no text, no scenery. Isolated on a completely uniform pure solid white background.
```

---

### A09 倭刀精锐（SAMURAI，敌方朝左）
- **画布比例**：`2:3`（目标尺寸 128×192）
- **标准立绘提示词**：
```text
A 2D side-scrolling game enemy sprite of a 16th-century Japanese wokou elite samurai raider, wearing dark crimson (#C53030) laced do-maru lamellar armor, fierce iron demon mask (menpo), traditional straw sandals, wielding a long curved odachi katana with both hands. Strict 90-degree pure orthographic side-profile view facing LEFT (NOT facing right, NOT 3/4 view), full body in a menacing combat stance, centered and bottom-aligned. Hand-painted flat semi-shaded Chinese guofeng 2D game art style, clean crisp 1.5px dark charcoal outline (#1A202C), maximum 3 flat shading tones per surface, dark earth and crimson palette, consistent light from upper-left, no glossy highlights, no 3D render, no drop shadow, no ground shadow, no text, no scenery. Isolated on a completely uniform pure solid white background.
```

---

### A10 倭酋统领（BOSS，敌方朝左）
- **画布比例**：`3:4`（目标尺寸 192×256）
- **标准立绘提示词**：
```text
A 2D side-scrolling game boss sprite of a towering 16th-century Japanese wokou warlord commander, imposing heavy build, wearing ornate dark blood-red (#742A2A) samurai armor with a tattered jinbaori battle surcoat, horned kabuto helmet with fierce demon mask, dual katana swords drawn in both hands. Strict 90-degree pure orthographic side-profile view facing LEFT (NOT facing right, NOT 3/4 view), full body in a dominant battle stance, centered and bottom-aligned. Hand-painted flat semi-shaded Chinese guofeng 2D game art style, clean crisp 1.5px dark charcoal outline (#1A202C), maximum 3 flat shading tones per surface, dark earthy crimson palette, consistent light from upper-left, no glossy highlights, no 3D render, no drop shadow, no ground shadow, no text, no scenery. Isolated on a completely uniform pure solid white background.
```

---

### 【角色连帧追问模板】（上传上面生成的标准立绘作为参考图）
在同一个对话中附上标准立绘，直接发送以下对应动作指令：
- **行走序列（6 帧横向序列图）**：
```text
Using the exact same character design, proportions, colors, and flat guofeng 1.5px dark outline style from the reference image, generate a horizontal 6-frame sprite sheet of a side-view walk cycle facing the exact same direction. Keep head height and foot baseline completely consistent across all 6 frames, clean spacing, no text, pure solid white background, no drop shadow.
```
- **攻击/劳作序列（4~6 帧横向序列图）**：
```text
Using the exact same character design, proportions, colors, and flat guofeng 1.5px dark outline style from the reference image, generate a horizontal 5-frame sprite sheet of a side-view {action: e.g., swinging the hoe / thrusting the spear / throwing a powerful qilin punch / swinging the katana} animation facing the exact same direction. Keep foot baseline consistent, no text, pure solid white background, no drop shadow.
```
- **受击帧（1 帧）**：
```text
Using the exact same character from the reference image, redraw him in a single-frame hurt/knockback recoil pose facing the exact same direction, leaning slightly back, same flat guofeng style and 1.5px dark outline, pure solid white background, no drop shadow.
```

---

## 二、A11 & A12：掉落工具与拾荒物资（48×48）

> **建议**：这 7 个小物件可以用 `1:1` 单独生成，或者用下面这个 **网格打包提示词** 一次性出完再切分。

- **打包一次生成（推荐，省额度）`1:1`**：
```text
A clean 3x3 grid of 7 separate 2D Ming dynasty game prop icons on pure white background, flat semi-shaded Chinese guofeng style with crisp 1.5px dark outline (#1A202C), warm earth palette, upper-left lighting, no text, no drop shadow:
1. Wooden-handled iron farming hoe with green ribbon (#48BB78)
2. Wide wooden salt shovel with yellow ribbon (#ECC94B)
3. Carpenter wooden mallet with orange ribbon (#ED8936)
4. Long wooden spear with red tassel and blue ribbon (#4299E1)
5. Rolled ancient kung fu scroll tied with crimson red silk ribbon (#E53E3E)
6. Coarse burlap sack overflowing with white sea salt crystals (#E2E8F0)
7. Bundle of driftwood cedar logs tied with hemp rope (#9C6644).
```

---

## 三、B 组：建筑与地标（正侧视，底部中心对齐）

### B01 王氏宗祠（360×360，核心地标）
- **画布比例**：`1:1`（目标尺寸 360×360）
- **提示词**：
```text
A 2D side-view game building sprite of a Ming dynasty Jiangnan clan ancestral hall (Wang Ancestral Hall), featuring traditional stepped white-and-gray horsehead gable walls (matouqiang), dark gray tiled roof, crimson-red (#9B2C2C) wooden main gate with stone entrance steps, and carved stone plinths. Strict 90-degree orthographic front-side elevation with minimal 10% top roof depth, centered and bottom-aligned. Hand-painted flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), max 3 shading tones per surface, warm earth palette, upper-left lighting, NO text on plaque or banners, no trees, no ground shadow, no sky. Isolated on a pure solid white background.
```

### B02 堡内水田（440×88，可平铺）
- **画布比例**：`16:9` 或宽幅裁剪（目标尺寸 440×88）
- **提示词**：
```text
A 2D side-view seamlessly horizontally tileable Ming dynasty terraced rice paddy field strip, neat rows of vibrant green rice seedlings (#68A357) standing in shallow reflective water bordered by low rammed-earth bunds. Strict orthographic side view without perspective distortion. Flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), upper-left light, no text, no sky, pure solid white background.
```

### B03 永嘉场盐课司（340×260）
- **画布比例**：`4:3`（目标尺寸 340×260）
- **提示词**：
```text
A 2D side-view game building sprite of a Ming dynasty coastal salt administration office (Yanjiesi), featuring a modest wooden-and-brick official hall with ochre-yellow (#D6B36A) accents, an open timber drying shed beside it, and neat white sea-salt mounds in woven baskets. Strict orthographic side elevation, bottom-aligned. Flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), max 3 shading tones per surface, warm earth palette, upper-left lighting, NO text, no ground shadow, pure solid white background.
```

### B04 内城水门与作坊（260×380）
- **画布比例**：`2:3`（目标尺寸 260×380）
- **提示词**：
```text
A 2D side-view game building sprite of a Ming dynasty stone-masonry inner fortress water sluice gate (#5A6772) with a heavy iron portcullis grate, paired with an adjacent timber blacksmith and carpentry workshop shed. Strict orthographic side elevation, bottom-aligned. Flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), max 3 shading tones per surface, upper-left light, NO text, no ground shadow, pure solid white background.
```

### B05 主城墙·校场（360×300）
- **画布比例**：`4:3`（目标尺寸 360×300）
- **提示词**：
```text
A 2D side-view game structure sprite of a Ming dynasty coastal stone fortress wall section (#718096) built with large interlocked granite blocks, crenellated battlements on top, and a wooden military weapon rack at the base. Strict orthographic side elevation, bottom-aligned. Flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), max 3 shading tones per surface, upper-left light, NO text, no soldiers, no ground shadow, pure solid white background.
```

### B06 环海楼与东门瓮城（280×440，核心建筑）
- **画布比例**：`2:3`（目标尺寸 280×440）
- **提示词**：
```text
A 2D side-view game building sprite of a grand Ming dynasty coastal fortress eastern gatehouse (Huanhai Tower and Barbican), featuring a massive gray stone city wall (#4A5568, #718096) with an arched gateway and raised iron portcullis, topped by a two-tiered traditional timber watchtower with upturned dark-tiled eaves. Strict orthographic side elevation, bottom-aligned. Flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), max 3 shading tones per surface, warm earth and stone palette, upper-left light, NO text on plaques, no soldiers, no ground shadow, pure solid white background.
```

### B07 敌台箭楼（112×210）
- **画布比例**：`1:2` 或 `2:3`（目标尺寸 112×210）
- **提示词**：
```text
A 2D side-view game tower sprite of a Ming dynasty fortress archer watchtower, solid trapezoidal granite stone base supporting an elevated dark-wood (#8C6D46) turret with narrow arrow slits and a sloped tiled roof. Strict orthographic side elevation, bottom-aligned. Flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), max 3 shading tones per surface, upper-left light, NO text, no ground shadow, pure solid white background.
```

### B08 佛郎机炮台（112×210）
- **画布比例**：`1:2` 或 `2:3`（目标尺寸 112×210）
- **提示词**：
```text
A 2D side-view game tower sprite of a Ming dynasty stone artillery bastion (#4A5568), sturdy granite masonry base with stone parapets, mounting a historical Chinese-Portuguese bronze Folangji breech-loading cannon pointing to the right. Strict orthographic side elevation, bottom-aligned. Flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), max 3 shading tones per surface, upper-left light, NO text, no ground shadow, pure solid white background.
```

### B09 大罗山（远山，320×720）
- **画布比例**：`9:16`（目标尺寸 320×720）
- **提示词**：
```text
A 2D game background layer of distant southern Zhejiang coastal mountains (Daluo Mountain), painted in Chinese ink-wash silhouette style fading from muted slate blue-green (#2F4F4F, #2C3E50) at the peaks down to soft mist at the base. Flat guofeng game art style, minimal detail, no trees close-up, no text, isolated on pure solid white background.
```

### B10 & B11 城外盐田滩涂与东海倭船（1120×56 / 280×120）
- **B11 东海海岸与倭船（`16:9`）提示词**：
```text
A 2D side-view game landmark of a rough 16th-century wooden Japanese wokou pirate raiding boat beached on sandy coastal mudflats (#B79F78) with dark blue East China Sea waves (#1E4E79) lapping at the stern. Strict orthographic side view, flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), warm earth and muted sea palette, no text, pure solid white background.
```

### 【建筑受损/开关门追问模板】（上传上面对应的完好建筑图）
- **受损版**：
```text
Using the exact same building from the reference image, keep the exact silhouette and 2D flat guofeng style, but add battle damage: cracked masonry, chipped corners, splintered wood, and dark scorch marks from cannon fire and smoke. Pure solid white background, no text.
```
- **关门/关闸版（针对 B04 水门 / B06 东门瓮城）**：
```text
Using the exact same gatehouse from the reference image, redraw it with the heavy iron portcullis gate lowered and tightly sealed shut. Keep everything else identical, pure solid white background, no text.
```

---

## 四、C 组：投射物与特效

### C03 炮弹爆炸（6 帧，128×128）& C04 麒麟步斩击（6 帧，256×128）
- **C03 炮弹爆炸序列（`16:9` 横排 6 帧）**：
```text
A 6-frame horizontal sprite sheet of a 2D cartoon-guofeng gunpowder cannonball explosion animation, transitioning from bright orange (#F6AD55) and pale yellow flash to billowing dark ink-gray smoke clouds. Clean crisp dark outlines (#1A202C), flat cel-like shading, no realistic fire noise, no text, isolated on pure solid white background.
```
- **C04 麒麟步斩击/拳风（`16:9` 横排 4~6 帧）**：
```text
A 4-frame horizontal sprite sheet of a 2D Chinese martial arts horizontal crescent qi-wave slash effect facing right, glowing pale-gold (#FEFCBF) and warm amber (#D97706) energy arc with crisp stylized ink-brush edge lines. Flat guofeng VFX style, no text, isolated on pure solid white background.
```

---

## 五、D 组与 E 组：大场景背景与标题/结算插画（1280×720）

### E10 标题界面背景（1280×720，夜色肃穆永昌堡）
- **画布比例**：`16:9`
- **提示词**：
```text
A sweeping 2D side-view panoramic title screen illustration for a Ming dynasty 1558 coastal defense game: the grand granite walls and watchtowers of Yongchang Fortress silhouetted against a deep indigo night sky (#101829) with flickering warm orange watchtower torches (#F6AD55), distant misty Daluo Mountains (#2F4F4F) behind, and the dark East China Sea (#1E4E79) stretching to the right. Flat semi-shaded hand-painted Chinese guofeng style, solemn and resolute historical atmosphere, warm earth and ink-blue palette, no characters in foreground, NO text, no logos.
```

### E11 结束界面底图（胜利 / 失败两版，`16:9`）
- **胜利版**：
```text
A 2D side-view panoramic illustration of a Ming dynasty coastal stone fortress standing intact and triumphant under warm golden morning sunlight (#F6E05E, #4A6FA5) rising over the East China Sea, fluttering Ming defense banners on the battlements. Flat semi-shaded Chinese guofeng style, solemn and uplifting, NO text, no characters close-up.
```
- **失败版**：
```text
A 2D side-view panoramic illustration of a battered Ming dynasty coastal stone fortress with breached walls, broken wooden watchtowers, and smoldering dark ash and gray smoke rising into a gloomy dusk sky (#7A5C3E, #101829). Flat semi-shaded Chinese guofeng style, tragic and solemn atmosphere, NO text, no gore.
```

---

## 六、F 组：UI 图标打包生成（48×48，1:1 网格一次出完）

> **建议**：为了风格与线条粗细 100% 统一，用一次 `1:1` 生成 16 个核心图标的整齐网格图，再用脚本按网格切分即可！

- **16 枚核心图标网格提示词（`1:1`）**：
```text
A clean 4x4 grid of 16 distinct 2D Ming dynasty game UI icons evenly spaced on a pure solid white background, flat semi-shaded Chinese guofeng style, clean 1.5px dark charcoal outline (#1A202C), upper-left lighting, NO text, NO letters, NO numbers:
Row 1: Silver sycee ingot (#CBD5E0), Golden rice grain stalk (#ECC94B), Ming villager head silhouette, Red ancestral hall gatehouse (#9B2C2C).
Row 2: Fortress stone gate arch (#4A5568), Iron water sluice gate (#5A6772), Wooden arrow watchtower (#8C6D46), Bright sun over battlements (#F6AD55).
Row 3: Crescent moon (#FEFCBF), Green straw hat & hoe (#48BB78), Yellow salt shovel (#ECC94B), Orange carpenter mallet (#ED8936).
Row 4: Blue spear tip (#4299E1), Red wrapped martial fist (#E53E3E), Ming war drum & drumsticks (#C53030), Crossed katana warning icon (#C53030).
```
