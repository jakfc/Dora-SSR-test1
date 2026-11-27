import { Color, DrawNode, KeyName, Keyboard, Label, Node, Size, Sprite, Vec2 } from 'Dora';
import { SceneManager } from 'src/scenes/SceneManager';
import { EnemyType, GameConfig, LandmarkId, ProjectKind, VillagerRole } from 'src/config/GameConfig';
import { Screen } from 'src/config/Screen';
import { artAt, artCover, artCoverSize, artInto, artReady, artStretch } from 'src/config/Assets';
import { GameState, BuildProject } from 'src/config/GameState';
import { DefenseTower } from 'src/entities/DefenseTower';
import { Enemy } from 'src/entities/Enemy';
import { Player } from 'src/entities/Player';
import { ToolDrop, Villager } from 'src/entities/Villager';
import { HudLayer } from 'src/ui/HudLayer';
import { animateMoveY, playFx, pulseNode, tickFx } from 'src/ui/Fx';
import { soundBgm, soundSfx } from 'src/audio/Sound';

interface ScavengeDrop {
	x: number;
	kind: 'SALT' | 'WOOD';
	collected: boolean;
	node: Node.Type;
}

interface PendingSpawn {
	enemyType: EnemyType;
	triggerTime: number;
	side: 'W' | 'E';
}

/** 工地可视化：进度条 + 抡锤动画 */
interface ProjectView {
	p: BuildProject;
	node: Node.Type;
	bar: DrawNode.Type;
	label: Label.Type;
	hammer: Sprite.Type | undefined;
}

interface FloatingText {
	label: Label.Type;
	timer: number;
}

/** 工具掉落物对应的美术 id（缺素材时回退到方块） */
const TOOL_ART: Partial<Record<VillagerRole, string>> = {
	FARMER: 'tool_hoe',
	SALT_WORKER: 'tool_shovel',
	BUILDER: 'tool_hammer',
	MILITIA: 'tool_spear',
	KUNG_FU: 'tool_manual',
};

/** 场上还活着的倭寇大将（给 HUD 显示血条用）。 */
const findBoss = (list: Enemy[]): Enemy | undefined => {
	for (const e of list) {
		if (!e.dead && e.type === 'BOSS') return e;
	}
	return undefined;
};

function drawRect(
	draw: DrawNode.Type,
	x: number,
	y: number,
	w: number,
	h: number,
	fillColor: number,
	borderColor?: number
): void {
	const verts = [Vec2(x, y), Vec2(x + w, y), Vec2(x + w, y + h), Vec2(x, y + h)];
	if (borderColor !== undefined) {
		draw.drawPolygon(verts, Color(fillColor), 1.5, Color(borderColor));
	} else {
		draw.drawPolygon(verts, Color(fillColor));
	}
}

/**
 * 核心横版战场场景
 */
export function GameScene(): Node.Type {
	const scene = Node();
	const gs = GameState.instance;

	// 1. 天空背景层（随昼夜变化）
	const skyDraw = DrawNode();
	scene.addChild(skyDraw);

	// 天空贴图：白天 / 黄昏 / 夜晚三张，按状态切换（缺素材时退回纯色天空）
	// 用 artCover 等比铺满：窗口宽高比与素材不一致时只裁边不拉伸，镜头拉近后云山不被压扁
	const skyArts: Array<{ id: string; sprite: Sprite.Type | undefined }> = [
		{ id: 'sky_day', sprite: artCover('sky_day', Screen.width, Screen.height) },
		{ id: 'sky_dusk', sprite: artCover('sky_dusk', Screen.width, Screen.height) },
		{ id: 'sky_night', sprite: artCover('sky_night', Screen.width, Screen.height) },
	];
	for (const item of skyArts) {
		if (item.sprite === undefined) continue;
		item.sprite.visible = false;
		scene.addChild(item.sprite);
	}

	// 2. 三层视差容器：远景 / 中景 / 主战场
	const farLayer = Node();
	const midLayer = Node();
	const worldLayer = Node();
	scene.addChild(farLayer);
	scene.addChild(midLayer);
	scene.addChild(worldLayer);

	// 战争迷雾（建在 worldLayer 内部、地标之后、角色之前：雾盖地不盖人）
	// 详见下方「战争迷雾」段：只有主角王叔杲能探路，族丁在雾里依然可见。

	// 新地图分区（一切布局都从配置推导，改坐标只需改 GameConfig）
	const LM = GameConfig.MAP_LANDMARKS;
	const westSeaEnd = LM.WEST_COAST.x; // 西岸：以西是海
	const eastSeaStart = LM.EAST_COAST.x; // 东岸：以东是海
	const cityMinX = LM.INNER_GATE.x + 60; // 堡内石板路（西起）
	const cityMaxX = LM.EAST_GATE.x - 60; // 堡内石板路（东止）

	// 远景：海天一线（西面的大罗山已撤，改为开阔海面与东西两头的倭船帆影）
	const farDraw = DrawNode();
	drawRect(farDraw, 0, GameConfig.GROUND_Y, GameConfig.MAP_WIDTH, 120, 0x332d3748);
	for (const jx of [430, 1060, 6800, 7280]) {
		farDraw.drawPolygon(
			[
				Vec2(jx - 26, GameConfig.GROUND_Y + 150),
				Vec2(jx + 26, GameConfig.GROUND_Y + 150),
				Vec2(jx + 14, GameConfig.GROUND_Y + 176),
				Vec2(jx - 14, GameConfig.GROUND_Y + 176),
			],
			Color(0x992c3e50)
		);
		farDraw.drawPolygon(
			[
				Vec2(jx, GameConfig.GROUND_Y + 150),
				Vec2(jx, GameConfig.GROUND_Y + 212),
				Vec2(jx + 22, GameConfig.GROUND_Y + 150),
			],
			Color(0x992c3e50)
		);
	}
	farLayer.addChild(farDraw);

	// 远景剪影贴图：横向平铺盖满整张大地图，隔块镜像以缓解重复感
	if (artAt(farLayer, 'horizon', 0, GameConfig.GROUND_Y) !== undefined) {
		farDraw.clear();
		for (let i = 1; i * 1280 < GameConfig.MAP_WIDTH + 1280; i++) {
			const flip = i % 2 === 1;
			const tile = artAt(farLayer, 'horizon', i * 1280 + (flip ? 1280 : 0), GameConfig.GROUND_Y);
			if (tile !== undefined && flip) tile.scaleX = -1;
		}
	}

	// 中景：堡内河浃、屋舍远影
	const midDraw = DrawNode();
	for (let x = cityMinX; x < cityMaxX; x += 240) {
		drawRect(midDraw, x, GameConfig.GROUND_Y, 110, 75, 0x883b4a59);
		drawRect(midDraw, x - 8, GameConfig.GROUND_Y + 75, 126, 22, 0x882d3748);
	}
	midLayer.addChild(midDraw);

	// 中景贴图：堡内村舍屋影，横向平铺盖住程序化色块
	if (artAt(midLayer, 'mid_houses', 0, GameConfig.GROUND_Y) !== undefined) {
		for (let i = 1; i * 1280 < GameConfig.MAP_WIDTH; i++) {
			artAt(midLayer, 'mid_houses', i * 1280, GameConfig.GROUND_Y);
		}
		midDraw.clear();
	}

	// 主战场地面与地标建筑
	// 地平线以上是陆地（人站的地方）；地平线以下先露一小条地面断面（岸），
	// 再往下整片是前景水面，水里映着上面的城。
	// 【修】水面以前是从地平线往上画的 —— 等于把一层深蓝涂在天空和城区背后
	// （所以看起来“建筑背后一片纯深蓝”），而且倒影只能挂在泥土层上。
	// 现在水面线压到地平线以下，水与倒影都在下方，地面断面只剩一条薄岸。
	const SHORE_H = GameConfig.WATER.SHORE_BAND; // 地面断面高度（走人的那条地）
	const WATER_TOP = GameConfig.GROUND_Y; // 地平线（人物落脚线）
	const WATER_LINE = WATER_TOP - SHORE_H; // 前景水面上沿：倒影从这里往下翻
	const WATER_BOTTOM = -240; // 水一直画到屏幕外，滚动时不留缝
	const WATER_H = WATER_LINE - WATER_BOTTOM;
	const WATER_SPAN = WATER_LINE - Math.max(0, WATER_BOTTOM); // 屏幕里看得见的那一段
	const SHORE_Y = WATER_LINE;
	const groundDraw = DrawNode();
	// 地面断面：贴着地平线的一大条，下面会被水面盖掉，所以要用实色打底，
	// 否则贴图接缝处会直接露出空底（就是那个“地底白洞”）。
	drawRect(groundDraw, 0, SHORE_Y, GameConfig.MAP_WIDTH, SHORE_H, 0xff3b3026);
	// 两头入海、中间堡城：西岸以西是海，西岸~内城水门是滩涂，
	// 内城水门~东门之间是堡内石板路，东门~东岸又是滩涂，东岸以东复为海。
	drawRect(groundDraw, 0, SHORE_Y, westSeaEnd, SHORE_H, 0xff1e4e79);
	drawRect(groundDraw, eastSeaStart, SHORE_Y, GameConfig.MAP_WIDTH - eastSeaStart, SHORE_H, 0xff1e4e79);
	drawRect(groundDraw, westSeaEnd, GameConfig.GROUND_Y - 14, cityMinX - westSeaEnd, 14, 0xffb79f78);
	drawRect(groundDraw, cityMaxX, GameConfig.GROUND_Y - 14, eastSeaStart - cityMaxX, 14, 0xffb79f78);
	drawRect(groundDraw, cityMinX, GameConfig.GROUND_Y - 14, cityMaxX - cityMinX, 14, 0xff718096);
	worldLayer.addChild(groundDraw);

	// 地面 / 滩涂贴图：横向平铺（有素材时盖住程序化地面）
	// 同一张 640 宽的图铺满 7600 像素的地图，一眼就能看出「一格一格」。
	// 主角脚下标记环（放在村民之后，不会被别人遮住）
	const playerMarkDraw = DrawNode();
	worldLayer.addChild(playerMarkDraw);

	// 三招打散重复感：① 有变体图就轮换；② 隔块水平镜像；③ 每块 ±2 像素微抖。
	// 最后再撒一层地物碎屑（石块/草簇/贝壳），把等距的节拍彻底打乱。
	const groundArtNode = Node();
	worldLayer.addChild(groundArtNode);
	const GROUND_TILE = 640;
	const GROUND_TILE_ART_H = 160; // 地面贴图原生高度；底部那一截会被水面盖掉
	// 固定种子伪随机：同一局每次重绘结果一致（不会闪），但相邻两块取法不同
	const groundRand = (n: number): number => {
		const v = Math.sin(n * 127.1 + 311.7) * 43758.5453;
		return v - Math.floor(v);
	};
	if (artReady('ground_beach')) {
		let tileIndex = 0;
		// 一整条从头铺到尾，按「块中心」落在哪个区选滩涂/堡内石板。
		// 之前分三段各铺一次，段尾总会多出半块压到下一段上，接缝处就是一道垂直断层。
		for (let x = 0; x < GameConfig.MAP_WIDTH; x += GROUND_TILE) {
			const mid = x + GROUND_TILE / 2;
			const inCity = mid >= cityMinX && mid <= cityMaxX;
			const want = inCity ? 'ground_city' : 'ground_beach';
			const variants = inCity ? ['ground_city_b'] : ['ground_beach_b', 'ground_beach_c'];
			const pick = variants[Math.floor(groundRand(tileIndex * 3.7) * variants.length)];
			const id =
				pick !== undefined && artReady(pick) ? pick : artReady(want) ? want : 'ground_beach';
			// 一块正好占满 [x, x+640]：不加 y 抖动、也不做镜像翻转。
			// 镜像那套（scaleX=-1 再把 x 挪一格）在左下角锚点下会把图案甩到隔壁格，
			// 结果就是「原格空成白洞 + 隔壁双叠两张」。重复感交给变体图和碎屑层。
			artAt(groundArtNode, id, x, GameConfig.GROUND_Y - GROUND_TILE_ART_H);
			tileIndex++;
		}
		groundDraw.clear();
		// 两头海面重新盖回（铺贴图时不能让滩涂越界到海里）
		const seaDraw = DrawNode();
		drawRect(seaDraw, 0, SHORE_Y, westSeaEnd, SHORE_H, 0xff1e4e79);
		drawRect(seaDraw, eastSeaStart, SHORE_Y, GameConfig.MAP_WIDTH - eastSeaStart, SHORE_H, 0xff1e4e79);
		worldLayer.addChild(seaDraw);

		// 地物碎屑层：按种子撒在滩涂与堡内地面上，压掉贴图的等距节拍
		// 每件碎屑是一张独立小图（石块 / 草簇 / 贝壳 / 木屑），随机挑、随机缩放与透明度。
		const decalIds = [
			'ground_decal_01',
			'ground_decal_02',
			'ground_decal_03',
			'ground_decal_04',
			'ground_decal_05',
			'ground_decal_06',
		].filter((id) => artReady(id));
		if (decalIds.length > 0) {
			const decalNode = Node();
			worldLayer.addChild(decalNode);
			for (let i = 0; i < Math.floor(GameConfig.MAP_WIDTH / 110); i++) {
				const dx = 40 + groundRand(i * 1.7) * (GameConfig.MAP_WIDTH - 80);
				if (dx < westSeaEnd || dx > eastSeaStart) continue;
				// 只贴在地平线附近，别飘到天上去
				// 只贴在地平线往上这一小片岸带上（再往下就是水面了）
				const dy = GameConfig.GROUND_Y - 3 - groundRand(i * 2.9) * 18;
				const pick = decalIds[Math.floor(groundRand(i * 3.3) * decalIds.length)];
				const node = pick !== undefined ? artAt(decalNode, pick, dx, dy) : undefined;
				if (node === undefined) continue;
				// 每处随机镜像 + 随机缩放 + 随机透明度，看上去就不是同一张图
				const flip = groundRand(i * 4.1) < 0.5 ? -1 : 1;
				node.scaleX = flip * (0.7 + groundRand(i * 6.7) * 0.7);
				node.opacity = 0.45 + groundRand(i * 8.3) * 0.55;
			}
		}
	}

	// ---- 城前水面：地平线以下全是水，水里映着上面的城 ----
	// 只画可视区域那一段（横跨整张地图的渐变会很浪费）
	const waterDraw = DrawNode();
	worldLayer.addChild(waterDraw);
	const rippleDraw = DrawNode();
	worldLayer.addChild(rippleDraw);
	// 碎光层：水面零零星星的反光，一闪一闪
	const glintDraw = DrawNode();
	worldLayer.addChild(glintDraw);
	// 所有倒影挂点：每帧轻微摆一下 scaleX，水面才有「晃」的感觉
	const mirrorNodes: Node.Type[] = [];
	let waterClock = 0;

	/** 水位渐变：贴地平线处亮（远水反天光），越靠画面底部越深 */
	const paintWater = (left: number, width: number) => {
		waterDraw.clear();
		const deep = GameConfig.WATER.COLOR_DEEP;
		const top = GameConfig.WATER.COLOR_TOP;
		const steps = 12;
		for (let i = 0; i < steps; i++) {
			// 贴水面处取 top（远水反天光），越靠画面底部越深
			const t = i / (steps - 1);
			// 水在慢慢起伏：整片水色随时间和深度轻微呼吸，不是一张死渐变
			const swell = 1 + Math.sin(waterClock * 0.9 - t * 3.4) * GameConfig.WATER.SWELL;
			const r = Math.round((((top >>> 16) & 0xff) * (1 - t) + ((deep >>> 16) & 0xff) * t) * swell);
			const g = Math.round((((top >>> 8) & 0xff) * (1 - t) + ((deep >>> 8) & 0xff) * t) * swell);
			const b = Math.round(((top & 0xff) * (1 - t) + (deep & 0xff) * t) * swell);
			const col =
				0xff000000 |
				(Math.min(255, r) << 16) |
				(Math.min(255, g) << 8) |
				Math.min(255, b);
			const hStep = WATER_H / steps + 1;
			// 从水面线往下铺：i=0 贴水面（最亮），越往下越深
			drawRect(waterDraw, left, WATER_LINE - (WATER_H * (i + 1)) / steps, width, hStep, col);
		}
	};

	/** 波纹：几道横贯水面的亮线，跟着镜头只画可视区，缓慢漂移 */
	const tickWater = (dt: number) => {
		waterClock += dt;
		const left = cameraX - Screen.width / 2 - 60;
		const width = Screen.width + 120;
		paintWater(left, width);
		rippleDraw.clear();
		const n = GameConfig.WATER.RIPPLE_COUNT;
		for (let i = 0; i < n; i++) {
			const seed = groundRand(i * 3.3 + 1.1);
			const y = WATER_LINE - 5 - seed * (WATER_SPAN - 14);
			const len = width * (0.14 + groundRand(i * 7.7) * 0.42);
			const speed = 5 + groundRand(i * 2.1) * 8;
			const drift = ((waterClock * speed + seed * 1000) % (width + 320)) - 160;
			const alpha = 0x28 + Math.floor(groundRand(i * 5.5) * 0x34);
			drawRect(rippleDraw, left + drift, y, len, 2, (alpha << 24) | 0xdfefff);
			// 每道波纹底下再压一条更暗的，看着像水面的褶皱
			drawRect(rippleDraw, left + drift + 6, y + 2, len * 0.7, 1, ((alpha >>> 1) << 24) | 0x9fc0e8);
		}
		// 水岸亮边：贴着地平线的一条浅水反光，随水波轻微呼吸
		const shoreA = 0x30 + Math.floor((Math.sin(waterClock * 1.2) * 0.5 + 0.5) * 0x26);
		drawRect(rippleDraw, left, WATER_LINE - 2, width, 2, (shoreA << 24) | 0xffffff);
		drawRect(rippleDraw, left, WATER_LINE - 4, width, 1, (Math.floor(shoreA * 0.6) << 24) | 0xcfe8ff);
		// 碎光：位置/周期各不相同，淡入淡出地闪
		glintDraw.clear();
		const gn = GameConfig.WATER.GLINT_COUNT;
		for (let i = 0; i < gn; i++) {
			const ph = groundRand(i * 13.7);
			const cycle = 1.6 + ph * 2.8;
			const t = ((waterClock / cycle + ph) % 1 + 1) % 1;
			if (t > 0.36) continue; // 只在一小段周期里亮，才有「闪」的感觉
			const fade = Math.sin((t / 0.36) * Math.PI);
			const gx =
				left + 40 + groundRand(i * 2.3) * (width - 80) + Math.sin(waterClock * 0.6 + i) * 9;
			const gy = WATER_LINE - 8 - groundRand(i * 4.9) * (WATER_SPAN - 18);
			const gw = 4 + Math.floor(groundRand(i * 6.1) * 9);
			const ga = Math.floor(0x30 + fade * 0x82);
			drawRect(glintDraw, gx, gy, gw, 3, (ga << 24) | 0xf2f8ff);
		}
		// 倒影微摆：每个倒影左右各晃一点，看着就像水里在动
		for (let i = 0; i < mirrorNodes.length; i++) {
			const m = mirrorNodes[i];
			if (m === undefined) continue;
			m.scaleX = 1 + Math.sin(waterClock * 0.7 + i * 1.7) * 0.03;
		}
	};

	/**
	 * 倒影挂点：挂在源挂点底下，绕水面线上下翻一格。
	 * 因为是子节点，源挂点一动倒影自动跟着跑，不需要每帧同步坐标。
	 */
	const reflectOf = (parent: Node.Type): Node.Type => {
		const found = parent.getChildByTag('refl');
		if (found !== undefined) return found;
		const n = Node();
		n.tag = 'refl';
		mirrorNodes.push(n);
		// 源挂点原点在地平线上，水面线在地平线以下一格岸带：
		// 倒影从水面线往下翻，不会叠到上面那条地面断面上。
		n.y = -SHORE_H;
		n.scaleY = -GameConfig.WATER.REFLECT_SQUASH;
		n.opacity = GameConfig.WATER.REFLECT_OPACITY;
		parent.addChild(n);
		return n;
	};

	// 绘制静态地标（宗祠、水田、盐课司、主城墙、东西滩头）
	// 每级一块模型：升级后换的是「另一座楼」，不是同一个方块改数字。
	const landmarkDraw = DrawNode();
	worldLayer.addChild(landmarkDraw);
	const landmarkIds = Object.keys(GameConfig.MAP_LANDMARKS) as LandmarkId[];

	/** 地标 → 当前等级/状态对应的模型 id */
	const landmarkArtId = (id: LandmarkId): string => {
		if (id === 'ANCESTRAL_HALL') {
			const lv = gs.ancestralHallLevel;
			return lv <= 1 ? 'lm_ANCESTRAL_HALL' : `lm_ANCESTRAL_HALL_lv${lv}`;
		}
		if (id === 'INNER_GATE') {
			if (gs.innerGateHp <= 0) return 'lm_INNER_GATE_broken';
			const lv = gs.innerGateLevel;
			return lv <= 1 ? 'lm_INNER_GATE' : `lm_INNER_GATE_lv${lv}`;
		}
		if (id === 'EAST_GATE') {
			if (gs.eastGateHp <= 0) return 'lm_EAST_GATE_broken';
			if (gs.eastGateOpen) return 'lm_EAST_GATE_open';
			const lv = gs.eastGateLevel;
			return lv <= 1 ? 'lm_EAST_GATE' : `lm_EAST_GATE_lv${lv}`;
		}
		if (id === 'WEST_PIER' || id === 'EAST_PIER') {
			const side = id === 'WEST_PIER' ? 'W' : 'E';
			if (!gs.pierAlive(side)) return `lm_pier_${side}_broken`;
			// 打到一半就换半毁素材，不用等它整座断掉
			const hp = gs.pierHpOf(side);
			if (hp * 2 <= gs.pierMaxHp) return `lm_pier_${side}_damaged`;
			return `lm_pier_${side}`;
		}
		if (id === 'WEST_COAST' || id === 'EAST_COAST') return 'lm_coast';
		const lmCfg = GameConfig.MAP_LANDMARKS[id];
		if (lmCfg.reclaimable === 'PADDY') return `lm_paddy_lv${gs.landLevelOf(id)}`;
		if (lmCfg.reclaimable === 'SALT') return `lm_saltflat_lv${gs.landLevelOf(id)}`;
		return `lm_${id}`;
	};

	const landmarkArtNodes: Partial<Record<LandmarkId, Node.Type>> = {};
	const landmarkArtRow: LandmarkId[] = [];
	for (const id of landmarkIds) {
		const lm = GameConfig.MAP_LANDMARKS[id];
		// 东门 / 内城水门 / 宗祠另用动态挂点（换门、换顶、破损态）
		if (id !== 'EAST_GATE' && id !== 'INNER_GATE' && id !== 'ANCESTRAL_HALL') {
			const holder = Node();
			holder.x = lm.x;
			holder.y = GameConfig.GROUND_Y;
			worldLayer.addChild(holder);
			landmarkArtNodes[id] = holder;
			landmarkArtRow.push(id);
		}
		const lbl = Label('sarasa-mono-sc-regular', 15) as Label.Type;
		lbl.text = `${lm.name}\n(${lm.subtitle})`;
		lbl.x = lm.x;
		lbl.y = GameConfig.GROUND_Y + lm.height + 26;
		lbl.color = Color(0xfffefcbf);
		worldLayer.addChild(lbl);
	}

	/** 按当前等级/状态重刷静态地标模型（缺图时回退色块） */
	const refreshLandmarkArt = () => {
		landmarkDraw.clear();
		for (const id of landmarkArtRow) {
			const holder = landmarkArtNodes[id];
			if (holder === undefined) continue;
			const lm = GameConfig.MAP_LANDMARKS[id];
			if (artInto(holder, landmarkArtId(id), reflectOf(holder)) === undefined) {
				drawRect(
					landmarkDraw,
					lm.x - lm.width / 2,
					GameConfig.GROUND_Y,
					lm.width,
					lm.height,
					lm.color,
					0xff1a202c
				);
			}
		}
	};
	refreshLandmarkArt();

	// ---- 民居：人口之源（等级决定住得下多少人）----
	// 与地标同层，但必须在村民之前创建，否则屋子会盖在人头上。
	const houseDraw = DrawNode();
	worldLayer.addChild(houseDraw);
	const houseArtNodes: Node.Type[] = [];
	for (let i = 0; i < gs.houses.length; i++) {
		const n = Node();
		worldLayer.addChild(n);
		houseArtNodes.push(n);
	}

	/** 按等级重画民居；有美术就换贴图，缺美术时用色块（空地只画地基） */
	const houseLabels: Label.Type[] = [];
	const refreshHouses = () => {
		houseDraw.clear();
		for (let i = 0; i < gs.houses.length; i++) {
			const h = gs.houses[i];
			const node = houseArtNodes[i];
			if (node === undefined) continue;
			node.x = h.x;
			node.y = GameConfig.GROUND_Y;
			const artId = h.level <= 0 ? 'lm_house_plot' : `lm_house_lv${h.level}`;
			if (artInto(node, artId, reflectOf(node)) !== undefined) continue; // 有贴图就不用画色块
			if (h.level <= 0) {
				// 空地：只画一圈地基，等玩家投银起造
				drawRect(houseDraw, h.x - 40, GameConfig.GROUND_Y - 3, 80, 6, 0xff3b4a59, 0xffe2e8f0);
				continue;
			}
			const w = 64 + h.level * 16;
			const hh = 42 + h.level * 12;
			const wall = 0xffcbd5e0;
			const roof = h.level >= 3 ? 0xff7b341e : (h.level >= 2 ? 0xff9c4221 : 0xff4a5568);
			drawRect(houseDraw, h.x - w / 2, GameConfig.GROUND_Y, w, hh, wall, 0xff2d3748);
			drawRect(houseDraw, h.x - w / 2 - 7, GameConfig.GROUND_Y + hh, w + 14, 13, roof, 0xff1a202c);
			drawRect(houseDraw, h.x - 10, GameConfig.GROUND_Y, 20, hh * 0.5, 0xff744210);
			// 房子升级时同步刷新挂牌
			const lbl = houseLabels[i];
			if (lbl !== undefined) {
				lbl.text =
					h.level <= 0
						? '民居遗址\n(投银起造)'
						: `民居 Lv.${h.level}\n(可住 ${
							h.level * GameConfig.HOUSE_CAPACITY_PER_LEVEL
						} 人)`;
			}
		}
	};
	for (let i = 0; i < gs.houses.length; i++) {
		const h = gs.houses[i];
		const lbl = Label('sarasa-mono-sc-regular', 13) as Label.Type;
		lbl.text =
			h.level <= 0
				? '民居遗址\n(投银起造)'
				: `民居 Lv.${h.level}\n(可住 ${
					h.level * GameConfig.HOUSE_CAPACITY_PER_LEVEL
				} 人)`;
		lbl.x = h.x;
		lbl.y = GameConfig.GROUND_Y + 100;
		lbl.color = Color(0xfffefcbf);
		worldLayer.addChild(lbl);
		houseLabels.push(lbl);
	}
	refreshHouses();

	// 动态城门绘制（东门与内城水门）
	const gatesDraw = DrawNode();
	worldLayer.addChild(gatesDraw);

	// 城门 / 宗祠贴图挂点（有素材时替代方块；同一挂点按状态切换 id，不会重复创建）
	const gateArtNode = Node(); // 东门门楼：只换等级 / 破损，形状不随开闭变
	const innerGateArtNode = Node(); // 内城水门：完好 / 破损
	const shrineArtNode = Node(); // 王氏宗祠：1 级 / 2 级
	// 东门闸门（单独一个节点）：只有它上下滑，门楼本体不动。
	// 原来整座门楼往上跳 90px + 换成 cropTop 的另一张图，所以看着很割裂。
	const portcullisNode = Node();
	const portcullisDraw = DrawNode();
	let gateLiftTarget = 0; // 0 = 落闸，1 = 提闸
	let gateLift = 0; // 当前插值位置
	let gateLiftPrev = 0;
	let portcullisDrawBuilt = false;

	/**
	 * 城门铁闸缓动：只有闸门杆件沿门洞上下滑，门楼本体一动不动。
	 * 位置用 smoothstep 插值（起落有重量感），落到底/提到顶各响一次尘烟。
	 */
	const tickGate = (rawDt: number) => {
		const dt = Math.min(rawDt, 0.05);
		const speed = 1.7; // 每秒推进的比例，约 0.6 秒走完全程
		const before = gateLift;
		if (gateLift < gateLiftTarget) gateLift = Math.min(gateLiftTarget, gateLift + speed * dt);
		else if (gateLift > gateLiftTarget) gateLift = Math.max(gateLiftTarget, gateLift - speed * dt);
		if (gateLift === before) return;
		const e = gateLift * gateLift * (3 - 2 * gateLift); // smoothstep
		const eastLm = GameConfig.MAP_LANDMARKS.EAST_GATE;
		portcullisNode.x = eastLm.x;
		portcullisNode.y = GameConfig.GROUND_Y + e * 74;
		// 闸门刚开始下沉时扬一层灰，落地那下更实
		if (gateLift === 0 && gateLiftPrev > 0) {
			playFx(worldLayer, 'fx_arrow_hit', eastLm.x, GameConfig.GROUND_Y + 10, 0.34, 0.6, 14);
		} else if (gateLift === 1 && gateLiftPrev < 1) {
			playFx(worldLayer, 'fx_arrow_hit', eastLm.x, GameConfig.GROUND_Y + 84, 0.26, 0.4, 12);
		}
		gateLiftPrev = gateLift;
	};
	worldLayer.addChild(innerGateArtNode);
	worldLayer.addChild(gateArtNode);
	worldLayer.addChild(portcullisNode);
	worldLayer.addChild(shrineArtNode);

	// 夜间火把光点
	const torchDraw = DrawNode();
	worldLayer.addChild(torchDraw);

	// 火把光晕贴图挂点
	const torchArtNode = Node();
	// 拆断的栈桥残片（浪里散落的断板）：单独一层，开夜/刷新时重画
	const pierDebrisNode = Node();
	worldLayer.addChild(pierDebrisNode);
	worldLayer.addChild(torchArtNode);

	// 点击地面移动交互层
	// 注意：Node 一旦设置了 size，子节点坐标就会以「size 盒子的左下角」为原点，
	// 而盒子左下角 = 节点位置 - size * anchor。默认 anchor 是 (0.5,0.5)，
	// 会把整层内容向左下平移半个 size，导致地面与地标全部移出画面。
	// 世界层的子节点本来就使用「世界坐标」，因此 anchor 必须为 (0,0)。
	worldLayer.anchor = Vec2(0, 0);
	worldLayer.size = Size(GameConfig.MAP_WIDTH, Screen.height);
	worldLayer.touchEnabled = true;

	// 实体容器
	const tools: ToolDrop[] = [];
	const scavenges: ScavengeDrop[] = [];
	const villagers: Villager[] = [];
	const enemies: Enemy[] = [];
	const towers: DefenseTower[] = [];
	const floatingTexts: FloatingText[] = [];
	let nextToolId = 1;

	// ---------- 战争迷雾 ----------
	// 层级：在地标之后、塔与人之前 —— 雾遮住未探明的地，但族丁不会被雾吞掉。
	// 只有主角王叔杲走过去才算「探明」（参考《王国：新大陆》：君主一人开路）。
	const fogLayer = Node();
	fogLayer.anchor = Vec2(0, 0);
	worldLayer.addChild(fogLayer);
	const fogDraw = DrawNode();
	fogLayer.addChild(fogDraw);
	const fogLabels: Record<string, Label.Type> = {};
	for (const z of GameConfig.FOG_ZONES) {
		const lbl = Label('sarasa-mono-sc-regular', 22) as Label.Type;
		lbl.text = `${z.name}\n未 探 明`;
		lbl.x = z.x + z.width / 2;
		lbl.y = GameConfig.GROUND_Y + 150;
		lbl.color = Color(0xff718096);
		fogLayer.addChild(lbl);
		fogLabels[z.id] = lbl;
	}
	const FOG_TOP = GameConfig.GROUND_Y + 420;
	const refreshFogVisuals = () => {
		fogDraw.clear();
		for (const z of GameConfig.FOG_ZONES) {
			const explored = gs.isExplored(z.id);
			const lbl = fogLabels[z.id];
			if (lbl !== undefined) lbl.visible = !explored;
			if (explored) continue;
			drawRect(fogDraw, z.x, 0, z.width, FOG_TOP, 0xdd0b1220);
		}
	};
	// 初始就点亮西滩到宗祠这一段：不然西边的敌台糊在雾里，开局就看不到自家防线
	for (const z of GameConfig.FOG_ZONES) {
		if (z.x <= GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x) gs.revealZone(z.id);
	}
	refreshFogVisuals();

	/** 主角行至未探明地界边线即揭开迷雾（其余族丁走进去不算，雾里也看得见他们） */
	const revealFogAround = (xs: number[]) => {
		let changed = false;
		const reach = GameConfig.FOG_REVEAL_RADIUS;
		for (const z of GameConfig.FOG_ZONES) {
			if (gs.isExplored(z.id)) continue;
			for (const x of xs) {
				if (x >= z.x - reach && x <= z.x + z.width + reach) {
					gs.revealZone(z.id);
					hud.showToast(`探明新地界：${z.name}`, 2.2);
					changed = true;
					break;
				}
			}
		}
		if (changed) refreshFogVisuals();
	};

	for (const ts of gs.towers) {
		const tower = new DefenseTower(ts);
		towers.push(tower);
		worldLayer.addChild(tower.node);
	}

	const player = new Player();
	worldLayer.addChild(player.node);

	worldLayer.onTapEnded((touch) => {
		// 屏蔽 HUD 顶栏 / 底部操作条上的点击（那两个条是 UI 单位，需换算成世界单位）
		const topGuard = Screen.uiToWorld(70);
		const bottomGuard = Screen.uiToWorld(80);
		if (touch.location.y >= bottomGuard && touch.location.y <= Screen.height - topGuard) {
			player.moveTargetX = Math.max(40, Math.min(GameConfig.MAP_WIDTH - 40, touch.location.x));
		}
	});

	// 夜间半透明遮罩（位于世界之上、HUD 之下）
	const nightMaskDraw = DrawNode();
	scene.addChild(nightMaskDraw);

	// 夜幕贴图（叠在世界之上、HUD 之下）
	const nightMaskArt = artStretch('night_mask', Screen.width, Screen.height);
	if (nightMaskArt !== undefined) {
		nightMaskArt.visible = false;
		scene.addChild(nightMaskArt);
	}

	// 初始 3 名闲置族丁
	const spawnVillager = (x: number, role: VillagerRole = 'IDLE') => {
		const v = new Villager(x, role);
		villagers.push(v);
		worldLayer.addChild(v.node);
		playFx(worldLayer, 'fx_recruit', x, GameConfig.GROUND_Y + 60, 0.5, 0.3, 16);
	};
	// 开局三名闲散族丁就在宗祠前（新地图的城心是宗祠@2620，不再从西海那头起步）
	spawnVillager(GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x - 120, 'IDLE');
	spawnVillager(GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x - 60, 'IDLE');
	spawnVillager(GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x - 20, 'IDLE');

	const addFloatingText = (text: string, x: number, y: number, color = 0xfff6e05e) => {
		const lbl = Label('sarasa-mono-sc-regular', 15) as Label.Type;
		lbl.text = text;
		lbl.x = x;
		lbl.y = y;
		lbl.color = Color(color);
		worldLayer.addChild(lbl);
		floatingTexts.push({ label: lbl, timer: 1.2 });
	};

	const spawnTool = (x: number, role: VillagerRole) => {
		const cfg = GameConfig.ROLES[role];
		const tNode = Node();
		tNode.x = x;
		tNode.y = GameConfig.GROUND_Y;

		const artId = TOOL_ART[role];
		if (artId === undefined || artAt(tNode, artId, 0, 0) === undefined) {
			const d = DrawNode();
			drawRect(d, -10, 4, 20, 18, cfg.color, 0xffffffff);
			tNode.addChild(d);
		}

		const l = Label('sarasa-mono-sc-regular', 12) as Label.Type;
		l.text = cfg.toolName;
		l.y = 32;
		l.color = Color(0xffffffff);
		tNode.addChild(l);

		worldLayer.addChild(tNode);
		tools.push({ id: nextToolId++, x, role, claimed: false, node: tNode });
		gs.toolsCrafted++;
		playFx(worldLayer, 'fx_recruit', x, GameConfig.GROUND_Y + 60, 0.45, 0.25, 14);
	};

	const spawnScavenge = (x: number, kind: 'SALT' | 'WOOD') => {
		const sNode = Node();
		sNode.x = x;
		sNode.y = GameConfig.GROUND_Y;

		const scavengeArtId = kind === 'SALT' ? 'salvage_salt_bag' : 'salvage_driftwood';
		if (artAt(sNode, scavengeArtId, 0, 0) === undefined) {
			const d = DrawNode();
			drawRect(d, -12, 2, 24, 20, kind === 'SALT' ? 0xffe2e8f0 : 0xff9c6644, 0xff1a202c);
			sNode.addChild(d);
		}

		const l = Label('sarasa-mono-sc-regular', 12) as Label.Type;
		l.text = kind === 'SALT' ? '无主盐包' : '漂流木料';
		l.y = 32;
		l.color = Color(0xfffefcbf);
		sNode.addChild(l);

		worldLayer.addChild(sNode);
		scavenges.push({ x, kind, collected: false, node: sNode });
	};

	const spawnDailyScavenges = () => {
		// 清理旧的未拾取物资
		for (const s of scavenges) {
			if (!s.collected) s.node.removeFromParent();
		}
		scavenges.length = 0;

		// 城外拾荒带拉长：从东门外的盐田滩涂一直铺到海岸
		const count = GameConfig.SCAVENGE_COUNT_PER_DAY;
		const spanMin = GameConfig.OUTER_ZONE_MIN_X + 150;
		const spanMax = GameConfig.OUTER_ZONE_MAX_X - 150;
		for (let i = 0; i < count; i++) {
			const base = spanMin + ((spanMax - spanMin) * i) / Math.max(1, count - 1);
			const x = base + ((gs.day * 29 + i * 41) % 60);
			spawnScavenge(x, i % 2 === 0 ? 'SALT' : 'WOOD');
		}
	};
	spawnDailyScavenges();

	let spawnQueue: PendingSpawn[] = [];
	let nightElapsed = 0;
	let foodConsumeTimer = 0;
	let waitingVictoryModal = false;
	// 黄昏未归警告：每昼夜只弹一次
	let curfewWarnedDay = 0;
	// 调试探针：默认关闭。开发时改成 true 可在引擎日志里看到每秒态势（PROBE ...）
	const DEBUG_PROBE = false;
	// 调试注入：默认关闭。打开后会塞满银粮、把两名负盐灶户丢到远滩涂，方便一次性观察夜猎
	const DEBUG_SEED = false;
	let probeTimer = 1.0;
	let probeSeeded = false;
	let cameraX = GameConfig.CAMERA_MIN_X;

	const refreshEnvironmentVisuals = () => {
		skyDraw.clear();
		nightMaskDraw.clear();
		torchDraw.clear();
		gatesDraw.clear();
		// 火把光晕用 artAt 直接创建，每次刷新前先清空，避免重复叠加
		torchArtNode.removeAllChildren();
		// 断桥残片同理：先清空再按「哪一侧断了」重画，保证拆完一直是断的样子
		pierDebrisNode.removeAllChildren();
		if (!gs.pierAlive('W')) paintPierWreck('W');
		if (!gs.pierAlive('E')) paintPierWreck('E');
		// 注意：城门 / 宗祠挂点用 artInto，靠节点 tag 判断是否已建过精灵，
		// 这里千万不能 removeAllChildren，否则 tag 还在、精灵没了，城门会凭空消失。

		// 天空色调（铺满整个可视区域）
		const isDusk = gs.phase === 'DAY' && gs.dayTimer <= GameConfig.DUSK_WARNING_TIME;
		const skyColor =
			gs.phase === 'NIGHT' ? 0xff101829 : (isDusk ? 0xff7a5c3e : 0xff4a6fa5);
		drawRect(skyDraw, 0, 0, Screen.width, Screen.height, skyColor);

		// 天空 / 夜幕贴图（随窗口尺寸重设，按状态显隐）
		for (const item of skyArts) {
			if (item.sprite === undefined) continue;
			const cover = artCoverSize(item.id, Screen.width, Screen.height);
			item.sprite.size = cover;
			item.sprite.x = (Screen.width - cover.width) / 2;
			item.sprite.visible =
				item.id === 'sky_night'
					? gs.phase === 'NIGHT'
					: (item.id === 'sky_dusk' ? isDusk : gs.phase === 'DAY' && !isDusk);
		}
		if (nightMaskArt !== undefined) {
			nightMaskArt.visible = gs.phase === 'NIGHT';
		}

		if (gs.phase === 'NIGHT') {
			drawRect(nightMaskDraw, 0, 0, Screen.width, Screen.height, 0x440b1426);
			// 城墙火把与敌台灯笼（含盐田新敌台）
			const torchXs = [
				GameConfig.MAP_LANDMARKS.WEST_SALT_FLAT.x,
				GameConfig.MAP_LANDMARKS.WEST_PADDY.x,
				GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x,
				GameConfig.MAP_LANDMARKS.SALT_OFFICE.x,
				GameConfig.MAP_LANDMARKS.INNER_GATE.x,
				GameConfig.MAP_LANDMARKS.MAIN_WALL.x,
				GameConfig.MAP_LANDMARKS.EAST_GATE.x,
				GameConfig.MAP_LANDMARKS.EAST_PADDY.x,
				GameConfig.MAP_LANDMARKS.EAST_SALT_FLAT.x,
			];
			for (const tx of torchXs) {
				if (artAt(torchArtNode, 'fx_torch_glow', tx, GameConfig.GROUND_Y + 95) === undefined) {
					torchDraw.drawDot(Vec2(tx, GameConfig.GROUND_Y + 95), 14, Color(0x88f6ad55));
					torchDraw.drawDot(Vec2(tx, GameConfig.GROUND_Y + 95), 6, Color(0xfffefcbf));
				}
			}
		}

		// 王氏宗祠（升到 2 级后换用升级版贴图）
		const hallLm = GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL;
		shrineArtNode.x = hallLm.x;
		shrineArtNode.y = GameConfig.GROUND_Y;
		const hallArtId = landmarkArtId('ANCESTRAL_HALL');
		if (artInto(shrineArtNode, hallArtId, reflectOf(shrineArtNode)) === undefined) {
			drawRect(
				gatesDraw,
				hallLm.x - hallLm.width / 2,
				GameConfig.GROUND_Y,
				hallLm.width,
				hallLm.height,
				hallLm.color,
				0xffe2e8f0
			);
		}

		// 内城水门（耐久归零后换成破损贴图）
		const innerLm = GameConfig.MAP_LANDMARKS.INNER_GATE;
		innerGateArtNode.x = innerLm.x;
		innerGateArtNode.y = GameConfig.GROUND_Y;
		if (gs.innerGateHp > 0) {
			if (artInto(innerGateArtNode, landmarkArtId('INNER_GATE'), reflectOf(innerGateArtNode)) === undefined) {
				drawRect(
					gatesDraw,
					innerLm.x - innerLm.width / 2,
					GameConfig.GROUND_Y,
					innerLm.width,
					innerLm.height,
					innerLm.color,
					0xffe2e8f0
				);
			}
		} else if (artInto(innerGateArtNode, 'lm_INNER_GATE_broken', reflectOf(innerGateArtNode)) === undefined) {
			drawRect(
				gatesDraw,
				innerLm.x - innerLm.width / 2,
				GameConfig.GROUND_Y,
				innerLm.width,
				32,
				0xff2d3748
			);
		}

		// 东门瓮城：门楼只按「等级 / 破损」换模型，开闭只体现为闸门升降
		const eastLm = GameConfig.MAP_LANDMARKS.EAST_GATE;
		gateArtNode.x = eastLm.x;
		gateArtNode.y = GameConfig.GROUND_Y;
		if (gs.eastGateHp <= 0) {
			if (artInto(gateArtNode, 'lm_EAST_GATE_broken', reflectOf(gateArtNode)) === undefined) {
				drawRect(
					gatesDraw,
					eastLm.x - eastLm.width / 2,
					GameConfig.GROUND_Y,
					eastLm.width,
					36,
					0xff2d3748
				);
			}
		} else if (artInto(gateArtNode, landmarkArtId('EAST_GATE'), reflectOf(gateArtNode)) === undefined) {
			drawRect(
				gatesDraw,
				eastLm.x - eastLm.width / 2,
				GameConfig.GROUND_Y,
				eastLm.width,
				eastLm.height,
				eastLm.color,
				0xfff6ad55
			);
		}

		// 闸门：独立节点，位置交给每帧的滑轨插值，这里只管素材与开关目标
		portcullisNode.x = eastLm.x;
		gateLiftTarget = gs.eastGateHp > 0 && gs.eastGateOpen ? 1 : 0;
		if (gs.eastGateHp <= 0) gateLift = 1; // 破损：闸门已毁，不再重画
		portcullisDraw.clear();
		if (gs.eastGateHp > 0) {
			portcullisNode.visible = true;
			if (artInto(portcullisNode, 'gate_portcullis') === undefined && !portcullisDrawBuilt) {
				// 无素材时的程序化铁栅门（落在门洞口，向上提入楼内）
				for (let i = -2; i <= 2; i++) {
					drawRect(portcullisDraw, i * 12 - 3, 0, 6, 74, 0xff2d3748, 0xff718096);
				}
				drawRect(portcullisDraw, -34, 70, 68, 8, 0xff4a5568, 0xff1a202c);
				portcullisNode.addChild(portcullisDraw);
				portcullisDrawBuilt = true;
			}
		} else {
			portcullisNode.visible = false;
		}
	};

	// ---- 营建工程：读秒施工 + 工地可视化 ----
	const projectLayer = Node();
	projectLayer.anchor = Vec2(0, 0);
	projectLayer.size = Size(GameConfig.MAP_WIDTH, Screen.height);
	worldLayer.addChild(projectLayer);
	const projectViews: ProjectView[] = [];

	/** 工地可视化：进度条 + 抡锤动画 + 敲出火花 */
	const syncProjectViews = (dt: number) => {
		for (let i = projectViews.length - 1; i >= 0; i--) {
			if (gs.projects.indexOf(projectViews[i].p) < 0) {
				projectViews[i].node.removeFromParent();
				projectViews.splice(i, 1);
			}
		}

		for (const p of gs.projects) {
			let view: ProjectView | undefined = undefined;
			for (const v of projectViews) {
				if (v.p === p) view = v;
			}
			if (view === undefined) {
				const node = Node();
				node.x = p.x;
				node.y = GameConfig.GROUND_Y + p.targetLevel * 2;
				const bar = DrawNode();
				node.addChild(bar);
				const label = Label('sarasa-mono-sc-regular', 12) as Label.Type;
				label.y = 28;
				label.color = Color(0xff9ae6b4);
				node.addChild(label);
				const hammer = artAt(node, 'icon_tool_hammer', 56, 8);
				if (hammer !== undefined) {
					hammer.anchor = Vec2(0.5, 0.5);
					hammer.size = Size(30, 30);
				}
				worldLayer.addChild(node);
				view = { p, node, bar, label, hammer };
				projectViews.push(view);
			}

			const pct = Math.max(0, Math.min(1, 1 - p.remain / Math.max(0.001, p.total)));
			view.bar.clear();
			drawRect(view.bar, -46, -10, 92, 10, 0xcc1a202c, 0xff4a5568);
			drawRect(view.bar, -45, -9, 90 * pct, 8, 0xff48bb78);
			view.label.text = `${p.label} ${Math.floor(pct * 100)}%${p.workers > 0 ? ` · 匠${p.workers}` : ' · 无匠'}`;

			// 工匠在场才抡锤，抡得快慢随人数
			if (view.hammer !== undefined && p.workers > 0) {
				const swing = Math.abs(Math.sin(p.hammerTimer * (6 + p.workers * 2)));
				view.hammer.angle = 40 - swing * 80;
			}
			if (p.workers > 0 && Math.random() < dt * 3) {
				playFx(worldLayer, 'fx_arrow_hit', p.x + 30, GameConfig.GROUND_Y + 22, 0.26, 0.35, 8);
				soundSfx('build_hammer');
			}
		}
	};

	/** 工程竣工结算（等级 / 耐久 / 贴图 / 特效） */
	const completeProject = (p: BuildProject) => {
		soundSfx('upgrade');
		if (p.kind === 'HALL_UPGRADE') {
			const oldHpBonus = gs.moraleHpBonus;
			gs.ancestralHallLevel++;
			gs.ancestralHallMaxHp += GameConfig.ANCESTRAL_HALL_HP_PER_LEVEL;
			gs.ancestralHallHp = Math.min(
				gs.ancestralHallMaxHp,
				gs.ancestralHallHp + GameConfig.ANCESTRAL_HALL_HP_PER_LEVEL
			);
			// 祠堂香火更旺：在册族人按角色基础血量同步长气血（现役也回血）
			const hpGain = gs.moraleHpBonus - oldHpBonus;
			if (hpGain > 0) {
				for (const v of villagers) {
					if (v.dead) continue;
					const gain = Math.round(GameConfig.ROLES[v.role].maxHp * hpGain);
					v.maxHp += gain;
					v.hp = Math.min(v.maxHp, v.hp + gain);
				}
				// 敌台同沾宗祠香火：已启用的弩炮/炮台气血同步增长
				for (const t of gs.towers) {
					if (!t.unlocked) continue;
					const gain = Math.round(GameConfig.TOWER_STATS[t.type].baseHp * hpGain);
					t.maxHp += gain;
					t.hp = Math.min(t.maxHp, t.hp + gain);
				}
			}
			refreshEnvironmentVisuals();
			playFx(
				worldLayer,
				'fx_levelup',
				GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x,
				GameConfig.GROUND_Y + 90,
				0.7,
				0.35,
				26
			);
			hud.showToast(
				`王氏宗祠竣工，升至 Lv.${gs.ancestralHallLevel}！族人士气 +${Math.round(
					gs.moraleBonus * 100
				)}%（攻速/伤害），气血 +${Math.round(gs.moraleHpBonus * 100)}%。`,
				2.8
			);
			return;
		}

		if (p.kind === 'EAST_GATE_UPGRADE') {
			gs.eastGateLevel++;
			gs.eastGateMaxHp += 350;
			gs.eastGateHp = gs.eastGateMaxHp;
			refreshEnvironmentVisuals();
			playFx(
				worldLayer,
				'fx_levelup',
				GameConfig.MAP_LANDMARKS.EAST_GATE.x,
				GameConfig.GROUND_Y + 120,
				0.7,
				0.35,
				26
			);
			hud.showToast(`东门瓮城加固竣工，升至 Lv.${gs.eastGateLevel}！`, 2.4);
			return;
		}

		if (p.kind === 'HOUSE_UPGRADE') {
			const idx = Number(p.towerId.replace('HOUSE:', ''));
			const house = gs.houses[idx];
			if (house !== undefined) {
				house.level = Math.min(GameConfig.HOUSE_MAX_LEVEL, house.level + 1);
				house.maxHp = GameConfig.HOUSE_BASE_HP + (house.level - 1) * 120;
				house.hp = house.maxHp;
				refreshHouses();
				playFx(worldLayer, 'fx_levelup', house.x, GameConfig.GROUND_Y + 70, 0.6, 0.3, 22);
				hud.showToast(
					`民居${house.level === 1 ? '落成' : `升至 Lv.${house.level}`}，可住 ${gs.housingCapacity} 人。`,
					2.4
				);
			}
			return;
		}

		if (p.kind === 'INNER_GATE_UPGRADE') {
			gs.innerGateLevel++;
			gs.innerGateMaxHp += 320;
			gs.innerGateHp = gs.innerGateMaxHp;
			refreshEnvironmentVisuals();
			playFx(
				worldLayer,
				'fx_levelup',
				GameConfig.MAP_LANDMARKS.INNER_GATE.x,
				GameConfig.GROUND_Y + 120,
				0.7,
				0.35,
				26
			);
			hud.showToast(`内城水门加固竣工，升至 Lv.${gs.innerGateLevel}！`, 2.4);
			return;
		}

		if (p.kind === 'LAND_RECLAIM') {
			const id = p.towerId as LandmarkId;
			const lm = GameConfig.MAP_LANDMARKS[id];
			const level = gs.landLevelOf(id) + 1;
			gs.landLevels[id] = level;
			refreshLandmarkArt();
			refreshEnvironmentVisuals();
			playFx(worldLayer, 'fx_levelup', lm.x, GameConfig.GROUND_Y + 60, 0.6, 0.3, 22);
			const kind = lm.reclaimable;
			const extra =
				kind === 'PADDY'
					? `每季多收 ${GameConfig.RECLAIM.PADDY_YIELD_PER_LEVEL} 石粮`
					: `每趟多出 ${GameConfig.RECLAIM.SALT_YIELD_PER_LEVEL} 两盐银`;
			hud.showToast(`${lm.name}开垦至 Lv.${level}，${extra}。`, 2.8);
			return;
		}

		let tower: DefenseTower | undefined = undefined;
		for (const t of towers) {
			if (t.state.id === p.towerId) tower = t;
		}
		if (tower === undefined) return;
		if (p.kind === 'TOWER_UNLOCK') {
			tower.state.unlocked = true;
			// 新敌台同样享受宗祠士气带来的气血加成
			const boosted = Math.round(
				GameConfig.TOWER_STATS[tower.state.type].baseHp * (1 + gs.moraleHpBonus)
			);
			if (boosted > tower.state.maxHp) {
				tower.state.maxHp = boosted;
				tower.state.hp = boosted;
			}
		} else {
			tower.state.level++;
			tower.state.maxHp += 120;
			tower.state.hp = tower.state.maxHp;
		}
		tower.refreshVisual();
		playFx(worldLayer, 'fx_levelup', tower.state.x, GameConfig.GROUND_Y + 90, 0.7, 0.35, 24);
		hud.showToast(`${p.label}竣工！`, 2.2);
	};

	/** 发起一项营建工程：白银当场扣除，效果等工期走完才生效 */
	const beginProject = (
		kind: ProjectKind,
		label: string,
		x: number,
		seconds: number,
		targetLevel: number,
		towerId = ''
	): boolean => {
		if (gs.hasProject(kind, towerId)) {
			hud.showToast(`「${label}」已在施工中，等候工匠完工。`, 2.0);
			return false;
		}
		gs.startProject(kind, label, x, seconds, targetLevel, towerId);
		hud.showToast(GameConfig.HISTORICAL_QUOTES.PROJECT_STARTED, 2.4);
		return true;
	};

	const startNightPhase = () => {
		if (gs.phase === 'NIGHT') return;
		gs.phase = 'NIGHT';
		gs.duskWarned = false;
		// 入夜：号角 + 城门落锁，BGM 切夜间曲
		soundBgm('night');
		soundSfx('wave_horn');
		soundSfx('gate_open');
		if (gs.eastGateOpen && gs.eastGateHp > 0) {
			gs.eastGateOpen = false;
			refreshEnvironmentVisuals();
			hud.showToast('暮鼓一响，东门落锁。若还要出城拾荒，到东门按 [E] 再开门。', 2.6);
		}
		nightElapsed = 0;
		foodConsumeTimer = 0;

		// 宗祠春祭祈福：全体义师恢复 20% 血量
		for (const v of villagers) {
			v.healPercent(GameConfig.SPRING_BLESSING_HEAL_RATIO);
		}
		hud.showToast(GameConfig.HISTORICAL_QUOTES.SPRING_BLESSING, 3.2);

		// 装载本夜倭寇波次
		const wave = GameConfig.NIGHT_WAVES[gs.day - 1];
		spawnQueue = [];
		// 两面上岸的距离不一样（西岸离堡更近），把西面的登岸往后推一点，
		// 免得西面贼兵抢到城下时东面还在赶路、守城节奏完全对不上。
		const hallX = GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x;
		const eastTravel = GameConfig.SPAWN_EAST_X - hallX;
		const westTravel = hallX - GameConfig.SPAWN_WEST_X;
		for (let gi = 0; gi < wave.groups.length; gi++) {
			const g = wave.groups[gi];
			// 未显式指定登岸面时，按组序东西交替：倭寇两面夹击
			const side: 'W' | 'E' = g.side !== undefined ? g.side : gi % 2 === 0 ? 'W' : 'E';
			const stat = GameConfig.ENEMIES[g.enemyType];
			const gapSeconds =
				((eastTravel - westTravel) / Math.max(1, stat.moveSpeed)) *
				GameConfig.WEST_LANDING_DELAY_RATIO;
			const sideDelay = side === 'W' ? Math.max(0, gapSeconds) : 0;
			for (let i = 0; i < g.count; i++) {
				spawnQueue.push({
					enemyType: g.enemyType,
					triggerTime: g.delay + sideDelay + i * g.interval,
					side,
				});
			}
		}
		// —— 码头状态直接决定这一夜从哪一侧上来多少人 ——
		// 栈桥完好：那一侧成建制上岸，还额外多运一船人（LANDING_BONUS_COUNT）。
		// 栈桥被砸断：那一侧掉到散兵比例（BROKEN_SIDE_RATIO）。
		// 拆过码头：欠下的血债当夜就从那一侧摸黑还回来（每锤 1 人，拆断再补 REVENGE_COUNT 人）。
		for (const side of ['W', 'E'] as ('W' | 'E')[]) {
			const sideName = side === 'W' ? '西' : '东';
			const alive = gs.pierAlive(side);
			const revenge = gs.takePierRevenge(side);
			if (alive) {
				// 码头完好：多运一船人（从这一侧上岸）
				const bonus = GameConfig.PIER.LANDING_BONUS_COUNT;
				const type: 'SCOUT' | 'SAMURAI' = gs.day >= 4 ? 'SAMURAI' : 'SCOUT';
				for (let i = 0; i < bonus; i++) {
					spawnQueue.push({ enemyType: type, triggerTime: 1.2 + i * 0.5, side });
				}
			} else {
				// 码头断了：这一侧的贼兵按比例打散，剩下的才是摸上来的散兵
				const pile = spawnQueue.filter((q) => q.side === side);
				const keep = Math.max(0, Math.round(pile.length * GameConfig.PIER.BROKEN_SIDE_RATIO));
				let drop = pile.length - keep;
				if (drop > 0) {
					spawnQueue = spawnQueue.filter((q) => {
						if (q.side !== side || drop <= 0) return true;
						drop--;
						return false;
					});
					hud.showToast(`码头没了：${sideName}岸只摸上来 ${keep} 个散兵。`, 2.4);
				}
			}
			if (revenge > 0) {
				// 砸过的码头会讨债：债主是这一侧的贼众
				const type: 'SCOUT' | 'SAMURAI' = gs.day >= 4 ? 'SAMURAI' : 'SCOUT';
				for (let i = 0; i < revenge; i++) {
					spawnQueue.push({ enemyType: type, triggerTime: 0.8 + i * 0.7, side });
				}
				hud.showToast(
					`${sideName}岸火把连成一条线：砸码头的账，今夜连本带利 ${revenge} 个人回来！`,
					3.2
				);
			}
		}
		refreshEnvironmentVisuals();
	};

	/**
	 * 银袋抛物线：投银时飞向升级点（专用美术缺失时退回程序化小方块，不影响可读性）
	 */
	const silverThrows: {
		node: Node.Type;
		t: number;
		x0: number;
		y0: number;
		x1: number;
		y1: number;
	}[] = [];
	const spawnSilverThrow = (x0: number, x1: number) => {
		soundSfx('coin_silver');
		const n = Node();
		if (artAt(n, 'fx_silver_pouch', 0, 0) === undefined) {
			const d = DrawNode();
			drawRect(d, -8, -8, 16, 16, 0xfff6e05e, 0xff744210);
			n.addChild(d);
		}
		n.x = x0;
		n.y = GameConfig.GROUND_Y + 46;
		worldLayer.addChild(n);
		silverThrows.push({
			node: n,
			t: 0,
			x0,
			y0: GameConfig.GROUND_Y + 46,
			x1,
			y1: GameConfig.GROUND_Y + 34,
		});
	};

	/**
	 * 「钱袋子飘银」：银钱离袋时，从钱袋位置往上飘一枚银钱并逐渐化去。
	 * 配合 `-N 两` 飘字，让「我确实花了这笔银」看得见。
	 */
	const silverRises: { node: Node.Type; t: number }[] = [];
	const spawnSilverRise = (x: number, amount: number) => {
		const n = Node();
		if (artAt(n, 'fx_silver_rise', 0, 0) === undefined) {
			const d = DrawNode();
			drawRect(d, -5, -9, 10, 18, 0xfff6e05e, 0xff744210);
			n.addChild(d);
		}
		n.x = x;
		n.y = GameConfig.GROUND_Y + 38;
		worldLayer.addChild(n);
		silverRises.push({ node: n, t: 0 });
		addFloatingText(`-${amount} ${GameConfig.SILVER_NAME}`, x, GameConfig.GROUND_Y + 104, 0xfff6e05e);
	};

	/** 投银点账目：key → 显示名与所需总额（供 HUD 显示“还差多少”） */
	const donationBook: { key: string; label: string; cost: number }[] = [];
	const rememberDonation = (key: string, label: string, cost: number) => {
		for (const d of donationBook) {
			if (d.key === key) {
				d.label = label;
				d.cost = cost;
				return;
			}
		}
		donationBook.push({ key, label, cost });
	};

	/** 当前所有没捐满的池子，形如「招募族丁 40/80」；全都空了就返回空串 */
	const donationSummary = (): string => {
		const parts: string[] = [];
		for (const d of donationBook) {
			const have = gs.donationOf(d.key);
			if (have > 0) parts.push(`${d.label} ${have}/${d.cost}`);
		}
		return parts.join('  ');
	};

	/**
	 * 投一袋银两到升级点：捐满 cost 才动工，多投的留在池里下次接着攒。
	 * 所有升级/建造/置办/招募都走这里——“银两升级都得人跑过去扔”。
	 */
	const pulseArtAtX = (x: number, intensity = 0.07, dur = 0.30) => {
		if (Math.abs(x - GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x) < 40) {
			pulseNode(shrineArtNode, intensity, dur);
			return;
		}
		if (Math.abs(x - GameConfig.MAP_LANDMARKS.INNER_GATE.x) < 40) {
			pulseNode(innerGateArtNode, intensity, dur);
			return;
		}
		if (Math.abs(x - GameConfig.MAP_LANDMARKS.EAST_GATE.x) < 40) {
			pulseNode(gateArtNode, intensity, dur);
			return;
		}
		for (const id of landmarkArtRow) {
			if (Math.abs(x - GameConfig.MAP_LANDMARKS[id].x) < 40) {
				pulseNode(landmarkArtNodes[id], intensity, dur);
				return;
			}
		}
		for (let i = 0; i < gs.houses.length; i++) {
			if (Math.abs(x - gs.houses[i].x) < 30) {
				pulseNode(houseArtNodes[i], intensity, dur);
				return;
			}
		}
	};

	const throwSilver = (
		purpose: string,
		targetX: number,
		cost: number,
		label: string,
		onFull: () => void
	) => {
		rememberDonation(purpose, label, cost);
		// 银两的最小面额就是 1 两：还差多少就投多少，最后一袋可能只投 1 两。
		// 所以这里不再固定投一整袋，而是按差额截断。
		const remain = Math.max(1, cost - gs.donationOf(purpose));
		const bag = Math.min(GameConfig.SILVER_BAG, remain);
		if (gs.silver < bag) {
			hud.showToast(
				`白银不足，还差 ${remain} ${GameConfig.SILVER_NAME}（现有 ${gs.silver} ${GameConfig.SILVER_NAME}）。`,
				2.0
			);
			return;
		}
		gs.spendSilver(bag);
		spawnSilverRise(player.x + player.facing * 10, bag);
		spawnSilverThrow(player.x + player.facing * 18, targetX);
		pulseArtAtX(targetX, 0.06, 0.28);
		playFx(worldLayer, 'fx_arrow_hit', targetX, GameConfig.GROUND_Y + 46, 0.25, 0.3, 10);
		const total = gs.addDonation(purpose, bag);
		if (total >= cost) {
			gs.clearDonation(purpose);
			pulseArtAtX(targetX, 0.10, 0.38);
			onFull();
			return;
		}
		hud.showToast(
			`【${label}】已投 ${total}/${cost} ${GameConfig.SILVER_NAME}，继续投银。`,
			1.6
		);
	};

	/** 站在哪间民居的投银点旁（-1 = 不在任何民居旁） */
	const houseInRange = (): number => {
		let best = -1;
		let bestDist = GameConfig.PLAYER.interactRange;
		for (let i = 0; i < gs.houses.length; i++) {
			const d = Math.abs(gs.houses[i].x - player.x);
			if (d <= bestDist) {
				bestDist = d;
				best = i;
			}
		}
		return best;
	};

	/** 民居下一级要投多少银：空地起造最便宜，越往上越贵 */
	const houseUpgradeCost = (level: number): number => {
		if (level <= 0) return GameConfig.HOUSE_BUILD_COST;
		if (level >= 2) return GameConfig.HOUSE_UPGRADE_COST_LV3;
		return GameConfig.HOUSE_UPGRADE_COST_LV2;
	};

	/**
	 * 普通攻击（空格 / L / HUD「出拳」）：不位移的短打。
	 * 麒麟步是「冲过去一记重手」，这个是站着也能连的平A，两者冷却各算各的。
	 */
	/**
	 * 砍中码头：砸桥是「攻击行为」，不是「交互」。
	 * 每刀记 1 点人头债，砍断那一刻再额外记 REVENGE_COUNT——所以拆桥爽一时，当夜还账。
	 */
	/** 每侧被砸了几锤（用来算什么时候放人抢滩） */
	const pierHits: Record<string, number> = { W: 0, E: 0 };

	/**
	 * 砸栈桥当场招来的抢滩小队：不等天黑，岸边贼船立刻放人往岸上冲。
	 * 敲得越很，来得越多——拆断那一刻还有 BREAK_GUARD_COUNT 个一起上。
	 */
	const pierGuardWave = (side: 'W' | 'E', count: number): void => {
		const pierX = GameConfig.MAP_LANDMARKS[side === 'W' ? 'WEST_PIER' : 'EAST_PIER'].x;
		// 从码头再往岸上让一段，免得人卡在栈桥里
		const off = GameConfig.PIER.GUARD_SPAWN_OFFSET;
		const shoreX =
			side === 'W'
				? Math.min(GameConfig.MAP_WIDTH - 120, pierX + off)
				: Math.max(120, pierX - off);
		// 场上人太多就先不加：既防卡顿，也给玩家喘口气的余地
		const alive = enemies.filter((e) => !e.dead && !e.escaped).length;
		const room = Math.max(0, GameConfig.PIER.GUARD_ALIVE_CAP - alive);
		const n = Math.min(count, room);
		for (let i = 0; i < n; i++) {
			// 散兵占大头，但每三个夹一个武士——一上一下的压迫感差很多
			const type: EnemyType = i % 3 === 2 ? 'SAMURAI' : 'SCOUT';
			// 拉成一条抢滩纵列，不要堆在同一个像素上
			const stagger = 26 + i * 34;
			const enemy = new Enemy(type, side === 'W' ? shoreX + stagger : shoreX - stagger, side);
			enemies.push(enemy);
			worldLayer.addChild(enemy.node);
		}
		playFx(worldLayer, 'fx_shockwave', shoreX, GameConfig.GROUND_Y + 26, 0.6, 0.6, 0);
		playFx(worldLayer, 'fx_torch_glow', shoreX, GameConfig.GROUND_Y + 60, 0.9, 0.35, 12);
		addFloatingText(`贼船在放人上岸！×${n}`, shoreX, GameConfig.GROUND_Y + 140, 0xfffc8181);
		soundSfx('drum_rally');
	};

	/**
	 * 拆断栈桥后的现场：浪里散板 + 余烟，桥永远看着是断的。
	 */
	const paintPierWreck = (side: 'W' | 'E'): void => {
		const pierX = GameConfig.MAP_LANDMARKS[side === 'W' ? 'WEST_PIER' : 'EAST_PIER'].x;
		for (let i = 0; i < 6; i++) {
			const dx = (i % 2 === 0 ? -1 : 1) * (18 + i * 21);
			// 浪里的断板：逐张半沉、不整齐，看着像散落的碎木
			artAt(pierDebrisNode, 'salvage_driftwood', pierX + dx, GameConfig.GROUND_Y + 6 + (i % 3) * 7);
		}
	};

	const damagePier = (side: 'W' | 'E', pierX: number, amount: number): void => {
		if (!gs.pierAlive(side)) return;
		const before = gs.pierHpOf(side);
		const after = Math.max(0, before - amount);
		gs.setPierHp(side, after);
		gs.addPierRevenge(side, 1);
		playFx(worldLayer, 'fx_arrow_hit', pierX, GameConfig.GROUND_Y + 46, 0.25, 0.3, 8);
		pulseArtAtX(pierX, 0.06, 0.22);
		soundSfx('build_hammer');
		const sideName = side === 'W' ? '西' : '东';
		// 血过半：外层换成「半毁」素材，不用等它整座断掉
		const maxHp = gs.pierMaxHp;
		if (before * 2 > maxHp && after * 2 <= maxHp) refreshEnvironmentVisuals();
		pierHits[side] += 1;
		pierGuardWave(side, GameConfig.PIER.GUARD_PER_HIT);
		if (after <= 0) {
			gs.addPierRevenge(side, GameConfig.PIER.REVENGE_COUNT);
			refreshEnvironmentVisuals();
			paintPierWreck(side);
			pierGuardWave(side, GameConfig.PIER.BREAK_GUARD_COUNT);
			hud.showToast(
				`【${sideName}滩倭寇码头】栈桥断成两截！${sideName}岸的贼船当场放人抢滩，这一夜的账也用不着等到天黑。`,
				3.0
			);
		} else {
			hud.showToast(`栈桥 ${after}/${gs.pierMaxHp}，岸上已经有人在放船了。`, 1.4);
		}
	};

	/**
	 * 攻击扫过的区间 [x0, x1] 碰到哪座码头，就把它当作受击目标。
	 * 判定把码头身位放宽 HIT_BOX_HALF，所以站在岸边原地出拳也够得着；
	 * 麒麟步则是从起手点到落点一路扫过去，能隔着半座桥打到。
	 */
	const attackPiers = (x0: number, x1: number, amount: number): boolean => {
		const lo = Math.min(x0, x1);
		const hi = Math.max(x0, x1);
		let hit = false;
		const piers: Array<{ id: LandmarkId; side: 'W' | 'E' }> = [
			{ id: 'WEST_PIER', side: 'W' },
			{ id: 'EAST_PIER', side: 'E' },
		];
		for (const p of piers) {
			const pierX = GameConfig.MAP_LANDMARKS[p.id].x;
			if (!gs.pierAlive(p.side)) continue;
			const half = GameConfig.PIER.HIT_BOX_HALF;
			if (hi < pierX - half || lo > pierX + half) continue;
			damagePier(p.side, pierX, amount);
			hit = true;
		}
		return hit;
	};

	const lightAttack = (): void => {
		if (waitingVictoryModal) return;
		const res = player.triggerLightAttack(enemies);
		if (!res.triggered) return;
		// 拳头也能砍栈桥：以主角为中心往朝向伸出 HIT_REACH
		const reach = GameConfig.PLAYER.lightRange + GameConfig.PIER.HIT_REACH;
		attackPiers(player.x - GameConfig.PIER.HIT_BOX_HALF, player.x + player.facing * reach, GameConfig.PIER.HIT_DAMAGE);
		if (res.hitCount > 0) {
			// 命中才飘字，抡空不脏屏；命中的敌人头顶另起一个小火花
			addFloatingText(
				res.hitCount > 1 ? `连击 ×${res.hitCount}` : '中！',
				player.x + player.facing * 40,
				GameConfig.GROUND_Y + 78,
				0xfffbd38d
			);
		}
	};

	/**
	 * 麒麟步号令：主角一冲，冲锋扫过的整段都算攻击范围，而且这条防线上的敌台
	 * 会立刻替他出箭。主角自己不加伤害——「弟兄们看见卫所官冲阵，替你放箭」。
	 */
	const qilinAttack = (fromX: number): void => {
		// ① 扫过的整段都算攻击范围：从起手点到落点 + 刀刃余势
		const reach = GameConfig.PLAYER.attackRange + GameConfig.PIER.HIT_REACH;
		attackPiers(
			Math.min(fromX, player.x) - GameConfig.PIER.HIT_BOX_HALF,
			Math.max(fromX, player.x) + player.facing * reach,
			GameConfig.PLAYER.attackDamage
		);
		// ② 这一段城墙上的敌台应令发矢
		let fired = 0;
		for (const t of towers) {
			if (!t.state.unlocked || t.state.hp <= 0) continue;
			if (Math.abs(t.state.x - fromX) > GameConfig.QILIN.TOWER_RANGE) continue;
			if (t.forceFire(enemies, player.x)) fired++;
		}
		if (fired > 0) {
			addFloatingText(`敌台发矢 ×${fired}`, player.x, GameConfig.GROUND_Y + 128, 0xff90cdf4);
			playFx(worldLayer, 'fx_levelup', player.x, GameConfig.GROUND_Y + 110, 0.5, 0.3, 12);
		}
	};

	/** [F] 撒银退敌：给最近的倭寇一笔银子，让他掉头离场（头目只买得到一瞬喘息） */
	const bribeNearestEnemy = () => {
		if (waitingVictoryModal) return;
		let target: Enemy | undefined = undefined;
		let bestDist = GameConfig.BRIBE_RANGE;
		for (const e of enemies) {
			if (e.dead || e.escaped || e.bribed) continue;
			const d = Math.abs(e.x - player.x);
			if (d <= bestDist) {
				bestDist = d;
				target = e;
			}
		}
		if (target === undefined) {
			hud.showToast(`身侧百步没有可以买通的倭寇。`, 1.8);
			return;
		}
		const cost = GameConfig.BRIBE_COST[target.type];
		if (gs.silver < cost) {
			hud.showToast(`买命需 ${cost} ${GameConfig.SILVER_NAME}，库中不足！`, 1.8);
			return;
		}
		gs.spendSilver(cost);
		spawnSilverRise(player.x + player.facing * 10, cost);
		spawnSilverThrow(player.x + player.facing * 18, target.x);
		target.bribe();
		if (target.type === 'BOSS') {
			hud.showToast(`塞了 ${cost} ${GameConfig.SILVER_NAME}给倭酋，只撂得他踉跄一阵！`, 2.4);
		} else {
			hud.showToast(`付 ${cost} ${GameConfig.SILVER_NAME}买命，倭寇收银退兵。`, 2.0);
		}
	};

	/** 开垦荒地：水田 / 盐田从 0 级「荒地」逐级开荒，工期遂级增长 */
	const startReclaim = (id: LandmarkId, x: number) => {
		const lm = GameConfig.MAP_LANDMARKS[id];
		const kind = lm.reclaimable;
		if (kind !== 'PADDY' && kind !== 'SALT') return;
		const level = gs.landLevelOf(id);
		if (level >= GameConfig.RECLAIM.MAX_LEVEL) {
			hud.showToast(`${lm.name}已是上等熟田（Lv.${level}），再无可垦之地。`, 2.2);
			return;
		}
		if (gs.hasProject('LAND_RECLAIM', id)) {
			hud.showToast('这片荒地正在开垦中。', 2.0);
			return;
		}
		const cost = GameConfig.RECLAIM.COST[kind] * (level + 1);
		const seconds = GameConfig.RECLAIM.SECONDS[kind] * (1 + 0.25 * level);
		const label = `${lm.name} 开垦 Lv.${level + 1}`;
		throwSilver(`RECLAIM:${id}`, x, cost, label, () =>
			beginProject('LAND_RECLAIM', label, x, seconds, level + 1, id)
		);
	};

	const handleInteract = (optionIndex = 0) => {
		if (waitingVictoryModal) return;

		// 民居优先：站到民居投银点旁就是「投银起造 / 扩建民居」
		const houseIdx = houseInRange();
		if (houseIdx >= 0) {
			const house = gs.houses[houseIdx];
			if (house.level >= GameConfig.HOUSE_MAX_LEVEL) {
				hud.showToast(`民居已达最高等级，可住 ${house.level * GameConfig.HOUSE_CAPACITY_PER_LEVEL} 人。`, 2.0);
				return;
			}
			const key = `HOUSE:${house.index}`;
			if (gs.hasProject('HOUSE_UPGRADE', key)) {
				hud.showToast('这间民居正在施工中。', 2.0);
				return;
			}
			const cost = houseUpgradeCost(house.level);
			const targetLevel = house.level + 1;
			throwSilver(key, house.x, cost, house.level <= 0 ? '起造民居' : '扩建民居', () =>
				beginProject(
					'HOUSE_UPGRADE',
					`民居 Lv.${targetLevel}`,
					house.x,
					GameConfig.CONSTRUCTION_SECONDS.HOUSE_UPGRADE,
					targetLevel,
					key
				)
			);
			return;
		}

		const landmark = player.findNearestLandmark();
		if (!landmark) {
			hud.showToast('请靠近宗祠、民居、水田、盐田、盐课司、内城水门、主城墙、东门或滩头后再交互', 2.0);
			return;
		}

		// 两头的倭寇码头：完好时那一侧成建制上岸（还会多运一船人），
		// 砸断那一侧只剩散兵摸上来；但每砸一下记一个人头债，当夜就连本带利还回来。
		// 注意：砸桥是「攻击」不是「交互」——用普通攻击或麒麟步打，
		// 走到跟前按 [E] 只做一件事：花银两把断桥修回来。
		if (landmark === 'WEST_PIER' || landmark === 'EAST_PIER') {
			const side: 'W' | 'E' = landmark === 'WEST_PIER' ? 'W' : 'E';
			const sideName = side === 'W' ? '西' : '东';
			const pierX = GameConfig.MAP_LANDMARKS[landmark].x;
			if (!gs.pierAlive(side)) {
				const cost = GameConfig.PIER.REPAIR_SILVER;
				if (!gs.spendSilver(cost)) {
					hud.showToast(`修栈桥要 ${cost} ${GameConfig.SILVER_NAME}，库里不够。`, 1.8);
					return;
				}
				gs.setPierHp(side, gs.pierHpOf(side) + GameConfig.PIER.REPAIR_AMOUNT);
				refreshEnvironmentVisuals();
				playFx(worldLayer, 'fx_levelup', pierX, GameConfig.GROUND_Y + 40, 0.6, 0.3, 20);
				hud.showToast(
					`${sideName}岸栈桥复工：贼船又能靠岸（那一侧也会多运一船人上来）。`,
					2.6
				);
			} else {
				hud.showToast(
					`栈桥 ${gs.pierHpOf(side)}/${gs.pierMaxHp}。要拆它就对着桥出拳 [空格] 或麒麟步 [J]，别按 [E]。`,
					2.0
				);
			}
			return;
		}

		if (landmark === 'ANCESTRAL_HALL') {
			if (optionIndex === 1) {
				if (gs.ancestralHallLevel >= GameConfig.ANCESTRAL_HALL_MAX_LEVEL) {
					hud.showToast('王氏宗祠已达最高等级！', 2.0);
					return;
				}
				const cost = GameConfig.ANCESTRAL_HALL_UPGRADE_BASE_COST * gs.ancestralHallLevel;
				if (gs.hasProject('HALL_UPGRADE')) {
					hud.showToast('宗祠正在施工中，等候工匠完工。', 2.0);
					return;
				}
				// 等级越高工期越长（+20%/级）
				const hallSeconds =
					GameConfig.CONSTRUCTION_SECONDS.HALL_UPGRADE * (1 + 0.2 * (gs.ancestralHallLevel - 1));
				throwSilver('HALL:UPGRADE', GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x, cost, '宗祠营建', () =>
					beginProject(
						'HALL_UPGRADE',
						`宗祠 Lv.${gs.ancestralHallLevel + 1}`,
						GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x,
						hallSeconds,
						gs.ancestralHallLevel + 1
					)
				);
				return;
			}

			if (gs.freeSlots <= 0) {
				hud.showToast(
					`住不下了（住房 ${gs.housingCapacity} / 口粮可养 ${gs.foodCapacity}），请投银起造民居或多种粮。`,
					2.6
				);
				return;
			}
			if (gs.recruits.length >= GameConfig.RECRUIT_MAX_PENDING) {
				hud.showToast('已有族人正在赶来报到的路上，稍候。', 2.0);
				return;
			}
			throwSilver(
				'HALL:RECRUIT',
				GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x,
				GameConfig.RECRUIT_VILLAGER_COST,
				'招募族丁',
				() => {
					gs.startRecruit();
					hud.showToast(
						`已递帖招揽族人，${GameConfig.RECRUIT_SECONDS.toFixed(0)} 秒后到宗祠报到。`,
						2.0
					);
				}
			);
		} else if (landmark === 'WEST_PADDY' || landmark === 'EAST_PADDY') {
			const lmX = GameConfig.MAP_LANDMARKS[landmark].x;
			if (optionIndex === 1) {
				startReclaim(landmark, lmX);
				return;
			}
			const cost = GameConfig.ROLES.FARMER.toolCost;
			throwSilver('TOOL:FARMER', lmX, cost, '置办锄头', () => {
				spawnTool(lmX, 'FARMER');
				addFloatingText('置办【锄头】', lmX, GameConfig.GROUND_Y + 80);
			});
		} else if (landmark === 'SALT_OFFICE') {
			const officeX = GameConfig.MAP_LANDMARKS.SALT_OFFICE.x;
			const cost = GameConfig.ROLES.SALT_WORKER.toolCost;
			throwSilver('TOOL:SALT_WORKER', officeX, cost, '置办盐铲', () => {
				spawnTool(officeX, 'SALT_WORKER');
				addFloatingText('置办【盐铲】', officeX, GameConfig.GROUND_Y + 80);
			});
		} else if (landmark === 'INNER_GATE') {
			if (optionIndex === 2) {
				if (gs.innerGateLevel >= GameConfig.INNER_GATE_MAX_LEVEL) {
					hud.showToast('内城水门已达最高坚固等级！', 2.0);
					return;
				}
				if (gs.hasProject('INNER_GATE_UPGRADE')) {
					hud.showToast('内城水门正在加固中。', 2.0);
					return;
				}
				throwSilver(
					'GATE:INNER',
					GameConfig.MAP_LANDMARKS.INNER_GATE.x,
					GameConfig.INNER_GATE_UPGRADE_COST,
					'内城水门加固',
					() =>
						beginProject(
							'INNER_GATE_UPGRADE',
							`内城水门 Lv.${gs.innerGateLevel + 1}`,
							GameConfig.MAP_LANDMARKS.INNER_GATE.x,
							GameConfig.CONSTRUCTION_SECONDS.INNER_GATE_UPGRADE,
							gs.innerGateLevel + 1
						)
				);
				return;
			}
			if (optionIndex === 1) {
				const innerTower = towers.find((t) => t.state.id === 'INNER_TOWER');
				if (!innerTower) return;
				if (!innerTower.state.unlocked) {
					const cost = 150;
					if (gs.hasProject('TOWER_UNLOCK', 'INNER_TOWER')) {
						hud.showToast('内城炮台正在施工中。', 2.0);
						return;
					}
					throwSilver('TOWER:INNER_TOWER', innerTower.state.x, cost, '内城炮台营建', () =>
						beginProject(
							'TOWER_UNLOCK',
							'内城佛郎机炮台',
							innerTower.state.x,
							GameConfig.CONSTRUCTION_SECONDS.TOWER_UNLOCK,
							1,
							'INNER_TOWER'
						)
					);
				} else {
					const cost = GameConfig.TOWER_STATS.CANNON.upgradeCost;
					if (gs.hasProject('TOWER_UPGRADE', 'INNER_TOWER')) {
						hud.showToast('炮台正在升级中。', 2.0);
						return;
					}
					throwSilver('TOWER:INNER_TOWER', innerTower.state.x, cost, '内城炮台升级', () =>
						beginProject(
							'TOWER_UPGRADE',
							`内城炮台 Lv.${innerTower.state.level + 1}`,
							innerTower.state.x,
							GameConfig.CONSTRUCTION_SECONDS.TOWER_UPGRADE,
							innerTower.state.level + 1,
							'INNER_TOWER'
						)
					);
				}
				return;
			}

			const cost = GameConfig.ROLES.BUILDER.toolCost;
			throwSilver('TOOL:BUILDER', GameConfig.MAP_LANDMARKS.INNER_GATE.x - 30, cost, '置办木锤', () => {
				spawnTool(GameConfig.MAP_LANDMARKS.INNER_GATE.x - 30, 'BUILDER');
				addFloatingText('置办【木锤】', GameConfig.MAP_LANDMARKS.INNER_GATE.x - 30, GameConfig.GROUND_Y + 80);
			});
		} else if (landmark === 'MAIN_WALL') {
			const role: VillagerRole = optionIndex === 1 ? 'KUNG_FU' : 'MILITIA';
			const cfg = GameConfig.ROLES[role];
			throwSilver(`TOOL:${role}`, GameConfig.MAP_LANDMARKS.MAIN_WALL.x, cfg.toolCost, `置办${cfg.toolName}`, () => {
				spawnTool(GameConfig.MAP_LANDMARKS.MAIN_WALL.x, role);
				addFloatingText(
					`置办【${cfg.toolName}】`,
					GameConfig.MAP_LANDMARKS.MAIN_WALL.x,
					GameConfig.GROUND_Y + 80
				);
			});
		} else if (landmark === 'EAST_GATE') {
			if (optionIndex === 1) {
				if (gs.eastGateLevel >= GameConfig.EAST_GATE_MAX_LEVEL) {
					hud.showToast('东门瓮城已达最高坚固等级！', 2.0);
					return;
				}
				const cost = GameConfig.EAST_GATE_UPGRADE_BASE_COST * gs.eastGateLevel;
				if (gs.hasProject('EAST_GATE_UPGRADE')) {
					hud.showToast('东门瓮城正在加固中。', 2.0);
					return;
				}
				const gateSeconds =
					GameConfig.CONSTRUCTION_SECONDS.EAST_GATE_UPGRADE * (1 + 0.15 * (gs.eastGateLevel - 1));
				throwSilver('GATE:EAST', GameConfig.MAP_LANDMARKS.EAST_GATE.x, cost, '东门加固', () =>
					beginProject(
						'EAST_GATE_UPGRADE',
						`东门 Lv.${gs.eastGateLevel + 1}`,
						GameConfig.MAP_LANDMARKS.EAST_GATE.x,
						gateSeconds,
						gs.eastGateLevel + 1
					)
				);
				return;
			}

			if (gs.eastGateHp <= 0) {
				hud.showToast('东门已毁，需由筑城工匠修复后方可开关！', 2.0);
				return;
			}
			gs.eastGateOpen = !gs.eastGateOpen;
			soundSfx('gate_open');
			pulseNode(gateArtNode, 0.06, 0.32);
			playFx(worldLayer, 'fx_arrow_hit', GameConfig.MAP_LANDMARKS.EAST_GATE.x, GameConfig.GROUND_Y + 42, 0.35, 0.55, 16);
			hud.showToast(gs.eastGateOpen ? '东门已开启，族丁可出城拾荒。' : '东门已关闭，瓮城严阵以待！', 2.0);
			refreshEnvironmentVisuals();
		} else if (landmark === 'WEST_SALT_FLAT' || landmark === 'EAST_SALT_FLAT') {
			const lmX = GameConfig.MAP_LANDMARKS[landmark].x;
			if (optionIndex === 1) {
				startReclaim(landmark, lmX);
				return;
			}
			const saltTower = towers.find((t) =>
				landmark === 'WEST_SALT_FLAT' ? t.state.id === 'WEST_SALT_TOWER' : t.state.id === 'EAST_SALT_TOWER'
			);
			if (saltTower !== undefined && !saltTower.state.unlocked) {
				if (gs.hasProject('TOWER_UNLOCK', saltTower.state.id)) {
					hud.showToast('盐田敌台正在施工中。', 2.0);
					return;
				}
				const cost = 220;
				throwSilver(`TOWER:${saltTower.state.id}`, saltTower.state.x, cost, '盐田敌台营建', () =>
					beginProject(
						'TOWER_UNLOCK',
						'盐田敌台',
						saltTower.state.x,
						GameConfig.CONSTRUCTION_SECONDS.TOWER_UNLOCK,
						1,
						saltTower.state.id
					)
				);
				return;
			}
			let saltCount = 0;
			for (const v of villagers) {
				if (!v.dead && v.role === 'SALT_WORKER') saltCount++;
			}
			hud.showToast(
				`灶户 ${saltCount} 名往来盐田背盐（每趟 ${GameConfig.SALT_FETCH.tripSilver} 银，田越熟出盐越多），天黑前务必召回！`,
				3.0
			);
		} else if (landmark === 'EAST_COAST' || landmark === 'WEST_COAST') {
			hud.showToast('滩头：倭寇由此东西两面登岸，天亮后便会涌入城外。', 2.6);
		}
	};

	const hud = new HudLayer({
		onSkipDay: () => {
			if (!waitingVictoryModal && gs.phase === 'DAY') {
				startNightPhase();
			}
		},
		onInteract: (optionIndex) => handleInteract(optionIndex),
		onLightAttack: () => lightAttack(),
		onQilinStep: () => {
			if (waitingVictoryModal) return;
			const fromX = player.x;
			const res = player.triggerQilinStep(enemies);
			if (res.triggered) {
				addFloatingText('王家拳·麒麟步！', player.x, GameConfig.GROUND_Y + 108, 0xfff6ad55);
				qilinAttack(fromX);
			}
		},
		onRally: () => {
			if (waitingVictoryModal) return;
			const res = player.triggerRally(villagers);
			if (res.triggered) {
				hud.showToast(`鸣鼓集结！已召回/集结 ${res.recalledCount} 名族丁。`, 2.0);
			}
		},
		onBribe: () => bribeNearestEnemy(),
		onVictoryModalConfirm: () => {
			waitingVictoryModal = false;
			gs.day++;
			gs.phase = 'DAY';
			gs.dayTimer = GameConfig.DAY_DURATION;
			gs.duskWarned = false;
			spawnDailyScavenges();
			refreshEnvironmentVisuals();
			soundBgm('day');
		},
	});
	scene.addChild(hud.node);
	refreshEnvironmentVisuals();
	soundBgm('day');

	// 窗口尺寸变化时重排 HUD 与背景（不重建场景，避免丢失游戏进度）
	SceneManager.setRelayout(() => {
		worldLayer.anchor = Vec2(0, 0);
		worldLayer.size = Size(GameConfig.MAP_WIDTH, Screen.height);
		hud.relayout();
		refreshEnvironmentVisuals();
	});

	// 主循环 update 调度
	scene.schedule((dt: number) => {
		// 全局节奏：把 dt 整体乘上 GAME_SPEED，移动 / 攻速 / 工期 / 招募 /
		// 日夜循环 / 动画会一起放慢，手感一致。
		const clampedDt = Math.min(dt, 0.05) * GameConfig.GAME_SPEED;
		tickFx(clampedDt);
		tickWater(clampedDt);
		// 城门铁闸：帧级缓动升降（闸门作为独立杆件滑进气槽，不再换图不硬跳）
		tickGate(dt);

		if (waitingVictoryModal) {
			const boss = findBoss(enemies);
			hud.update(
				clampedDt,
				player.findNearestLandmark(),
				enemies.length,
				boss !== undefined ? boss.hp : 0,
				boss !== undefined ? boss.maxHp : 0,
				boss !== undefined ? GameConfig.ENEMIES.BOSS.name : ''
			);
			return false;
		}

		// 1. 玩家输入与移动
		let moveInput = 0;
		if (Keyboard.isKeyPressed(KeyName.A) || Keyboard.isKeyPressed(KeyName.Left)) moveInput -= 1;
		if (Keyboard.isKeyPressed(KeyName.D) || Keyboard.isKeyPressed(KeyName.Right)) moveInput += 1;

		if (Keyboard.isKeyDown(KeyName.E)) handleInteract(0);
		// 普通攻击：空格或 L（按下即出，不等释放），快节奏连段
		if (Keyboard.isKeyPressed(KeyName.Space) || Keyboard.isKeyPressed(KeyName.L)) lightAttack();
		if (Keyboard.isKeyDown(KeyName.J)) {
			const fromX = player.x;
			const res = player.triggerQilinStep(enemies);
			if (res.triggered) {
				addFloatingText('王家拳·麒麟步！', player.x, GameConfig.GROUND_Y + 108, 0xfff6ad55);
				qilinAttack(fromX);
			}
		}
		if (Keyboard.isKeyDown(KeyName.K)) {
			const res = player.triggerRally(villagers);
			if (res.triggered) {
				hud.showToast(`鸣鼓集结！已召回/集结 ${res.recalledCount} 名族丁。`, 2.0);
			}
		}
		if (Keyboard.isKeyDown(KeyName.F)) bribeNearestEnemy();

		const nearestLandmark = player.update(clampedDt, moveInput);
		// 主角脚下标记：镜头拉近、人一多，一眼就能认出王叔杲
		playerMarkDraw.clear();
		// 主角脚下不再画黄色光圈/横线：不再用标记圈人，靠美术和镜头认主角
		for (const t of towers) t.setNearby(Math.abs(t.state.x - player.x) < 300);

		// 探路：只有主角王叔杲亲自走到未探明地界才算「探明」（族丁不算，但他们仍能从雾里被看见）
		revealFogAround([player.x]);

		// 2. 摄像机平滑跟随 + 三层视差滚动（按可视区域宽度动态限幅）
		const halfView = Screen.width / 2;
		const targetCamX = Math.max(
			halfView,
			Math.min(GameConfig.MAP_WIDTH - halfView, player.x)
		);
		cameraX += (targetCamX - cameraX) * Math.min(1, clampedDt * 8);
		const scroll = GameConfig.SCREEN_WIDTH / 2 - cameraX;
		const offset = Screen.offsetX + scroll;
		worldLayer.x = offset;
		midLayer.x = Screen.offsetX + scroll * 0.55;
		farLayer.x = Screen.offsetX + scroll * 0.25;

		// 3. 日夜状态机与波次刷怪
		if (gs.phase === 'DAY') {
			gs.dayTimer -= clampedDt;
			if (!gs.duskWarned && gs.dayTimer <= GameConfig.DUSK_WARNING_TIME) {
				gs.duskWarned = true;
				hud.showToast(GameConfig.HISTORICAL_QUOTES.DUSK_WARNING, 4.0);
			}
			if (gs.dayTimer <= 0) {
				startNightPhase();
			}
		} else {
			nightElapsed += clampedDt;
			const remainingQueue: PendingSpawn[] = [];
			for (const item of spawnQueue) {
				if (nightElapsed >= item.triggerTime) {
					const enemy = new Enemy(
						item.enemyType,
						item.side === 'E' ? GameConfig.SPAWN_EAST_X : GameConfig.SPAWN_WEST_X,
						item.side
					);
					enemies.push(enemy);
					worldLayer.addChild(enemy.node);
				} else {
					remainingQueue.push(item);
				}
			}
			spawnQueue = remainingQueue;

			// 夜晚作战粮草消耗
			foodConsumeTimer += clampedDt;
			if (foodConsumeTimer >= GameConfig.FOOD_CONSUME_INTERVAL) {
				foodConsumeTimer -= GameConfig.FOOD_CONSUME_INTERVAL;
				const combatCount =
					gs.getRoleCount('MILITIA') + gs.getRoleCount('KUNG_FU');
				if (combatCount > 0) {
					const wasLow = gs.isLowFood;
					gs.consumeFood(combatCount * GameConfig.FOOD_CONSUME_PER_COMBAT_UNIT);
					if (!wasLow && gs.isLowFood) {
						hud.showToast(GameConfig.HISTORICAL_QUOTES.LOW_FOOD_WARNING, 3.5);
					}
				}
			}
		}

		// 4. 城外散落物资拾取检测
		for (const item of scavenges) {
			if (item.collected) continue;
			let pickerX: number | undefined = undefined;
			if (Math.abs(player.x - item.x) <= 42) {
				pickerX = player.x;
			} else {
				for (const v of villagers) {
					if (!v.dead && Math.abs(v.x - item.x) <= 36) {
						pickerX = v.x;
						break;
					}
				}
			}
			if (pickerX !== undefined) {
				item.collected = true;
				item.node.removeFromParent();
				if (item.kind === 'SALT') {
					gs.addSilver(GameConfig.SCAVENGE_SALT_SILVER);
					addFloatingText(`+${GameConfig.SCAVENGE_SALT_SILVER} 白银`, item.x, GameConfig.GROUND_Y + 60);
				} else {
					if (gs.eastGateHp < gs.eastGateMaxHp) {
						gs.eastGateHp = Math.min(gs.eastGateMaxHp, gs.eastGateHp + GameConfig.SCAVENGE_WOOD_REPAIR);
					} else {
						gs.ancestralHallHp = Math.min(gs.ancestralHallMaxHp, gs.ancestralHallHp + GameConfig.SCAVENGE_WOOD_REPAIR);
					}
					addFloatingText(`+${GameConfig.SCAVENGE_WOOD_REPAIR} 修复`, item.x, GameConfig.GROUND_Y + 60, 0xff68d391);
				}
			}
		}

		// 4.5 营建工程：先按在场工匠数推进工期，再结算完工
		for (const p of gs.projects) p.workers = 0;
		for (const v of villagers) {
			if (v.dead || v.role !== 'BUILDER') continue;
			let best: BuildProject | undefined = undefined;
			let bestDist = GameConfig.BUILD_SITE_RADIUS;
			for (const p of gs.projects) {
				const d = Math.abs(p.x - v.x);
				if (d <= bestDist) {
					bestDist = d;
					best = p;
				}
			}
			if (best !== undefined) best.workers++;
		}
		const finishedProjects = gs.tickProjects(clampedDt);
		for (const p of finishedProjects) completeProject(p);
		syncProjectViews(clampedDt);

		// 5. 更新所有实体
		for (const v of villagers) {
			v.update(clampedDt, {
				phase: gs.phase,
				dayTimer: gs.dayTimer,
				enemies,
				tools,
				projects: gs.projects,
				playerInAura: (vx) => player.isInAura(vx),
				onProduceResource: (kind, amount, vx) => {
					addFloatingText(
						kind === 'FOOD' ? `+${amount} 粮` : `+${amount} 银`,
						vx,
						GameConfig.GROUND_Y + 72,
						kind === 'FOOD' ? 0xff68d391 : 0xfff6e05e
					);
					if (kind === 'SILVER' && amount >= GameConfig.SALT_FETCH.tripSilver) {
						addFloatingText(
							GameConfig.HISTORICAL_QUOTES.SALT_HAUL_ARRIVED,
							vx,
							GameConfig.GROUND_Y + 96,
							0xffe2e8f0
						);
					}
				},
				onRepairBuilding: (amount, vx) => {
					addFloatingText(`+${amount} 修筑`, vx, GameConfig.GROUND_Y + 72, 0xff63b3ed);
				},
				onSaltGathered: (vx) => {
					addFloatingText('装满盐担', vx, GameConfig.GROUND_Y + 72, 0xffe2e8f0);
					playFx(worldLayer, 'fx_recruit', vx, GameConfig.GROUND_Y + 46, 0.3, 0.3, 6);
				},
				onCargoDropped: (vx) => {
					spawnScavenge(vx, 'SALT');
					addFloatingText('弃担逃命！', vx, GameConfig.GROUND_Y + 72, 0xfffc8181);
				},
			});
		}

		// 5.2 招募读秒：到岗即生成族丁
		const arrivedRecruits = gs.tickRecruits(clampedDt);
		for (let i = 0; i < arrivedRecruits; i++) {
			soundSfx('recruit');
			spawnVillager(GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x + 30, 'IDLE');
			addFloatingText(
				'+1 族丁',
				GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x,
				GameConfig.GROUND_Y + 120,
				0xff9ae6b4
			);
		}

		// 5.3 民居添丁：住房与粮食都有余裕时，民居自己慢慢走出人来（比交银招募慢得多）
		const bornFromHouses = gs.tickHouses(clampedDt);
		for (const born of bornFromHouses) {
			soundSfx('recruit');
			spawnVillager(born.x, 'IDLE');
			addFloatingText('+1 族丁', born.x, GameConfig.GROUND_Y + 110, 0xff9ae6b4);
		}

		// 清理阵亡族丁并同步快照（背着盐被杀 → 盐担失落城外）
		for (let i = villagers.length - 1; i >= 0; i--) {
			const v = villagers[i];
			if (!v.dead) continue;
			if (v.carrying) {
				spawnScavenge(v.x, 'SALT');
				addFloatingText(
					GameConfig.HISTORICAL_QUOTES.SALT_HAUL_LOST,
					v.x,
					GameConfig.GROUND_Y + 80,
					0xfffc8181
				);
			}
			villagers.splice(i, 1);
		}
		gs.villagers = villagers.map((v) => ({
			id: v.id,
			role: v.role,
			hp: v.hp,
			maxHp: v.maxHp,
			x: v.x,
		}));

		for (const t of towers) {
			t.update(clampedDt, enemies);
		}

		for (const e of enemies) {
			e.update(clampedDt, villagers);
		}
		for (let i = enemies.length - 1; i >= 0; i--) {
			if (enemies[i].escaped || (enemies[i].dead && enemies[i].dying === 0)) enemies.splice(i, 1);
		}

		// 6.2 投银抛物线：银袋飞完落地，化一小簇银光
		for (let i = silverThrows.length - 1; i >= 0; i--) {
			const bag = silverThrows[i];
			bag.t += clampedDt / GameConfig.THROW_SECONDS;
			if (bag.t >= 1) {
				playFx(worldLayer, 'fx_levelup', bag.x1, GameConfig.GROUND_Y + 38, 0.26, 0.2, 6);
				bag.node.removeFromParent();
				silverThrows.splice(i, 1);
				continue;
			}
			bag.node.x = bag.x0 + (bag.x1 - bag.x0) * bag.t;
			bag.node.y =
				bag.y0 + (bag.y1 - bag.y0) * bag.t + Math.sin(bag.t * Math.PI) * 44;
		}

		// 6.3 钱袋飘银：银钱从钱袋往上飘，飘完化掉
		for (let i = silverRises.length - 1; i >= 0; i--) {
			const rise = silverRises[i];
			rise.t += clampedDt / 0.7;
			const k = Math.min(1, rise.t);
			const ease = 1 - (1 - k) * (1 - k);
			rise.node.y = GameConfig.GROUND_Y + 38 + ease * 58;
			rise.node.opacity = 1 - ease;
			rise.node.scaleX = 1 + ease * 0.35;
			if (k >= 1) {
				rise.node.removeFromParent();
				silverRises.splice(i, 1);
			}
		}

		// 6. 更新飘字
		for (let i = floatingTexts.length - 1; i >= 0; i--) {
			const ft = floatingTexts[i];
			ft.timer -= clampedDt;
			ft.label.y += 28 * clampedDt;
			if (ft.timer <= 0) {
				ft.label.removeFromParent();
				floatingTexts.splice(i, 1);
			}
		}

		// 7. 胜负判定
		if (gs.ancestralHallHp <= 0) {
			gs.isVictory = false;
			SceneManager.start('GAMEOVER');
			return true;
		}

		if (gs.phase === 'NIGHT' && spawnQueue.length === 0 && enemies.length === 0) {
			const wave = GameConfig.NIGHT_WAVES[gs.day - 1];
			gs.wavesCleared++;
			soundSfx('drum_rally');
			gs.addSilver(wave.rewardSilver);

			if (gs.day >= GameConfig.TOTAL_NIGHTS) {
				gs.isVictory = true;
				SceneManager.start('GAMEOVER');
				return true;
			}

			waitingVictoryModal = true;
			hud.showVictoryModal(wave);
		}

		// 6.5 城外未归人数：黄昏看东门之外，入夜看内城水门之外
		let stragglers = 0;
		const safeLineX =
			gs.phase === 'NIGHT'
				? GameConfig.MAP_LANDMARKS.INNER_GATE.x
				: GameConfig.MAP_LANDMARKS.EAST_GATE.x;
		for (const v of villagers) {
			if (!v.dead && v.x > safeLineX) stragglers++;
		}
		if (
			gs.phase === 'DAY' &&
			gs.dayTimer <= GameConfig.DUSK_RETURN_SECONDS &&
			stragglers > 0 &&
			curfewWarnedDay !== gs.day
		) {
			curfewWarnedDay = gs.day;
			hud.showToast(GameConfig.HISTORICAL_QUOTES.CURFEW_WARNING, 3.4);
		}

		if (DEBUG_SEED && !probeSeeded) {
			probeSeeded = true;
			gs.silver = 5000;
			gs.food = 5000;
			// 两名背着盐的灶户被丢在远滩涂，天色马上转黄昏
			spawnVillager(4300, 'SALT_WORKER');
			spawnVillager(4520, 'SALT_WORKER');
			for (const v of villagers) {
				if (v.role === 'SALT_WORKER') {
					v.carrying = true;
					v.refreshVisual();
				}
			}
			spawnVillager(GameConfig.MAP_LANDMARKS.INNER_GATE.x, 'BUILDER');
			gs.dayTimer = 8;
		}
		probeTimer -= clampedDt;
		if (DEBUG_PROBE && probeTimer <= 0) {
			probeTimer = 1.0;
			const sw = villagers
				.filter((v) => v.role === 'SALT_WORKER')
				.map((v) => `${Math.round(v.x)}${v.carrying ? 'c' : ''}`);
			const bd = villagers.filter((v) => v.role === 'BUILDER').length;
			print(
				`PROBE d=${gs.day} ph=${gs.phase} t=${gs.dayTimer.toFixed(1)} pop=${gs.populationCount} sw=[${sw.join(
					','
				)}] builders=${bd} proj=${gs.projects.length} rec=${gs.recruits.length} straggle=${stragglers} enemy=${enemies.length} salv=${scavenges.length} hall=${gs.ancestralHallLevel} mor=${Math.round(
					gs.moraleBonus * 100
				)}/${Math.round(gs.moraleHpBonus * 100)} hpop=${gs.housingCapacity}/${gs.foodCapacity} houseLv=[${gs.houses
					.map((h) => h.level)
					.join(',')}] don=${donationSummary()}`
			);
		}

		const nightBoss = findBoss(enemies);
		hud.update(
			clampedDt,
			nearestLandmark,
			enemies.length,
			nightBoss !== undefined ? nightBoss.hp : 0,
			nightBoss !== undefined ? nightBoss.maxHp : 0,
			nightBoss !== undefined ? GameConfig.ENEMIES.BOSS.name : '',
			{
				projects: gs.projects.map((p) => ({
					label: p.label,
					pct: 1 - p.remain / Math.max(0.001, p.total),
					workers: p.workers,
				})),
				recruitRemain: gs.recruits.length > 0 ? gs.recruits[0].remain : 0,
				stragglers,
				housing: gs.housingCapacity,
				emptyLots: gs.houses.filter((h) => h.level <= 0).length,
				houseSpawn: gs.freeSlots > 0 ? gs.houseSpawnProgress : 0,
				donation: donationSummary(),
			}
		);
		return false;
	});

	return scene;
}
