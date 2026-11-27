/**
 * 《永昌堡：铁血筑城》全局配置
 * 包含地图坐标、地标定义、职业属性、敌人属性、8夜波次表与历史文案
 */

export type VillagerRole =
	| 'IDLE'
	| 'FARMER'
	| 'SALT_WORKER'
	| 'BUILDER'
	| 'MILITIA'
	| 'KUNG_FU';

export type EnemyType = 'SCOUT' | 'SAMURAI' | 'BOSS';

export type TowerType = 'ARROW' | 'CANNON';

/** 营建/升级工程类型（读秒施工，见 CONSTRUCTION_SECONDS） */
export type ProjectKind =
	| 'HALL_UPGRADE'
	| 'EAST_GATE_UPGRADE'
	| 'INNER_GATE_UPGRADE'
	| 'TOWER_UNLOCK'
	| 'TOWER_UPGRADE'
	| 'HOUSE_UPGRADE'
	| 'LAND_RECLAIM';

export type LandmarkId =
	| 'WEST_COAST'
	| 'WEST_SALT_FLAT'
	| 'WEST_PADDY'
	| 'INNER_GATE'
	| 'ANCESTRAL_HALL'
	| 'SALT_OFFICE'
	| 'MAIN_WALL'
	| 'EAST_GATE'
	| 'EAST_PADDY'
	| 'EAST_SALT_FLAT'
	| 'EAST_COAST'
	// 两头的倭寇码头：建起来才有鬼子上岸，被拆了就只来散兵
	| 'WEST_PIER'
	| 'EAST_PIER';

export interface LandmarkConfig {
	id: LandmarkId;
	name: string;
	subtitle: string;
	x: number;
	width: number;
	height: number;
	color: number; // ARGB 0xAARRGGBB
	description: string;
	interactHint: string;
	/** 可开垦地块：水田（产粮）或盐田（产银）；不填即为普通建筑地标 */
	reclaimable?: 'PADDY' | 'SALT';
}

export interface FogZoneConfig {
	id: string;
	name: string;
	/** 迷雾区中心世界坐标 */
	x: number;	/** 迷雾区宽度 */
	width: number;
	/** 开局是否已亮（城堡核心区是亮的） */
	startRevealed?: boolean;
}

/** 两头倭寇码头（被打塔 → 那一侧只剩散兵） */
export interface PierConfig {
	MAX_HP: number;
	OFFSET_WEST: number;
	OFFSET_EAST: number;
	SABOTAGE_DAMAGE: number;
	REPAIR_AMOUNT: number;
	LANDING_BONUS_COUNT: number;
	BROKEN_SIDE_RATIO: number;
	REVENGE_DELAY_SECONDS: number;
	REVENGE_COUNT: number;
	/** 对码头出拳/麒麟步的伤害与判定范围 */
	HIT_DAMAGE: number;
	HIT_BOX_HALF: number;
	HIT_REACH: number;
	// 旧字段（保留兼容）：语义同 SABOTAGE_DAMAGE / REPAIR_AMOUNT，
	// REPAIR_SILVER 是主角修栈桥一次要花的银两。
	HIT_HP: number;
	REPAIR_HP: number;
	REPAIR_SILVER: number;
	SQUAD_PER_FULL_PIER: number;
}

export interface RoleConfig {
	role: VillagerRole;
	name: string;
	toolName: string;
	toolCost: number;
	color: number;
	maxHp: number;
	moveSpeed: number;
	attackDamage: number;
	attackRange: number;
	attackInterval: number;
	produceInterval: number;
	produceAmount: number;
	repairPerSec: number;
	description: string;
}

export interface EnemyConfig {
	type: EnemyType;
	name: string;
	maxHp: number;
	moveSpeed: number;
	attackDamage: number;
	attackRange: number;
	attackInterval: number;
	rewardSilver: number;
	width: number;
	height: number;
	color: number;
}

export interface WaveSpawnGroup {
	enemyType: EnemyType;
	count: number;
	interval: number;
	delay: number;
	/** 登岸面：W 从西湾上岸（向右推进），E 从东海上岸（向左推进）；缺省按组序自动东西交替 */
	side?: 'W' | 'E';
}

export interface NightWaveConfig {
	night: number;
	title: string;
	historicalNote: string;
	victorySpeech: string;
	rewardSilver: number;
	groups: WaveSpawnGroup[];
}

export interface HistoryCodexEntry {
	title: string;
	period: string;
	content: string;
}

export const GameConfig = {
	// 视图与地图空间常量 (1D 逻辑，2D 卷轴)
	SCREEN_WIDTH: 1280,
	SCREEN_HEIGHT: 720,
	// 大地图：西海 — 西滩（盐田/水田）— 城堡（内城水门/宗祠/盐课司/主墙/东门）— 东滩（水田/盐田）— 东海
	// 左右两头都是倭寇上岸点，永昌堡夹在中间，四面受敌（参考《王国：新大陆》）。
	MAP_WIDTH: 7600,
	// 地平线（人物落脚线）。可视世界高度 = CAMERA_VIEW_HEIGHT / WORLD_ZOOM ≈ 416 单位，
	// 而这个值就是「地平线离屏幕底边的高度」：
	//   GROUND_Y / 416 = 地面（岸 + 城前水面）占屏比
	// 现在 104/416 ≈ 25%：岸 6% + 水 19%，上面 75% 全留给天和城。
	// 想再压地面就继续调小；地面要厚一点就调大（别超过 200，否则人会被挤到画面中间）。
	GROUND_Y: 104,
	// 地平线以下这一条不再是滩涂土块，而是城前的水面：
	// 上面的门楼、宗祠、民居会在水里留一道倒影。
	WATER: {
		// 岸带高度：地平线往下这一小条才是看得见的实地，再往下都被水面盖住。
		// 26 ≈ 屏幕高度的 6%（原来是 60/30，地上一直显得太厚）。
		SHORE_BAND: 26,
		// 倒影纵向压缩（真实水面倒影总被压扁）与透明度
		REFLECT_SQUASH: 0.72,
		REFLECT_OPACITY: 0.42,
		// 水色：贴地平线处亮、越靠画面底部越深
		COLOR_TOP: 0xff3c6f9c,
		COLOR_DEEP: 0xff0b1a2b,
		// 水面波纹条数（横贯可视区域，缓慢漂移）
		RIPPLE_COUNT: 11,
		// 水面碎光（一闪一闪的反光点）个数
		GLINT_COUNT: 34,
		// 整片水色的「呼吸」幅度：0.13 = 明暗±13%，抢眼但不把倒影洗掉
		SWELL: 0.13,
	},
	// ------- 镜头构图基准（设计单位）-------
	// 分辨率变化时锁死这两个数：超宽屏只会多看到两边，不会把画面挤成中间一条窄带。
	// 屏幕竖着看：地平线在 GROUND_Y（底往上 128），下面是水面（宽 31%），上面是城与天。
	CAMERA_VIEW_WIDTH: 960,
	CAMERA_VIEW_HEIGHT: 520,
	CAMERA_MIN_X: 480,
	CAMERA_MAX_X: 7120,
	SAFE_LINE_X: 2350,
	SPAWN_EAST_X: 7420,
	SPAWN_WEST_X: 260,
	/** 东岸到宗祠的路比西岸长；西岸贼兵按这个比例延后登岸（1 = 完全抵平路程差） */
	WEST_LANDING_DELAY_RATIO: 0.6,
	OUTER_ZONE_MIN_X: 600,
	OUTER_ZONE_MAX_X: 7100,

	// 初始资源与建筑参数
	INITIAL_SILVER: 13,
	INITIAL_FOOD: 120,
	INITIAL_MAX_POPULATION: 8,
	POPULATION_PER_HALL_LEVEL: 4,
	RECRUIT_VILLAGER_COST: 4,

	// ---- 民居（人口之源）----
	// 人口上限 = min(住房容量, 粮食能养活的人数)；人慢慢从民居自然添丁，或花银子招募
	HOUSE_SLOTS: [
		{ x: 2450, level: 1 },
		{ x: 2700, level: 1 },
		{ x: 3000, level: 1 },
		{ x: 3280, level: 1 },
	],
	HOUSE_MAX_LEVEL: 3,
	// 每级民居可住的族丁数（lv1=2, lv2=4, lv3=6）
	HOUSE_CAPACITY_PER_LEVEL: 2,
	HOUSE_BASE_HP: 400,
	// 民居升级：直接投银（一袋 2 两，可连投）
	HOUSE_BUILD_COST: 6,
	HOUSE_UPGRADE_COST_LV2: 8,
	HOUSE_UPGRADE_COST_LV3: 18,
	// 民居自然添丁：每间民居每过这么多秒添一名族丁（有空位且粮食够时）
	HOUSE_SPAWN_SECONDS: 22,
	// 每个族丁要占的口粮：粮食决定人口上限
	FOOD_PER_PERSON: 25,

	// ---- 投银（银两升级都要人跑过去扔到升级点）----
	// 银两的单位就是「两」，最低面额 1 两：投银时按还差多少截断，
	// 最后一袋可能只投 1 两；所有花费/收益都写成整两，不再有「一袋＝四十两」的大面额。
	SILVER_NAME: '两',
	// 一次投银的默认袋重（不够时按差值截断，最少 1 两）
	SILVER_BAG: 2,
	// 掷出银袋的抛物线飞行时间
	THROW_SECONDS: 0.45,
	THROW_RANGE: 150,

	// ---- 撒银退敌：给倭寇钱，让他们放弃追击 ----
	BRIBE_RANGE: 300,
	BRIBE_COST: { SCOUT: 2, SAMURAI: 4, BOSS: 12 } as Record<string, number>,
	// 收钱后退回海边的秒数（BOSS 只买“愕一下”的喘息时间）
	BRIBE_RETREAT_SECONDS: 8,
	BRIBE_BOSS_STUN_SECONDS: 3.5,

	ANCESTRAL_HALL_BASE_HP: 1000,
	ANCESTRAL_HALL_UPGRADE_BASE_COST: 9,
	ANCESTRAL_HALL_MAX_LEVEL: 5,
	ANCESTRAL_HALL_HP_PER_LEVEL: 300,
	SPRING_BLESSING_HEAL_RATIO: 0.2,
	// 宗祠升级不再加人口，而是提士气：每级 +12% 攻击、+8% 气血上限
	MORALE_ATTACK_PER_LEVEL: 0.12,
	MORALE_HP_PER_LEVEL: 0.08,

	// 夜袭猎杀：天黑后倭寇会主动追杀滞留在城外的族丁（此距离内）
	// 范围要给得大：倭寇从海岸登岸，晚归的人正好在他们前方，能真被咬上
	ENEMY_HUNT_RANGE: 900,
	// 追杀时的血狂加速（否则肯定追不上负盐的灶户，威慎无从谈起）
	ENEMY_HUNT_SPEED_SCALE: 1.9,

	// 营建读秒：升级 / 建造不再瞬间完成，须等工期走完（有工匠在场会快很多）
	CONSTRUCTION_SECONDS: {
		HALL_UPGRADE: 16,
		EAST_GATE_UPGRADE: 14,
		INNER_GATE_UPGRADE: 14,
		INNER_GATE_REPAIR: 0,
		TOWER_UNLOCK: 12,
		TOWER_UPGRADE: 10,
		HOUSE_UPGRADE: 12,
		LAND_RECLAIM: 12,
	} as Record<ProjectKind, number>,
	// 工期推进速率：基础自动推进 + 每名在场工匠加成，上限
	BUILD_RATE_IDLE: 0.3,
	BUILD_RATE_PER_BUILDER: 0.7,
	BUILD_RATE_MAX: 2.5,
	BUILD_SITE_RADIUS: 70,

	// 招募读秒：付款后过几秒族丁才到宗祠报到
	RECRUIT_SECONDS: 3.0,
	RECRUIT_MAX_PENDING: 3,

	// ---- 灶户取盐：出城到盐田装盐，再背回盐课司入库（来回一趟约 30 余秒，黄昏前须赶回） ----
	SALT_FETCH: {
		gatherSeconds: 3.0,
		// 负盐跑得慢（也很容易被倭寇追上），天黑狂奔时仍背负着担子
		carrySpeedScale: 0.62,
		panicSpeedScale: 1.35,
		// 夜里近处出现倭寇（比这还近）时，灶户会弃担逃命（盐担失落城外，可捡回）
		dropSaltThreatRange: 520,
		yardOffsetMin: -260,
		yardOffsetMax: 260,
		tripSilver: 6,
		dropSilverIfCaught: 3,
	},
	// 黄昏回城：白天剩余时间少于这个秒数时，城外族丁开始往城里跑
	DUSK_RETURN_SECONDS: 12,
	CURFEW_ALERT_SECONDS: 10,

	INNER_GATE_BASE_HP: 600,
	INNER_GATE_UPGRADE_COST: 7,
	INNER_GATE_MAX_LEVEL: 3,
	INNER_GATE_DEFENSE_X: 2280,

	EAST_GATE_BASE_HP: 800,

	// ---- 两头的倭寇码头 ----
	// 倭船就泊在这里。码头被打塌（HP=0）：那一侧只剩散兵零星摸上来；
	// 只要码头还在，夜暂时那一侧的人就是成建制上岸。
	PIER: {
		MAX_HP: 180,
		// 码头美术相对交互点往海里让多少：让到「栈桥右端正好接上岸线」为止
		// （岸线 = 西 600 / 东 7000，码头贴图宽 220，所以让 70 刚好贴岸）
		OFFSET_WEST: 70,
		OFFSET_EAST: 70,
		// 主角拆码头一下多少伤害 / 修一次补多少
		SABOTAGE_DAMAGE: 45,
		REPAIR_AMOUNT: 60,
		// 码头完好时，从这一侧上岸的额外兵力（相当于「码头运兵」）
		LANDING_BONUS_COUNT: 2,
		// 码头没了以后，这一侧只留多少比例的原波次（剩下的是散兵）
		BROKEN_SIDE_RATIO: 0.35,
		// 码头被拆后，多久（秒）对方会补一次拆后报复的散兵
		REVENGE_DELAY_SECONDS: 25,
		// 每砸一锤欠下的血债（人）；拆断那一刻再额外记 REVENGE_COUNT 人
		REVENGE_COUNT: 3,
		// 对码头出拳/麒麟步一下多少伤害（和拆桥同一档）
		HIT_DAMAGE: 45,
		// 码头受击判定半宽（世界单位）：原地站着打也要够得着
		HIT_BOX_HALF: 96,
		// 攻击伸出码头的额外距离（出拳的刀刃/冲刺的余势）
		HIT_REACH: 46,
		// 旧字段保留（有老代码引用），语义同 SABOTAGE_DAMAGE / REPAIR_AMOUNT
		HIT_HP: 45,
		REPAIR_HP: 60,
		REPAIR_SILVER: 2,
		SQUAD_PER_FULL_PIER: 3,
	} as PierConfig,
	EAST_GATE_UPGRADE_BASE_COST: 8,
	EAST_GATE_MAX_LEVEL: 3,
	EAST_GATE_DEFENSE_X: 3380,

	// 敌台防御塔配置（东西两面滩头 + 城堡三道防线）
	TOWER_SLOTS: [
		{ id: 'WEST_SALT_TOWER', x: 1200, defaultType: 'ARROW' as TowerType, unlocked: false, unlockCost: 11 },
		{ id: 'WEST_TOWER', x: 2150, defaultType: 'ARROW' as TowerType, unlocked: true, unlockCost: 0 },
		{ id: 'INNER_TOWER', x: 2450, defaultType: 'CANNON' as TowerType, unlocked: false, unlockCost: 7 },
		{ id: 'WALL_TOWER', x: 3150, defaultType: 'ARROW' as TowerType, unlocked: true, unlockCost: 0 },
		{ id: 'EAST_TOWER', x: 3520, defaultType: 'ARROW' as TowerType, unlocked: true, unlockCost: 0 },
		{ id: 'EAST_SALT_TOWER', x: 4650, defaultType: 'ARROW' as TowerType, unlocked: false, unlockCost: 11 },
	],
	TOWER_STATS: {
		ARROW: {
			name: '敌台箭楼',
			baseHp: 400,
			range: 420,
			damage: 22,
			cooldown: 1.1,
			upgradeCost: 6,
			color: 0xff8c6d46,
		},
		CANNON: {
			name: '佛郎机炮台',
			baseHp: 500,
			range: 520,
			damage: 58,
			splashRadius: 90,
			cooldown: 2.6,
			upgradeCost: 9,
			color: 0xff4a5568,
		},
	},
	// 麒麟步是「号令」不是「砍人」：主角冲过去的那一段防线上，敌台会立刻替你发箭。
	QILIN: {
		// 算「这一段防线」的距离：敌台与主角出发点的水平距离
		TOWER_RANGE: 560,
		// 号令加持下的出箭威力倍数（比常驻自动开火重一点，才值一个指令）
		DAMAGE_SCALE: 1.6,
	},

	// ---- 镜头取景 ----
	// 镜头拉近的旋钮只有一个：Screen.WORLD_ZOOM（见 src/config/Screen.ts）。
	// 那里同时按窗口像素尺寸做适配，保证任何分辨率下取景一致、界面不被放大。

	// 全局节奏：1 = 原速。作用在每一帧的 dt 上，移动 / 攻速 / 工期 / 招募 /
	// 日夜循环 / 动画速度会整体同步放慢，调一个数字即可改全局节奏。
	GAME_SPEED: 0.6,
	// 动画补偿：GAME_SPEED 会把 dt 整体缩小，若动画时钟也跟着变慢，
	// 6 帧的走路循环就会掉到 ~8fps 而显得卡顿。这里把动画时钟还原回真实时间。
	ANIM_TIME_SCALE: 1 / 0.6,

	// ---- 开垦：水田与盐田起始都是荒地，须投银 + 工期开垦才能产出 ----
	RECLAIM: {
		MAX_LEVEL: 3,
		// 升到下一级需投的白银（每级累加）
		COST: { PADDY: 6, SALT: 7 } as Record<string, number>,
		// 开垦一级的基础工期（秒），每级 +25%
		SECONDS: { PADDY: 11, SALT: 13 } as Record<string, number>,
		// 每级水田追加的粮产（在农夫 ROLES.FARMER.produceAmount 基础上叠加）
		PADDY_YIELD_PER_LEVEL: 15,
		// 每级盐田追加的每趟出盐白银
		SALT_YIELD_PER_LEVEL: 6,
	},

	// ---- 地图迷雾：未探索区域盖着黑幕，人走到跟前才揭形（《王国》式开拓感）----
	FOG_ZONES: [
		{ id: 'WEST_WILD', name: '西滩荒野', x: 600, width: 1650, startRevealed: false },
		{ id: 'FORTRESS', name: '永昌堡', x: 2250, width: 1450, startRevealed: true },
		{ id: 'EAST_WILD', name: '东滩荒野', x: 3700, width: 3350, startRevealed: false },
		{ id: 'EAST_SEA', name: '东海', x: 7050, width: 550, startRevealed: false },
	] as FogZoneConfig[],
	// 迷雾揭开半径：族丁踏入区域边线以内（或贴边这个距离）才揭开，不会轻易望穿荒滩
	FOG_REVEAL_RADIUS: 120,

	// 日夜循环常量
	TOTAL_NIGHTS: 8,
	DAY_DURATION: 66,
	DUSK_WARNING_TIME: 10,
	FOOD_CONSUME_INTERVAL: 5,
	FOOD_CONSUME_PER_COMBAT_UNIT: 2,

	// 城外拾荒刷新
	SCAVENGE_SALT_SILVER: 4,
	SCAVENGE_WOOD_REPAIR: 2,
	SCAVENGE_COUNT_PER_DAY: 4,

	// 主角王叔杲参数
	PLAYER: {
		name: '王叔杲',
		title: '筑堡总指挥',
		startX: 2470,
		moveSpeed: 320,
		interactRange: 95,
		dashDistance: 110,
		attackRange: 120,
		attackDamage: 45,
		knockbackDistance: 65,
		attackCooldown: 1.2,
		// 普通攻击（Space / L / 点按“拳”键）：短距离平A，快、轻、可连段，不位移
		lightRange: 82,
		lightDamage: 24,
		lightKnockback: 22,
		lightCooldown: 0.42,
		auraRadius: 250,
		auraAttackSpeedBonus: 0.3,
		auraDuration: 5.0,
		rallyCooldown: 4.0,
		color: 0xffd97706,
	},

	// 关键地标配置 (MAP_LANDMARKS)
	MAP_LANDMARKS: {
		WEST_COAST: {
			id: 'WEST_COAST',
			name: '西湾登陆点',
			subtitle: '倭寇西面登岸处',
			x: 300,
			width: 300,
			height: 80,
			color: 0xff1e4e79,
			description: '西面海域，倭寇船只由此登岸，向西城墙横推。',
			interactHint: '西海前哨：倭寇亦从此面上岸，两面受敌。',
		},
		ANCESTRAL_HALL: {
			id: 'ANCESTRAL_HALL',
			name: '王氏宗祠',
			subtitle: '江南故宫 · 核心',
			x: 2620,
			width: 180,
			height: 180,
			color: 0xff9b2c2c,
			description: '英桥王氏宗祠，基地核心。耐久归零则堡破人亡。',
			interactHint: '[E] 投一袋银饷 (40两) 招募族丁；点「升级宗祠」投银升士气',
		},
		WEST_PADDY: {
			id: 'WEST_PADDY',
			name: '西滩水田',
			subtitle: '荒地 · 待开垦',
			x: 1950,
			width: 190,
			height: 44,
			color: 0xff68a357,
			description: '西城墙外的荒滩。须由工匠投银开垦成水田，农夫方能耕作产粮；等级越高，粮产越厚。',
			interactHint: '[E] 投银开垦水田，再置办【锄头】派农夫耕作。',
			reclaimable: 'PADDY',
		},
		SALT_OFFICE: {
			id: 'SALT_OFFICE',
			name: '永嘉场盐课司',
			subtitle: '白银命脉',
			x: 2900,
			width: 170,
			height: 130,
			color: 0xffd6b36a,
			description: '灶户须出城赴盐田装盐，再背回盐课司入库。一趟来回三十余秒，黄昏来不及回城的盐丁会被倭寇所杀。',
			interactHint: '[E] 置办【盐铲】 (3白银) -> 闲置族丁转为灶户，出城取盐',
		},
		INNER_GATE: {
			id: 'INNER_GATE',
			name: '内城水门与作坊',
			subtitle: '第二道防线',
			x: 2350,
			width: 130,
			height: 190,
			color: 0xff5a6772,
			description: '工匠作坊与水门铁闸。所有营建与升级工程都在此调度，工匠越多工期越短。',
			interactHint: '[E] 置办【木锤】 (3白银) -> 筑城工匠 / 修筑内城炮台',
		},
		MAIN_WALL: {
			id: 'MAIN_WALL',
			name: '主城墙 · 校场',
			subtitle: '十八号包干分段',
			x: 3150,
			width: 180,
			height: 150,
			color: 0xff718096,
			description: '依十八号分段包干制筑成的主墙校场，可整备乡兵与王家拳武师。',
			interactHint: '[E] 置办【长枪】(4银) 或 【红绸拳谱】(5银)',
		},
		EAST_GATE: {
			id: 'EAST_GATE',
			name: '环海楼与东门瓮城',
			subtitle: '第一道核心防线',
			x: 3450,
			width: 140,
			height: 220,
			color: 0xff4a5568,
			description: '环海楼带瓮城，永昌堡东向第一道防线。入夜前务必关闭城门！',
			interactHint: '[E] 开关东门 / 加固东门瓮城（需工期）',
		},
		EAST_PADDY: {
			id: 'EAST_PADDY',
			name: '东滩水田',
			subtitle: '荒地 · 待开垦',
			x: 3850,
			width: 190,
			height: 44,
			color: 0xff68a357,
			description: '东城墙外的荒滩。须投银开垦成水田，农夫方能耕作产粮。',
			interactHint: '[E] 投银开垦水田，再置办【锄头】派农夫耕作。',
			reclaimable: 'PADDY',
		},
		WEST_SALT_FLAT: {
			id: 'WEST_SALT_FLAT',
			name: '西滩盐田',
			subtitle: '荒地 · 待开垦',
			x: 1200,
			width: 470,
			height: 28,
			color: 0xffb79f78,
			description: '西面滩涂。须投银开垦成盐田，灶户方能晒盐背盐；等级越高，每趟出盐越多。',
			interactHint: '[E] 投银开垦盐田，再置办【盐铲】派灶户晒盐。',
			reclaimable: 'SALT',
		},
		EAST_SALT_FLAT: {
			id: 'EAST_SALT_FLAT',
			name: '东滩盐田',
			subtitle: '荒地 · 待开垦',
			x: 4650,
			width: 560,
			height: 28,
			color: 0xffb79f78,
			description: '东面滩涂，灶户在此装盐；散落无主盐包(+4银)与漂流木料(+2修复)。黄昏前须全员撤回城内。',
			interactHint: '[E] 投银开垦盐田，再置办【盐铲】派灶户晒盐。',
			reclaimable: 'SALT',
		},
		EAST_COAST: {
			id: 'EAST_COAST',
			name: '东海登陆点',
			subtitle: '倭寇东面登岸处',
			x: 7300,
			width: 300,
			height: 80,
			color: 0xff1e4e79,
			description: '倭寇船只夜袭登岸之所，黑夜降临时倭寇由此涌来。',
			interactHint: '东海前哨，严防倭寇夜袭。',
		},
		// 两头的栈桥码头：倭寇靠岸下人的地方。
		// 拆了它，对面就只剩没码头的散兵摸上来；修回来，成建制的贼船又会靠岸。
		WEST_PIER: {
			id: 'WEST_PIER',
			name: '西滩倭寇码头',
			subtitle: '贼船靠岸的栈桥',
			x: 560,
			width: 220,
			height: 150,
			color: 0xff4a3b28,
			description: '西面这一段栈桥一直留着没动：贼船靠在这里，鬼子从这里下滩。',
			interactHint: '对淮栈桥出拳 [空格] 或麒麟步 [J] 可砍断它；按 [E] 花 2 两修桥。',
		},
		EAST_PIER: {
			id: 'EAST_PIER',
			name: '东滩倭寇码头',
			subtitle: '贼船靠岸的栈桥',
			x: 7040,
			width: 220,
			height: 150,
			color: 0xff4a3b28,
			description: '东面这一段栈桥一直留着没动：贼船靠在这里，鬼子从这里下滩。',
			interactHint: '对淮栈桥出拳 [空格] 或麒麟步 [J] 可砍断它；按 [E] 花 2 两修桥。',
		},
	} as Record<LandmarkId, LandmarkConfig>,

	// 族丁职业属性配置
	ROLES: {
		IDLE: {
			role: 'IDLE',
			name: '闲置族丁',
			toolName: '无',
			toolCost: 0,
			color: 0xffcbd5e0,
			maxHp: 80,
			moveSpeed: 130,
			attackDamage: 5,
			attackRange: 40,
			attackInterval: 1.5,
			produceInterval: 0,
			produceAmount: 0,
			repairPerSec: 0,
			description: '在宗祠附近待命，会自动拾取场上空闲工具转职。',
		},
		FARMER: {
			role: 'FARMER',
			name: '水田农夫',
			toolName: '锄头',
			toolCost: 2,
			color: 0xff48bb78,
			maxHp: 90,
			moveSpeed: 135,
			attackDamage: 6,
			attackRange: 40,
			attackInterval: 1.5,
			produceInterval: 5,
			produceAmount: 15,
			repairPerSec: 0,
			description: '白昼于堡内水田耕作，每5秒产出15粮草；入夜躲回宗祠。',
		},
		SALT_WORKER: {
			role: 'SALT_WORKER',
			name: '盐场灶户',
			toolName: '盐铲',
			toolCost: 3,
			color: 0xffecc94b,
			maxHp: 90,
			moveSpeed: 135,
			attackDamage: 6,
			attackRange: 40,
			attackInterval: 1.5,
			produceInterval: 3.0, // 在盐田装满一擔盐所需秒数
			produceAmount: 6, // 背回盐课司一趟入库白银
			repairPerSec: 0,
			description: '白昼出城到城外盐田装盐，再背回盐课司入库(每趟6银)。负重跑得慢，黄昏前赶不回来就会死在城外。',
		},
		BUILDER: {
			role: 'BUILDER',
			name: '筑城工匠',
			toolName: '木锤',
			toolCost: 3,
			color: 0xffed8936,
			maxHp: 110,
			moveSpeed: 150,
			attackDamage: 10,
			attackRange: 45,
			attackInterval: 1.4,
			produceInterval: 0,
			produceAmount: 0,
			repairPerSec: 15,
			description: '全天候巡检受损城门与敌台，每秒修复15点耐久；有在建工程时会先赶去工地，每名在场工匠使工期快 70%。',
		},
		MILITIA: {
			role: 'MILITIA',
			name: '永嘉场乡兵',
			toolName: '长枪',
			toolCost: 4,
			color: 0xff4299e1,
			maxHp: 160,
			moveSpeed: 165,
			attackDamage: 20,
			attackRange: 65,
			attackInterval: 1.0,
			produceInterval: 0,
			produceAmount: 0,
			repairPerSec: 0,
			description: '白昼巡逻校场，夜晚列阵最前线防线持枪迎敌。',
		},
		KUNG_FU: {
			role: 'KUNG_FU',
			name: '王家拳武师',
			toolName: '红绸拳谱',
			toolCost: 5,
			color: 0xffe53e3e,
			maxHp: 240,
			moveSpeed: 185,
			attackDamage: 32,
			attackRange: 70,
			attackInterval: 0.9,
			produceInterval: 0,
			produceAmount: 0,
			repairPerSec: 0,
			description: '精锐护堡武师，每3次攻击触发范围震击并恢复自身15点生命。',
		},
	} as Record<VillagerRole, RoleConfig>,

	// 倭寇敌人配置
	ENEMIES: {
		SCOUT: {
			type: 'SCOUT',
			name: '浪人斥候',
			maxHp: 90,
			moveSpeed: 120,
			attackDamage: 14,
			attackRange: 50,
			attackInterval: 1.1,
			rewardSilver: 1,
			width: 28,
			height: 52,
			color: 0xff9f7aea,
		},
		SAMURAI: {
			type: 'SAMURAI',
			name: '倭刀精锐',
			maxHp: 210,
			moveSpeed: 95,
			attackDamage: 26,
			attackRange: 60,
			attackInterval: 1.25,
			rewardSilver: 2,
			width: 34,
			height: 62,
			color: 0xffc53030,
		},
		BOSS: {
			type: 'BOSS',
			name: '倭酋统领',
			maxHp: 780,
			moveSpeed: 72,
			attackDamage: 48,
			attackRange: 75,
			attackInterval: 1.5,
			rewardSilver: 8,
			width: 48,
			height: 82,
			color: 0xff742a2a,
		},
	} as Record<EnemyType, EnemyConfig>,

	// 8 夜波次配置（八挫倭锋）
	NIGHT_WAVES: [
		{
			night: 1,
			title: '第一夜 · 初试堡墙',
			historicalNote: '嘉靖三十七年，王叔杲辍试归乡，倡议筑堡自卫，初成东垣。',
			victorySpeech: '「堡墙初立，小股倭探已退。然贼势方炽，速整农桑盐课以备大敌！」',
			rewardSilver: 4,
			groups: [
				{ enemyType: 'SCOUT', count: 4, interval: 1.8, delay: 0.5 },
				{ enemyType: 'SCOUT', count: 2, interval: 2.0, delay: 3.0 },
			],
		},
		{
			night: 2,
			title: '第二夜 · 滩涂夜袭',
			historicalNote: '贼众借潮汐登岸龙湾，直扑环海楼瓮城。',
			victorySpeech: '「乡兵用命，东门无恙。盐课既入堡，军资渐丰！」',
			rewardSilver: 5,
			groups: [
				{ enemyType: 'SCOUT', count: 6, interval: 1.5, delay: 0.5 },
				{ enemyType: 'SAMURAI', count: 2, interval: 2.5, delay: 5.0 },
			],
		},
		{
			night: 3,
			title: '第三夜 · 十八号齐心',
			historicalNote: '王氏宗族依“十八号分段包干”之制，轮番登城御敌。',
			victorySpeech: '「十八号族人同心协力，倭奴虽众，难越雷池一步！」',
			rewardSilver: 6,
			groups: [
				{ enemyType: 'SCOUT', count: 7, interval: 1.4, delay: 0.5 },
				{ enemyType: 'SAMURAI', count: 4, interval: 2.0, delay: 4.0 },
			],
		},
		{
			night: 4,
			title: '第四夜 · 倭酋叩关',
			historicalNote: '倭酋率精锐夜攻环海楼，炮石齐发，火光照彻永嘉场。',
			victorySpeech: '「斩却倭酋前锋，环海楼巍然屹立！然大股贼寇尚在海上窥伺。」',
			rewardSilver: 9,
			groups: [
				{ enemyType: 'SCOUT', count: 6, interval: 1.3, delay: 0.5 },
				{ enemyType: 'SAMURAI', count: 4, interval: 1.8, delay: 3.5 },
				{ enemyType: 'BOSS', count: 1, interval: 1.0, delay: 9.0 },
			],
		},
		{
			night: 5,
			title: '第五夜 · 断粮之忧',
			historicalNote: '贼围堡外，欲断我粮道，幸赖堡内水田自给不绝。',
			victorySpeech: '「堡中有田有盐，久困不乱。贼计既穷，其势必急！」',
			rewardSilver: 8,
			groups: [
				{ enemyType: 'SCOUT', count: 9, interval: 1.2, delay: 0.5 },
				{ enemyType: 'SAMURAI', count: 6, interval: 1.7, delay: 3.0 },
			],
		},
		{
			night: 6,
			title: '第六夜 · 铁闸怒潮',
			historicalNote: '东门激战正酣，内城水门铁闸与十二敌台互为犄角。',
			victorySpeech: '「敌台箭雨如蝗，佛郎机炮震海，倭寇丧胆而逃！」',
			rewardSilver: 9,
			groups: [
				{ enemyType: 'SCOUT', count: 10, interval: 1.0, delay: 0.5 },
				{ enemyType: 'SAMURAI', count: 8, interval: 1.5, delay: 2.5 },
			],
		},
		{
			night: 7,
			title: '第七夜 · 血战金岙志',
			historicalNote: '念及王沛梅头殉国、王德金岙捐躯之烈，全堡义师无不奋勇当先。',
			victorySpeech: '「先烈忠魂佑我英桥！明夜乃最后一战，务求全胜！」',
			rewardSilver: 11,
			groups: [
				{ enemyType: 'SCOUT', count: 12, interval: 0.9, delay: 0.5 },
				{ enemyType: 'SAMURAI', count: 10, interval: 1.4, delay: 2.0 },
			],
		},
		{
			night: 8,
			title: '第八夜 · 八挫倭锋',
			historicalNote: '永昌堡建成后八次击退倭寇大举进犯，保一方黎民平安，名垂青史。',
			victorySpeech: '「八战八捷，倭患终靖！永昌堡铁血之名，从此永镇东南海疆！」',
			rewardSilver: 15,
			groups: [
				{ enemyType: 'SCOUT', count: 12, interval: 0.85, delay: 0.5 },
				{ enemyType: 'SAMURAI', count: 10, interval: 1.3, delay: 2.0 },
				{ enemyType: 'BOSS', count: 2, interval: 4.5, delay: 8.0 },
			],
		},
	] as NightWaveConfig[],

	// 史料图鉴与背景文案
	HISTORY_CODEX: [
		{
			title: '英桥忠烈 · 王沛与王德',
			period: '明嘉靖三十七年（1558）',
			content: '嘉靖年间倭寇屡犯温州龙湾永嘉场。英桥王氏族长王沛于梅头迎敌殉国，乡贤王德于金岙力战捐躯，忠义精神激起全族筑堡抗倭之志。',
		},
		{
			title: '请筑堡疏 · 散财筑城',
			period: '嘉靖三十七年夏',
			content: '王叔果上《请筑堡疏》请建御倭之堡；其弟王叔杲毅然辍试归乡，捐资七千余金，亲自主持筑堡大计。',
		},
		{
			title: '十八号分段包干制',
			period: '筑城方略（历时11个月）',
			content: '永昌堡将城墙与防务划为十八号分段包干，全族分工协作，仅用十一个月便筑成石城，设四城门（东环海楼带瓮城）、四水门、十二敌台。',
		},
		{
			title: '堡内自给 · 八挫倭锋',
			period: '嘉靖三十八年以后',
			content: '堡内迁入永嘉场盐课司与巡检司，辟水田以自给，外联大罗山、东海之险，先后八次击退倭寇大举进犯，保全一方生灵。',
		},
	] as HistoryCodexEntry[],

	HISTORICAL_QUOTES: {
		TITLE_SUBTITLE: '明嘉靖三十七年 · 温州龙湾永嘉场',
		DUSK_WARNING: '黄昏钟响！天色将暗，请速按 [K] 召回城外族丁并关闭东门！',
		CURFEW_WARNING: '日头将落，仍有族丁滞留城外！天黑前赶不回内城，必遭倭寇毒手——速按 [K] 鸣鼓召回！',
		SALT_HAUL_LOST: '盐担失落城外……',
		SALT_HAUL_ARRIVED: '盐担入库',
		PROJECT_STARTED: '工程已开工，工匠会赶去施工（在工地左近可加快工期）。',
		SPRING_BLESSING: '宗祠春祭祈福生效：全体义师恢复 20% 气血！',
		LOW_FOOD_WARNING: '堡内粮草告罄！义师饥疲，攻击速度减半！',
		VICTORY_EPILOGUE: '嘉靖三十七年始筑，十一个月功成；四门十二敌台，八挫倭锋，永昌之名震于浙东。',
		DEFEAT_EPILOGUE: '宗祠倾颓，英桥沦陷……然忠义未泯，来日再聚族人，重筑永昌！',
	},
};
