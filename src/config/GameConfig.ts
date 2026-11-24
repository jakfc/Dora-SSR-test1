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

export type LandmarkId =
	| 'DALUO_MOUNTAIN'
	| 'ANCESTRAL_HALL'
	| 'PADDY_FIELD'
	| 'SALT_OFFICE'
	| 'INNER_GATE'
	| 'MAIN_WALL'
	| 'EAST_GATE'
	| 'OUTER_SALT_FLAT'
	| 'COAST_SPAWN';

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
	MAP_WIDTH: 3600,
	GROUND_Y: 160,
	CAMERA_MIN_X: 640,
	CAMERA_MAX_X: 2960,
	SAFE_LINE_X: 2400,
	SPAWN_X: 3500,
	OUTER_ZONE_MIN_X: 2800,
	OUTER_ZONE_MAX_X: 3400,

	// 初始资源与建筑参数
	INITIAL_SILVER: 260,
	INITIAL_FOOD: 120,
	INITIAL_MAX_POPULATION: 8,
	POPULATION_PER_HALL_LEVEL: 4,
	RECRUIT_VILLAGER_COST: 80,

	ANCESTRAL_HALL_BASE_HP: 1000,
	ANCESTRAL_HALL_UPGRADE_BASE_COST: 180,
	ANCESTRAL_HALL_MAX_LEVEL: 3,
	SPRING_BLESSING_HEAL_RATIO: 0.2,

	INNER_GATE_BASE_HP: 600,
	INNER_GATE_UPGRADE_COST: 140,
	INNER_GATE_DEFENSE_X: 1550,

	EAST_GATE_BASE_HP: 800,
	EAST_GATE_UPGRADE_BASE_COST: 160,
	EAST_GATE_MAX_LEVEL: 3,
	EAST_GATE_DEFENSE_X: 2350,

	// 敌台防御塔配置
	TOWER_SLOTS: [
		{ id: 'INNER_TOWER', x: 1640, defaultType: 'CANNON' as TowerType, unlocked: false, unlockCost: 150 },
		{ id: 'WALL_TOWER', x: 2000, defaultType: 'ARROW' as TowerType, unlocked: true, unlockCost: 0 },
		{ id: 'EAST_TOWER', x: 2360, defaultType: 'ARROW' as TowerType, unlocked: true, unlockCost: 0 },
	],
	TOWER_STATS: {
		ARROW: {
			name: '敌台箭楼',
			baseHp: 400,
			range: 420,
			damage: 22,
			cooldown: 1.1,
			upgradeCost: 120,
			color: 0xff8c6d46,
		},
		CANNON: {
			name: '佛郎机炮台',
			baseHp: 500,
			range: 520,
			damage: 58,
			splashRadius: 90,
			cooldown: 2.6,
			upgradeCost: 180,
			color: 0xff4a5568,
		},
	},

	// 日夜循环常量
	TOTAL_NIGHTS: 8,
	DAY_DURATION: 45,
	DUSK_WARNING_TIME: 10,
	FOOD_CONSUME_INTERVAL: 5,
	FOOD_CONSUME_PER_COMBAT_UNIT: 2,

	// 城外拾荒刷新
	SCAVENGE_SALT_SILVER: 80,
	SCAVENGE_WOOD_REPAIR: 50,
	SCAVENGE_COUNT_PER_DAY: 4,

	// 主角王叔杲参数
	PLAYER: {
		name: '王叔杲',
		title: '筑堡总指挥',
		startX: 460,
		moveSpeed: 320,
		interactRange: 95,
		dashDistance: 110,
		attackRange: 120,
		attackDamage: 45,
		knockbackDistance: 65,
		attackCooldown: 1.2,
		auraRadius: 250,
		auraAttackSpeedBonus: 0.3,
		auraDuration: 5.0,
		rallyCooldown: 4.0,
		color: 0xffd97706,
	},

	// 关键地标配置 (MAP_LANDMARKS)
	MAP_LANDMARKS: {
		DALUO_MOUNTAIN: {
			id: 'DALUO_MOUNTAIN',
			name: '大罗山',
			subtitle: '西屏屏障',
			x: 80,
			width: 160,
			height: 360,
			color: 0xff2f4f4f,
			description: '永嘉场西侧天然山屏，俯瞰龙湾盐田与东海海岸。',
			interactHint: '山川形胜，永昌堡背山面海之基。',
		},
		ANCESTRAL_HALL: {
			id: 'ANCESTRAL_HALL',
			name: '王氏宗祠',
			subtitle: '江南故宫 · 核心',
			x: 400,
			width: 180,
			height: 180,
			color: 0xff9b2c2c,
			description: '英桥王氏宗祠，基地核心。耐久归零则堡破人亡。',
			interactHint: '[E] 招募闲置族丁 (80白银) / 升级宗祠提高人口上限',
		},
		PADDY_FIELD: {
			id: 'PADDY_FIELD',
			name: '堡内水田',
			subtitle: '军粮自给',
			x: 800,
			width: 220,
			height: 44,
			color: 0xff68a357,
			description: '堡内开垦水田自给自足。农夫每5秒产出15粮草，断粮时义师攻速减半。',
			interactHint: '[E] 置办【锄头】 (50白银) -> 闲置族丁拾取转为农夫',
		},
		SALT_OFFICE: {
			id: 'SALT_OFFICE',
			name: '永嘉场盐课司',
			subtitle: '白银命脉',
			x: 1200,
			width: 170,
			height: 130,
			color: 0xffd6b36a,
			description: '迁入堡内之盐课司。灶户每5秒煎盐产出25白银。',
			interactHint: '[E] 置办【盐铲】 (60白银) -> 闲置族丁拾取转为灶户',
		},
		INNER_GATE: {
			id: 'INNER_GATE',
			name: '内城水门与作坊',
			subtitle: '第二道防线',
			x: 1600,
			width: 130,
			height: 190,
			color: 0xff5a6772,
			description: '工匠作坊与水门铁闸。东门若失守，义师退守此第二道防线。',
			interactHint: '[E] 置办【木锤】 (70白银) -> 筑城工匠 / 解锁内城炮台',
		},
		MAIN_WALL: {
			id: 'MAIN_WALL',
			name: '主城墙 · 校场',
			subtitle: '十八号包干分段',
			x: 2000,
			width: 180,
			height: 150,
			color: 0xff718096,
			description: '依十八号分段包干制筑成的主墙校场，可整备乡兵与王家拳武师。',
			interactHint: '[E] 置办【长枪】(75银) 或 【红绸拳谱】(110银)',
		},
		EAST_GATE: {
			id: 'EAST_GATE',
			name: '环海楼与东门瓮城',
			subtitle: '第一道核心防线',
			x: 2400,
			width: 140,
			height: 220,
			color: 0xff4a5568,
			description: '环海楼带瓮城，永昌堡东向第一道防线。入夜前务必关闭城门！',
			interactHint: '[E] 开关东门 / 升级加固东门瓮城',
		},
		OUTER_SALT_FLAT: {
			id: 'OUTER_SALT_FLAT',
			name: '城外盐田与滩涂',
			subtitle: '白天高危拓荒区',
			x: 3100,
			width: 560,
			height: 28,
			color: 0xffb79f78,
			description: '城外散落无主盐包(+80银)与漂流木料(+50修复)，黄昏前须全员撤回城内。',
			interactHint: '靠近散落物资自动拾取，按 [K] 鸣鼓召回城外族丁。',
		},
		COAST_SPAWN: {
			id: 'COAST_SPAWN',
			name: '东海海岸',
			subtitle: '倭寇登岸处',
			x: 3500,
			width: 140,
			height: 60,
			color: 0xff1e4e79,
			description: '倭寇船只夜袭登岸之所，黑夜降临时倭寇由此涌来。',
			interactHint: '东海前哨，严防倭寇夜袭。',
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
			toolCost: 50,
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
			toolCost: 60,
			color: 0xffecc94b,
			maxHp: 90,
			moveSpeed: 135,
			attackDamage: 6,
			attackRange: 40,
			attackInterval: 1.5,
			produceInterval: 5,
			produceAmount: 25,
			repairPerSec: 0,
			description: '白昼于盐课司煎盐，每5秒产出25白银；入夜躲回宗祠。',
		},
		BUILDER: {
			role: 'BUILDER',
			name: '筑城工匠',
			toolName: '木锤',
			toolCost: 70,
			color: 0xffed8936,
			maxHp: 110,
			moveSpeed: 150,
			attackDamage: 10,
			attackRange: 45,
			attackInterval: 1.4,
			produceInterval: 0,
			produceAmount: 0,
			repairPerSec: 15,
			description: '全天候巡检受损城门与敌台，每秒修复15点耐久。',
		},
		MILITIA: {
			role: 'MILITIA',
			name: '永嘉场乡兵',
			toolName: '长枪',
			toolCost: 75,
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
			toolCost: 110,
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
			rewardSilver: 18,
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
			rewardSilver: 35,
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
			rewardSilver: 160,
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
			rewardSilver: 90,
			groups: [
				{ enemyType: 'SCOUT', count: 5, interval: 1.8, delay: 0.5 },
			],
		},
		{
			night: 2,
			title: '第二夜 · 滩涂夜袭',
			historicalNote: '贼众借潮汐登岸龙湾，直扑环海楼瓮城。',
			victorySpeech: '「乡兵用命，东门无恙。盐课既入堡，军资渐丰！」',
			rewardSilver: 110,
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
			rewardSilver: 130,
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
			rewardSilver: 180,
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
			rewardSilver: 160,
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
			rewardSilver: 190,
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
			rewardSilver: 220,
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
			rewardSilver: 300,
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
		SPRING_BLESSING: '宗祠春祭祈福生效：全体义师恢复 20% 气血！',
		LOW_FOOD_WARNING: '堡内粮草告罄！义师饥疲，攻击速度减半！',
		VICTORY_EPILOGUE: '嘉靖三十七年始筑，十一个月功成；四门十二敌台，八挫倭锋，永昌之名震于浙东。',
		DEFEAT_EPILOGUE: '宗祠倾颓，英桥沦陷……然忠义未泯，来日再聚族人，重筑永昌！',
	},
};
