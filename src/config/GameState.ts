import { GameConfig, TowerType, VillagerRole } from 'src/config/GameConfig';

export type DayPhase = 'DAY' | 'NIGHT';

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

	public towers: TowerState[] = [];

	// 族丁快照列表（由实体管理器同步，供 HUD 与跨系统读取）
	public villagers: VillagerSnapshot[] = [];

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

		this.villagers = [];
		this.totalKills = 0;
		this.wavesCleared = 0;
		this.toolsCrafted = 0;
		this.silverEarned = 0;
		this.isVictory = false;
	}

	public get maxPopulation(): number {
		return (
			GameConfig.INITIAL_MAX_POPULATION +
			(this.ancestralHallLevel - 1) * GameConfig.POPULATION_PER_HALL_LEVEL
		);
	}

	public get populationCount(): number {
		return this.villagers.length;
	}

	public get isLowFood(): boolean {
		return this.food <= 0;
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

	public getFrontDefenseX(): number {
		if (this.eastGateHp > 0 && !this.eastGateOpen) {
			return GameConfig.EAST_GATE_DEFENSE_X;
		}
		if (this.eastGateHp > 0 && this.phase === 'DAY') {
			return GameConfig.EAST_GATE_DEFENSE_X;
		}
		return GameConfig.INNER_GATE_DEFENSE_X;
	}

	public getRoleCount(role: VillagerRole): number {
		let count = 0;
		for (const v of this.villagers) {
			if (v.role === role) count++;
		}
		return count;
	}
}
