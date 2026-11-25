import { Color, DrawNode, KeyName, Keyboard, Label, Node, Size, Sprite, Vec2 } from 'Dora';
import { SceneManager } from 'src/scenes/SceneManager';
import { EnemyType, GameConfig, LandmarkId, ProjectKind, VillagerRole } from 'src/config/GameConfig';
import { Screen } from 'src/config/Screen';
import { artAt, artCover, artCoverSize, artInto, artStretch } from 'src/config/Assets';
import { GameState, BuildProject } from 'src/config/GameState';
import { DefenseTower } from 'src/entities/DefenseTower';
import { Enemy } from 'src/entities/Enemy';
import { Player } from 'src/entities/Player';
import { ToolDrop, Villager } from 'src/entities/Villager';
import { HudLayer } from 'src/ui/HudLayer';
import { playFx, tickFx } from 'src/ui/Fx';
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

	// 远景：大罗山与海天轮廓
	const farDraw = DrawNode();
	drawRect(farDraw, 0, GameConfig.GROUND_Y, 2400, 120, 0x332d3748);
	farDraw.drawPolygon(
		[
			Vec2(0, GameConfig.GROUND_Y),
			Vec2(180, 480),
			Vec2(420, 290),
			Vec2(700, 420),
			Vec2(1050, 240),
			Vec2(1050, GameConfig.GROUND_Y),
		],
		Color(0xff2c3e50)
	);
	farLayer.addChild(farDraw);

	// 远景剪影贴图：横向平铺，隔块镜像以缓解重复感
	if (artAt(farLayer, 'horizon', 0, GameConfig.GROUND_Y) !== undefined) {
		farDraw.clear();
		for (let i = 1; i < 5; i++) {
			const flip = i % 2 === 1;
			const tile = artAt(farLayer, 'horizon', i * 1280 + (flip ? 1280 : 0), GameConfig.GROUND_Y);
			if (tile !== undefined && flip) tile.scaleX = -1;
		}
	}

	// 中景：堡内河浃、屋舍远影
	const midDraw = DrawNode();
	for (let x = 220; x < 2400; x += 240) {
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
	const groundDraw = DrawNode();
	drawRect(groundDraw, 0, 0, GameConfig.MAP_WIDTH, GameConfig.GROUND_Y, 0xff3b3026);
	// 堡内石板路 (0 ~ 2560) 与城外滩涂 / 盐田 (2560 ~ 海)
	const cityGroundW = 2560;
	const seaStart = GameConfig.MAP_LANDMARKS.COAST_SPAWN.x - 260;
	drawRect(groundDraw, 0, GameConfig.GROUND_Y - 14, cityGroundW, 14, 0xff718096);
	drawRect(groundDraw, cityGroundW, GameConfig.GROUND_Y - 14, seaStart - cityGroundW, 14, 0xffb79f78);
	drawRect(groundDraw, seaStart, 0, GameConfig.MAP_WIDTH - seaStart, GameConfig.GROUND_Y, 0xff1e4e79);
	worldLayer.addChild(groundDraw);

	// 地面 / 滩涂贴图：横向平铺（有素材时盖住程序化地面）
	const groundArtNode = Node();
	worldLayer.addChild(groundArtNode);
	if (artAt(groundArtNode, 'ground_city', 0, 0) !== undefined) {
		for (let i = 1; i * 640 < cityGroundW; i++) artAt(groundArtNode, 'ground_city', i * 640, 0);
		for (let x = cityGroundW; x < GameConfig.MAP_WIDTH; x += 640) {
			artAt(groundArtNode, 'ground_beach', x, 0);
		}
		groundDraw.clear();
		// 最右侧海面
		const seaDraw = DrawNode();
		drawRect(seaDraw, seaStart, 0, GameConfig.MAP_WIDTH - seaStart, GameConfig.GROUND_Y, 0xff1e4e79);
		worldLayer.addChild(seaDraw);
	}

	// 绘制静态地标（宗祠、水田、盐课司、主城墙、海滨）
	const landmarkDraw = DrawNode();
	worldLayer.addChild(landmarkDraw);
	const landmarkIds = Object.keys(GameConfig.MAP_LANDMARKS) as LandmarkId[];
	for (const id of landmarkIds) {
		const lm = GameConfig.MAP_LANDMARKS[id];
		if (id !== 'EAST_GATE' && id !== 'INNER_GATE' && id !== 'ANCESTRAL_HALL') {
			// 有美术素材就摆精灵，否则退回方块
			if (artAt(worldLayer, `lm_${id}`, lm.x, GameConfig.GROUND_Y) === undefined) {
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
		const lbl = Label('sarasa-mono-sc-regular', 15) as Label.Type;
		lbl.text = `${lm.name}\n(${lm.subtitle})`;
		lbl.x = lm.x;
		lbl.y = GameConfig.GROUND_Y + lm.height + 26;
		lbl.color = Color(0xfffefcbf);
		worldLayer.addChild(lbl);
	}

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
			if (artInto(node, artId) !== undefined) continue; // 有贴图就不用画色块
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
	const gateArtNode = Node(); // 东门：闭门 / 开门 / 破损
	const innerGateArtNode = Node(); // 内城水门：完好 / 破损
	const shrineArtNode = Node(); // 王氏宗祠：1 级 / 2 级
	worldLayer.addChild(innerGateArtNode);
	worldLayer.addChild(gateArtNode);
	worldLayer.addChild(shrineArtNode);

	// 夜间火把光点
	const torchDraw = DrawNode();
	worldLayer.addChild(torchDraw);

	// 火把光晕贴图挂点
	const torchArtNode = Node();
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
	spawnVillager(360, 'IDLE');
	spawnVillager(410, 'IDLE');
	spawnVillager(455, 'IDLE');

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
			const torchXs = [460, 860, 1260, 1660, 2060, 2420, 3300];
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
		const hallArtId = gs.ancestralHallLevel >= 2 ? 'lm_ANCESTRAL_HALL_lv2' : 'lm_ANCESTRAL_HALL';
		if (artInto(shrineArtNode, hallArtId) === undefined) {
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
			if (artInto(innerGateArtNode, 'lm_INNER_GATE') === undefined) {
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
		} else if (artInto(innerGateArtNode, 'lm_INNER_GATE_broken') === undefined) {
			drawRect(
				gatesDraw,
				innerLm.x - innerLm.width / 2,
				GameConfig.GROUND_Y,
				innerLm.width,
				32,
				0xff2d3748
			);
		}

		// 东门瓮城（开 / 闭 / 破损三态）
		const eastLm = GameConfig.MAP_LANDMARKS.EAST_GATE;
		if (gs.eastGateHp <= 0) {
			gateArtNode.x = eastLm.x;
			gateArtNode.y = GameConfig.GROUND_Y;
			if (artInto(gateArtNode, 'lm_EAST_GATE_broken') === undefined) {
				drawRect(
					gatesDraw,
					eastLm.x - eastLm.width / 2,
					GameConfig.GROUND_Y,
					eastLm.width,
					36,
					0xff2d3748
				);
			}
		} else if (gs.eastGateOpen) {
			// 开启状态：仅上方门楼，下方通行
			gateArtNode.x = eastLm.x;
			gateArtNode.y = GameConfig.GROUND_Y + 90;
			if (artInto(gateArtNode, 'lm_EAST_GATE_open') === undefined) {
				drawRect(
					gatesDraw,
					eastLm.x - eastLm.width / 2,
					GameConfig.GROUND_Y + 90,
					eastLm.width,
					eastLm.height - 90,
					eastLm.color,
					0xff68d391
				);
			}
		} else {
			// 关闭状态：全封闭瓮城铁门
			gateArtNode.x = eastLm.x;
			gateArtNode.y = GameConfig.GROUND_Y;
			if (artInto(gateArtNode, 'lm_EAST_GATE') === undefined) {
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
		for (const g of wave.groups) {
			for (let i = 0; i < g.count; i++) {
				spawnQueue.push({
					enemyType: g.enemyType,
					triggerTime: g.delay + i * g.interval,
				});
			}
		}
		refreshEnvironmentVisuals();
	};

	// 银袋抛物线：投银时飞向升级点（程序化小方块，无美术也看得见）
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
		const d = DrawNode();
		drawRect(d, -8, -8, 16, 16, 0xfff6e05e, 0xff744210);
		n.addChild(d);
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
	const throwSilver = (
		purpose: string,
		targetX: number,
		cost: number,
		label: string,
		onFull: () => void
	) => {
		rememberDonation(purpose, label, cost);
		const bag = GameConfig.SILVER_BAG;
		if (gs.silver < bag) {
			hud.showToast(`白银不足，投一袋需 ${bag} 两（现有 ${gs.silver} 两）。`, 2.0);
			return;
		}
		gs.spendSilver(bag);
		spawnSilverThrow(player.x + player.facing * 18, targetX);
		const total = gs.addDonation(purpose, bag);
		if (total >= cost) {
			gs.clearDonation(purpose);
			onFull();
			return;
		}
		hud.showToast(`【${label}】已投 ${total}/${cost} 两，继续投银。`, 1.6);
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
			hud.showToast(`买命需 ${cost} 两白银，库中不足！`, 1.8);
			return;
		}
		gs.spendSilver(cost);
		spawnSilverThrow(player.x + player.facing * 18, target.x);
		target.bribe();
		if (target.type === 'BOSS') {
			hud.showToast(`塞了 ${cost} 两给倭酋，只撂得他踉跄一阵！`, 2.4);
		} else {
			hud.showToast(`付 ${cost} 两买命，倭寇收银退兵。`, 2.0);
		}
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
			hud.showToast('请靠近宗祠、民居、水田、盐课司、内城水门、主城墙或东门后再交互', 2.0);
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
		} else if (landmark === 'PADDY_FIELD') {
			const cost = GameConfig.ROLES.FARMER.toolCost;
			throwSilver('TOOL:FARMER', GameConfig.MAP_LANDMARKS.PADDY_FIELD.x, cost, '置办锄头', () => {
				spawnTool(GameConfig.MAP_LANDMARKS.PADDY_FIELD.x, 'FARMER');
				addFloatingText('置办【锄头】', GameConfig.MAP_LANDMARKS.PADDY_FIELD.x, GameConfig.GROUND_Y + 80);
			});
		} else if (landmark === 'SALT_OFFICE') {
			const cost = GameConfig.ROLES.SALT_WORKER.toolCost;
			throwSilver('TOOL:SALT_WORKER', GameConfig.MAP_LANDMARKS.SALT_OFFICE.x, cost, '置办盐铲', () => {
				spawnTool(GameConfig.MAP_LANDMARKS.SALT_OFFICE.x, 'SALT_WORKER');
				addFloatingText('置办【盐铲】', GameConfig.MAP_LANDMARKS.SALT_OFFICE.x, GameConfig.GROUND_Y + 80);
			});
		} else if (landmark === 'INNER_GATE') {
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
			hud.showToast(gs.eastGateOpen ? '东门已开启，族丁可出城拾荒。' : '东门已关闭，瓮城严阵以待！', 2.0);
			refreshEnvironmentVisuals();
		} else if (landmark === 'OUTER_SALT_FLAT') {
			if (optionIndex === 1) {
				const saltTower = towers.find((t) => t.state.id === 'SALT_TOWER');
				if (!saltTower) return;
				if (gs.hasProject('TOWER_UNLOCK', 'SALT_TOWER')) {
					hud.showToast('盐田敌台正在施工中。', 2.0);
					return;
				}
				const cost = 220;
				throwSilver('TOWER:SALT_TOWER', saltTower.state.x, cost, '盐田敌台营建', () =>
					beginProject(
						'TOWER_UNLOCK',
						'盐田敌台',
						saltTower.state.x,
						GameConfig.CONSTRUCTION_SECONDS.TOWER_UNLOCK,
						1,
						'SALT_TOWER'
					)
				);
				return;
			}
			let saltCount = 0;
			for (const v of villagers) {
				if (!v.dead && v.role === 'SALT_WORKER') saltCount++;
			}
			hud.showToast(
				`灶户 ${saltCount} 名往来盐田背盐（每趟 ${GameConfig.SALT_FETCH.tripSilver} 银），天黑前务必召回！`,
				3.0
			);
		} else if (landmark === 'COAST_SPAWN') {
			hud.showToast('东海前哨：倭寇由此登岸，天亮后便会涌入城外。', 2.6);
		}
	};

	const hud = new HudLayer({
		onSkipDay: () => {
			if (!waitingVictoryModal && gs.phase === 'DAY') {
				startNightPhase();
			}
		},
		onInteract: (optionIndex) => handleInteract(optionIndex),
		onQilinStep: () => {
			if (waitingVictoryModal) return;
			const res = player.triggerQilinStep(enemies);
			if (res.triggered) {
				addFloatingText('王家拳·麒麟步！', player.x, GameConfig.GROUND_Y + 108, 0xfff6ad55);
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
		if (Keyboard.isKeyDown(KeyName.J)) {
			const res = player.triggerQilinStep(enemies);
			if (res.triggered) {
				addFloatingText('王家拳·麒麟步！', player.x, GameConfig.GROUND_Y + 108, 0xfff6ad55);
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
					const enemy = new Enemy(item.enemyType, GameConfig.SPAWN_X);
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
