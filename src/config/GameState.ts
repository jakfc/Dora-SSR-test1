import { GameConfig, LandmarkId, ProjectKind, TowerType, VillagerRole } from 'src/config/GameConfig';

export type DayPhase = 'DAY' | 'NIGHT';

/** 在建工程：升级宗祠／加固城门／修筑敌台都不是瞬间完成，需要工期与工匠。 */
export interface BuildProject {
	kind: ProjectKind;
	towerId: string; // 敌台工程对应的 TowerState.id，非敌台工程为空串
	label: string; // 例：「王氏宗祠 Lv.3」
	x: number; // 施工点世界坐标（工匠据此站位）
	remain: number; // 剩余秒数
	total: number; // 总工期
	targetLevel: number;
	workers: number; // 在场工匠数（每帧刷新）
	hammerTimer: number; // 挥锤动画节拍
}

/** 招募队列：交银后原地读秒，到点族丁才到岗。 */
export interface RecruitJob {
	remain: number;
	total: number;
}

/** 民居：人口之源。人慢慢从这里添丁，也可花银子招募。 */
export interface HouseState {
	index: number;
	x: number;
	level: number;
	hp: number;
	maxHp: number;
}

export interface TowerState {
	id: string;
	x: number;
	type: TowerType;
	unlocked: boolean;
	level: number;
	hp: number;
	maxHp: number;
}

export interface VillagerSnapshot {
	id: number;
	role: VillagerRole;
	hp: number;
	maxHp: number;
	x: number;
}

/**
 * 全局单例游戏状态
 */
export class GameState {
	private static _instance: GameState | undefined = undefined;

	public static get instance(): GameState {
		if (!GameState._instance) {
			GameState._instance = new GameState();
		}
		return GameState._instance;
	}

	// 资源
	public silver = GameConfig.INITIAL_SILVER;
	public food = GameConfig.INITIAL_FOOD;

	// 日夜与波次
	public day = 1;
	public phase: DayPhase = 'DAY';
	public dayTimer = GameConfig.DAY_DURATION;
	public duskWarned = false;

	// 核心建筑与防线
	public ancestralHallLevel = 1;
	public ancestralHallMaxHp = GameConfig.ANCESTRAL_HALL_BASE_HP;
	public ancestralHallHp = GameConfig.ANCESTRAL_HALL_BASE_HP;

	public innerGateLevel = 1;
	public innerGateMaxHp = GameConfig.INNER_GATE_BASE_HP;
	public innerGateHp = GameConfig.INNER_GATE_BASE_HP;

	public eastGateLevel = 1;
	public eastGateMaxHp = GameConfig.EAST_GATE_BASE_HP;
	public eastGateHp = GameConfig.EAST_GATE_BASE_HP;
	public eastGateOpen = true;

	// ---- 两头的倭寇码头 ----
	// 血量 > 0 就是栈桥还好好的：那一侧的贼船能靠岸、夜暂成建制。
	// 被打到 0 就是栈桥断了：那一侧只能来散兵。修回来又变成建制夜暂。
	public pierMaxHp = GameConfig.PIER.MAX_HP;
	public westPierHp = GameConfig.PIER.MAX_HP;
	public eastPierHp = GameConfig.PIER.MAX_HP;

	public pierHpOf(side: 'W' | 'E'): number {
		return side === 'W' ? this.westPierHp : this.eastPierHp;
	}

	public setPierHp(side: 'W' | 'E', hp: number): void {
		const clamped = Math.max(0, Math.min(this.pierMaxHp, Math.round(hp)));
		if (side === 'W') this.westPierHp = clamped;
		else this.eastPierHp = clamped;
	}

	/** 这一侧还有没有能靠船的码头 */
	public pierAlive(side: 'W' | 'E'): boolean {
		return this.pierHpOf(side) > 0;
	}

	/**
	 * 拆码头欠下的血债：入夜后这一侧要额外还回来的人数。
	 * 砸一锤记 1 人，拆断那一刻再额外记 REVENGE_COUNT 人。
	 */
	public pierRevenge = { W: 0, E: 0 };

	public addPierRevenge(side: 'W' | 'E', count: number): void {
		if (count <= 0) return;
		this.pierRevenge[side] += count;
	}

	/** 取走并清零某一侧的报复人数 */
	public takePierRevenge(side: 'W' | 'E'): number {
		const n = this.pierRevenge[side];
		this.pierRevenge[side] = 0;
		return n;
	}

	public towers: TowerState[] = [];

	// 营建工程与招募队列
	public projects: BuildProject[] = [];
	public recruits: RecruitJob[] = [];

	// 族丁快照列表（由实体管理器同步，供 HUD 与跨系统读取）
	public villagers: VillagerSnapshot[] = [];

	/** 民居（人口容量 + 自然添丁） */
	public houses: HouseState[] = [];
	/** 可开垦地块等级（LandmarkId → 已开垦等级，0 = 荒地未开垦） */
	public landLevels: Record<string, number> = {};
	/** 地图迷雾：已探索的迷雾区 id */
	public explored: Record<string, boolean> = {};
	/** 已投入的银两（按目标 id 累计，例：'HALL'、'EAST_GATE'、'TOWER:INNER_TOWER'、'HOUSE:0'） */
	public donations: Record<string, number> = {};
	/** 民居自然添丁计时 */
	private houseSpawnTimer = 0;
	/** 下一名新丁从哪间民居出现（轮流） */
	private houseSpawnCursor = 0;

	// 战绩统计
	public totalKills = 0;
	public wavesCleared = 0;
	public toolsCrafted = 0;
	public silverEarned = 0;
	public isVictory = false;

	private constructor() {
		this.reset();
	}

	public reset(): void {
		this.silver = GameConfig.INITIAL_SILVER;
		this.food = GameConfig.INITIAL_FOOD;

		this.day = 1;
		this.phase = 'DAY';
		this.dayTimer = GameConfig.DAY_DURATION;
		this.duskWarned = false;

		this.ancestralHallLevel = 1;
		this.ancestralHallMaxHp = GameConfig.ANCESTRAL_HALL_BASE_HP;
		this.ancestralHallHp = GameConfig.ANCESTRAL_HALL_BASE_HP;

		this.innerGateLevel = 1;
		this.innerGateMaxHp = GameConfig.INNER_GATE_BASE_HP;
		this.innerGateHp = GameConfig.INNER_GATE_BASE_HP;

		this.eastGateLevel = 1;
		this.eastGateMaxHp = GameConfig.EAST_GATE_BASE_HP;
		this.eastGateHp = GameConfig.EAST_GATE_BASE_HP;
		this.eastGateOpen = true;

		this.pierMaxHp = GameConfig.PIER.MAX_HP;
		this.pierRevenge = { W: 0, E: 0 };
		this.westPierHp = GameConfig.PIER.MAX_HP;
		this.eastPierHp = GameConfig.PIER.MAX_HP;

		this.towers = GameConfig.TOWER_SLOTS.map((slot) => {
			const stats = GameConfig.TOWER_STATS[slot.defaultType];
			return {
				id: slot.id,
				x: slot.x,
				type: slot.defaultType,
				unlocked: slot.unlocked,
				level: 1,
				hp: stats.baseHp,
				maxHp: stats.baseHp,
			};
		});

		this.projects = [];
		this.recruits = [];
		this.villagers = [];
		this.houses = GameConfig.HOUSE_SLOTS.map((slot, i) => ({
			index: i,
			x: slot.x,
			level: slot.level,
			hp: GameConfig.HOUSE_BASE_HP,
			maxHp: GameConfig.HOUSE_BASE_HP,
		}));
		this.donations = {};
		this.houseSpawnTimer = 0;
		this.houseSpawnCursor = 0;

		// 可开垦地块开局都是荒地（level 0）
		this.landLevels = {};
		for (const id of Object.keys(GameConfig.MAP_LANDMARKS) as LandmarkId[]) {
			if (GameConfig.MAP_LANDMARKS[id].reclaimable !== undefined) this.landLevels[id] = 0;
		}
		// 迷雾：城堡核心区开局已亮，四野待探索
		this.explored = {};
		for (const z of GameConfig.FOG_ZONES) this.explored[z.id] = z.startRevealed === true;
		this.totalKills = 0;
		this.wavesCleared = 0;
		this.toolsCrafted = 0;
		this.silverEarned = 0;
		this.isVictory = false;
	}

	/**
	 * 人口上限 = min(住房容量, 粮食可养人口)。
	 * 房屋决定住得下多少人，粮食决定养得起多少人；宗祠升级只管士气不再管人口。
	 */
	public get maxPopulation(): number {
		const byHouse = this.housingCapacity;
		const byFood = this.foodCapacity;
		return byHouse < byFood ? byHouse : byFood;
	}

	/** 住房容量：所有民居等级之和 × 每级可住人数 */
	public get housingCapacity(): number {
		let total = 0;
		for (const h of this.houses) total += h.level * GameConfig.HOUSE_CAPACITY_PER_LEVEL;
		return total;
	}

	/** 粮食可养人口：每 FOOD_PER_PERSON 粮草养活 1 人 */
	public get foodCapacity(): number {
		return Math.floor(this.food / GameConfig.FOOD_PER_PERSON);
	}

	/** 宗祠士气：攻击加成（每级 +12%） */
	public get moraleBonus(): number {
		return (this.ancestralHallLevel - 1) * GameConfig.MORALE_ATTACK_PER_LEVEL;
	}

	/** 宗祠士气：气血上限加成（每级 +8%） */
	public get moraleHpBonus(): number {
		return (this.ancestralHallLevel - 1) * GameConfig.MORALE_HP_PER_LEVEL;
	}

	/** 还能容纳多少新丁（含已在路上的招募队列） */
	public get freeSlots(): number {
		return this.maxPopulation - this.populationCount - this.recruits.length;
	}

	// ---- 民居与添丁 ----

	/**
	 * 民居自然添丁：住房与粮食都有余裕时，过 HOUSE_SPAWN_SECONDS 从民居走出1名新丁。
	 * @returns 本帧应新添的族丁数与其出生坐标（调用方负责真正生成）。
	 */
	public tickHouses(dt: number): { x: number }[] {
		const born: { x: number }[] = [];
		if (this.freeSlots <= 0 || this.houses.length === 0) {
			this.houseSpawnTimer = 0;
			return born;
		}
		this.houseSpawnTimer += dt;
		while (this.houseSpawnTimer >= GameConfig.HOUSE_SPAWN_SECONDS && this.freeSlots > 0) {
			this.houseSpawnTimer -= GameConfig.HOUSE_SPAWN_SECONDS;
			const house = this.houses[this.houseSpawnCursor % this.houses.length];
			this.houseSpawnCursor++;
			born.push({ x: house.x + 26 });
		}
		return born;
	}

	/** 民居自然添丁进度（0~1，HUD 显示用） */
	public get houseSpawnProgress(): number {
		return Math.max(0, Math.min(1, this.houseSpawnTimer / GameConfig.HOUSE_SPAWN_SECONDS));
	}

	// ---- 捐银（投银升级 / 招兵 / 贿赂） ----

	public donationOf(key: string): number {
		const v = this.donations[key];
		return v === undefined ? 0 : v;
	}

	/** 投一袋银子进捐银池（上限不超过所需额） */
	public addDonation(key: string, amount: number): number {
		const next = this.donationOf(key) + amount;
		this.donations[key] = next;
		return next;
	}

	/** 捐银到位后清空该池 */
	public clearDonation(key: string): void {
		this.donations[key] = 0;
	}

	/** 城外（内城水门以东）尚在人世的族丁数，用于黄昏未归警报。 */
	public get stragglerCount(): number {
		const westWallX = GameConfig.MAP_LANDMARKS.INNER_GATE.x;
		const eastWallX = GameConfig.MAP_LANDMARKS.EAST_GATE.x;
		let count = 0;
		for (const v of this.villagers) {
			if (v.hp > 0 && (v.x < westWallX || v.x > eastWallX)) count++;
		}
		return count;
	}

	// ---- 营建工程 ----

	public hasProject(kind: ProjectKind, towerId = ''): boolean {
		for (const p of this.projects) {
			if (p.kind === kind && p.towerId === towerId) return true;
		}
		return false;
	}

	public startProject(
		kind: ProjectKind,
		label: string,
		x: number,
		seconds: number,
		targetLevel: number,
		towerId = ''
	): BuildProject {
		const project: BuildProject = {
			kind,
			towerId,
			label,
			x,
			remain: seconds,
			total: seconds,
			targetLevel,
			workers: 0,
			hammerTimer: 0.6,
		};
		this.projects.push(project);
		return project;
	}

	/**
	 * 推进所有工程。返回本帧完工的工程列表，调用方负责结算效果与画面刷新。
	 */
	public tickProjects(dt: number): BuildProject[] {
		if (this.projects.length === 0) return [];
		const done: BuildProject[] = [];
		for (let i = this.projects.length - 1; i >= 0; i--) {
			const p = this.projects[i];
			let rate = GameConfig.BUILD_RATE_IDLE + p.workers * GameConfig.BUILD_RATE_PER_BUILDER;
			if (rate > GameConfig.BUILD_RATE_MAX) rate = GameConfig.BUILD_RATE_MAX;
			p.remain -= rate * dt;
			p.hammerTimer += dt;
			if (p.remain <= 0) {
				p.remain = 0;
				this.projects.splice(i, 1);
				done.push(p);
			}
		}
		return done;
	}

	// ---- 招募读秒 ----

	public startRecruit(): void {
		this.recruits.push({
			remain: GameConfig.RECRUIT_SECONDS,
			total: GameConfig.RECRUIT_SECONDS,
		});
	}

	/** 推进招募队列，返回本帧到岗的族丁数量。 */
	public tickRecruits(dt: number): number {
		if (this.recruits.length === 0) return 0;
		let arrived = 0;
		for (let i = this.recruits.length - 1; i >= 0; i--) {
			const r = this.recruits[i];
			r.remain -= dt;
			if (r.remain <= 0) {
				this.recruits.splice(i, 1);
				arrived++;
			}
		}
		return arrived;
	}

	public get populationCount(): number {
		return this.villagers.length;
	}

	public get isLowFood(): boolean {
		return this.food <= 0;
	}

	// ---- 开垦与迷雾 ----

	/** 地块当前开垦等级（0 = 荒地） */
	public landLevelOf(id: string): number {
		const v = this.landLevels[id];
		return v === undefined ? 0 : v;
	}

	/** 地块是否已开垦（等级 ≥ 1，可以派人产出） */
	public isLandReady(id: string): boolean {
		return this.landLevelOf(id) > 0;
	}

	/** 某类可开垦地块（PADDY 水田 / SALT 盐田），供族丁就近择地劳作 */
	public landPlots(kind: 'PADDY' | 'SALT'): LandmarkId[] {
		const out: LandmarkId[] = [];
		for (const id of Object.keys(GameConfig.MAP_LANDMARKS) as LandmarkId[]) {
			if (GameConfig.MAP_LANDMARKS[id].reclaimable === kind) out.push(id);
		}
		return out;
	}

	/** 水田总开垦等级（HUD 展示：粮产加成） */
	public get paddyLevels(): number {
		let total = 0;
		for (const id of this.landPlots('PADDY')) total += this.landLevelOf(id);
		return total;
	}

	/** 盐田总开垦等级（HUD 展示：盐产出盐加成） */
	public get saltLevels(): number {
		let total = 0;
		for (const id of this.landPlots('SALT')) total += this.landLevelOf(id);
		return total;
	}

	public isExplored(zoneId: string): boolean {
		return this.explored[zoneId] === true;
	}

	/** 揭开一片迷雾；返回是否为新揭开 */
	public revealZone(zoneId: string): boolean {
		if (this.explored[zoneId] === true) return false;
		this.explored[zoneId] = true;
		return true;
	}

	/** 尚有迷雾未揭开的区域数 */
	public get foggedCount(): number {
		let n = 0;
		for (const z of GameConfig.FOG_ZONES) {
			if (this.explored[z.id] !== true) n++;
		}
		return n;
	}

	public addSilver(amount: number): void {
		if (amount <= 0) return;
		this.silver += amount;
		this.silverEarned += amount;
	}

	public spendSilver(amount: number): boolean {
		if (this.silver < amount) return false;
		this.silver -= amount;
		return true;
	}

	public addFood(amount: number): void {
		if (amount <= 0) return;
		this.food += amount;
	}

	public consumeFood(amount: number): void {
		this.food = Math.max(0, this.food - amount);
	}

	/** 东面防线：东门关着守东门；门开着或已被破，敌锋直指宗祠，就退守宗祠前 */
	public getFrontDefenseX(): number {
		if (this.eastGateHp > 0 && !this.eastGateOpen) {
			return GameConfig.EAST_GATE_DEFENSE_X;
		}
		return GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x + 60;
	}

	/** 西面防线：内城水门（西墙） */
	public getWestDefenseX(): number {
		return GameConfig.MAP_LANDMARKS.INNER_GATE.x;
	}

	public getRoleCount(role: VillagerRole): number {
		let count = 0;
		for (const v of this.villagers) {
			if (v.role === role) count++;
		}
		return count;
	}
}
