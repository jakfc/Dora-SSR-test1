import { Color, DrawNode, Label, Node, Vec2 } from 'Dora';
import { GameConfig, VillagerRole } from 'src/config/GameConfig';
import { GameState } from 'src/config/GameState';
import { Enemy } from 'src/entities/Enemy';
import { artInto } from 'src/config/Assets';

export interface ToolDrop {
	id: number;
	x: number;
	role: VillagerRole;
	claimed: boolean;
	node: Node.Type;
}

export interface VillagerUpdateContext {
	phase: 'DAY' | 'NIGHT';
	enemies: Enemy[];
	tools: ToolDrop[];
	playerInAura: (x: number) => boolean;
	onProduceResource: (kind: 'FOOD' | 'SILVER', amount: number, x: number) => void;
	onRepairBuilding: (amount: number, x: number) => void;
}

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
		draw.drawPolygon(verts, Color(fillColor), 1, Color(borderColor));
	} else {
		draw.drawPolygon(verts, Color(fillColor));
	}
}

/**
 * 族丁实体与职业 AI 状态机
 */
export class Villager {
	private static nextId = 1;

	public readonly id: number;
	public readonly node: Node.Type;
	private readonly bodyDraw: DrawNode.Type;
	private readonly roleLabel: Label.Type;
	private readonly artNode: Node.Type;

	public role: VillagerRole = 'IDLE';
	public x: number;
	public hp: number;
	public maxHp: number;
	public dead = false;

	private wanderTargetX: number;
	private rallyTargetX: number | undefined = undefined;
	private rallyTimer = 0;

	private produceTimer = 0;
	private attackTimer = 0;
	private attackCount = 0;
	private repairAccum = 0;
	private shockwaveTimer = 0;

	constructor(startX: number, role: VillagerRole = 'IDLE') {
		this.id = Villager.nextId++;
		this.x = startX;
		this.wanderTargetX = startX;
		const cfg = GameConfig.ROLES[role];
		this.role = role;
		this.maxHp = cfg.maxHp;
		this.hp = cfg.maxHp;

		this.node = Node();
		this.node.x = this.x;
		this.node.y = GameConfig.GROUND_Y;

		this.bodyDraw = DrawNode();
		this.node.addChild(this.bodyDraw);

		// 美术挂点：位于方块层之上、职业名之下
		this.artNode = Node();
		this.node.addChild(this.artNode);

		this.roleLabel = Label('sarasa-mono-sc-regular', 13) as Label.Type;
		this.roleLabel.y = 62;
		this.node.addChild(this.roleLabel);

		this.refreshVisual();
	}

	public changeRole(newRole: VillagerRole): void {
		this.role = newRole;
		const cfg = GameConfig.ROLES[newRole];
		const ratio = this.maxHp > 0 ? this.hp / this.maxHp : 1;
		this.maxHp = cfg.maxHp;
		this.hp = Math.max(20, Math.round(cfg.maxHp * ratio));
		this.produceTimer = 0;
		this.attackTimer = 0;
		this.attackCount = 0;
		this.refreshVisual();
	}

	public orderRally(targetX: number, duration = 4.0): void {
		this.rallyTargetX = targetX + ((this.id % 5) - 2) * 18;
		this.rallyTimer = duration;
	}

	public healPercent(ratio: number): void {
		if (this.dead) return;
		this.hp = Math.min(this.maxHp, this.hp + Math.round(this.maxHp * ratio));
		this.refreshVisual();
	}

	public takeDamage(amount: number): void {
		if (this.dead) return;
		this.hp -= amount;
		if (this.hp <= 0) {
			this.hp = 0;
			this.dead = true;
			this.node.removeFromParent();
			return;
		}
		this.refreshVisual();
	}

	private refreshVisual(): void {
		const cfg = GameConfig.ROLES[this.role];
		this.bodyDraw.clear();
		// 有美术素材时按职业换精灵
		if (artInto(this.artNode, `villager_${this.role}`) === undefined) {
			// 躯干
			drawRect(this.bodyDraw, -11, 0, 22, 40, cfg.color, 0xff1a202c);
			// 头部
			drawRect(this.bodyDraw, -7, 40, 14, 12, 0xfffbd38d);
		}
		// 武师拳气特效
		if (this.shockwaveTimer > 0) {
			drawRect(this.bodyDraw, -45, 4, 90, 18, 0x77fc8181, 0xffe53e3e);
		}
		// 血条
		if (this.hp < this.maxHp) {
			const pct = Math.max(0, this.hp / this.maxHp);
			drawRect(this.bodyDraw, -14, 54, 28, 4, 0xff2d3748);
			drawRect(this.bodyDraw, -14, 54, 28 * pct, 4, 0xff48bb78);
		}
		this.roleLabel.text = cfg.name.slice(0, 4);
		this.roleLabel.color = Color(0xffe2e8f0);
	}

	private moveToward(targetX: number, dt: number): boolean {
		const speed = GameConfig.ROLES[this.role].moveSpeed;
		const diff = targetX - this.x;
		if (Math.abs(diff) <= 6) {
			return true;
		}
		const step = Math.sign(diff) * Math.min(Math.abs(diff), speed * dt);
		this.x = Math.max(60, Math.min(GameConfig.MAP_WIDTH - 60, this.x + step));
		return false;
	}

	public update(dt: number, ctx: VillagerUpdateContext): void {
		if (this.dead) return;

		if (this.attackTimer > 0) this.attackTimer = Math.max(0, this.attackTimer - dt);
		if (this.shockwaveTimer > 0) {
			this.shockwaveTimer = Math.max(0, this.shockwaveTimer - dt);
			if (this.shockwaveTimer === 0) this.refreshVisual();
		}

		// 鸣鼓集结优先移动
		if (this.rallyTimer > 0 && this.rallyTargetX !== undefined) {
			this.rallyTimer -= dt;
			const arrived = this.moveToward(this.rallyTargetX, dt);
			if (arrived || this.rallyTimer <= 0) {
				this.rallyTimer = 0;
				this.rallyTargetX = undefined;
			}
			this.node.x = this.x;
			return;
		}

		switch (this.role) {
			case 'IDLE':
				this.updateIdle(dt, ctx);
				break;
			case 'FARMER':
			case 'SALT_WORKER':
				this.updateProducer(dt, ctx);
				break;
			case 'BUILDER':
				this.updateBuilder(dt, ctx);
				break;
			case 'MILITIA':
			case 'KUNG_FU':
				this.updateCombat(dt, ctx);
				break;
		}

		this.node.x = this.x;
	}

	private updateIdle(dt: number, ctx: VillagerUpdateContext): void {
		// 优先寻找场上未被拾取的工具
		let nearestTool: ToolDrop | undefined = undefined;
		let bestDist = Infinity;
		for (const tool of ctx.tools) {
			if (tool.claimed) continue;
			const d = Math.abs(tool.x - this.x);
			if (d < bestDist) {
				bestDist = d;
				nearestTool = tool;
			}
		}

		if (nearestTool) {
			const arrived = this.moveToward(nearestTool.x, dt);
			if (arrived && !nearestTool.claimed) {
				nearestTool.claimed = true;
				nearestTool.node.removeFromParent();
				this.changeRole(nearestTool.role);
			}
			return;
		}

		// 在宗祠附近徘徊
		const hallX = GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x;
		if (this.moveToward(this.wanderTargetX, dt)) {
			const offset = ((this.id * 37) % 120) - 60;
			this.wanderTargetX = hallX + (Math.abs(this.x - hallX) > 20 ? 0 : offset);
		}
	}

	private updateProducer(dt: number, ctx: VillagerUpdateContext): void {
		const isFarmer = this.role === 'FARMER';
		if (ctx.phase === 'NIGHT') {
			const shelterX = GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x + ((this.id % 5) - 2) * 20;
			this.moveToward(shelterX, dt);
			return;
		}

		const workX =
			(isFarmer
				? GameConfig.MAP_LANDMARKS.PADDY_FIELD.x
				: GameConfig.MAP_LANDMARKS.SALT_OFFICE.x) +
			((this.id % 5) - 2) * 22;

		if (this.moveToward(workX, dt)) {
			const cfg = GameConfig.ROLES[this.role];
			this.produceTimer += dt;
			if (this.produceTimer >= cfg.produceInterval) {
				this.produceTimer -= cfg.produceInterval;
				if (isFarmer) {
					GameState.instance.addFood(cfg.produceAmount);
					ctx.onProduceResource('FOOD', cfg.produceAmount, this.x);
				} else {
					GameState.instance.addSilver(cfg.produceAmount);
					ctx.onProduceResource('SILVER', cfg.produceAmount, this.x);
				}
			}
		}
	}

	private updateBuilder(dt: number, ctx: VillagerUpdateContext): void {
		const gs = GameState.instance;
		const eastBreached = gs.eastGateHp <= 0 || (ctx.phase === 'NIGHT' && gs.eastGateOpen);
		const maxSafeX = eastBreached ? GameConfig.MAP_LANDMARKS.INNER_GATE.x : GameConfig.MAP_LANDMARKS.EAST_GATE.x;

		// 查找受损建筑
		let repairTargetX: number | undefined = undefined;
		let repairKind: 'EAST' | 'INNER' | 'HALL' | 'TOWER' | undefined = undefined;
		let repairTowerIdx = -1;

		if (!eastBreached && gs.eastGateHp < gs.eastGateMaxHp) {
			repairTargetX = GameConfig.MAP_LANDMARKS.EAST_GATE.x - 20;
			repairKind = 'EAST';
		} else if (gs.innerGateHp < gs.innerGateMaxHp) {
			repairTargetX = GameConfig.MAP_LANDMARKS.INNER_GATE.x - 20;
			repairKind = 'INNER';
		} else if (gs.ancestralHallHp < gs.ancestralHallMaxHp) {
			repairTargetX = GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x + 20;
			repairKind = 'HALL';
		} else {
			for (let i = 0; i < gs.towers.length; i++) {
				const t = gs.towers[i];
				if (t.unlocked && t.x <= maxSafeX && t.hp < t.maxHp) {
					repairTargetX = t.x;
					repairKind = 'TOWER';
					repairTowerIdx = i;
					break;
				}
			}
		}

		if (repairTargetX !== undefined && repairKind !== undefined) {
			if (this.moveToward(repairTargetX, dt)) {
				const rate = GameConfig.ROLES.BUILDER.repairPerSec;
				this.repairAccum += rate * dt;
				if (this.repairAccum >= 5) {
					const heal = Math.floor(this.repairAccum);
					this.repairAccum -= heal;
					if (repairKind === 'EAST') {
						gs.eastGateHp = Math.min(gs.eastGateMaxHp, gs.eastGateHp + heal);
					} else if (repairKind === 'INNER') {
						gs.innerGateHp = Math.min(gs.innerGateMaxHp, gs.innerGateHp + heal);
					} else if (repairKind === 'HALL') {
						gs.ancestralHallHp = Math.min(gs.ancestralHallMaxHp, gs.ancestralHallHp + heal);
					} else if (repairKind === 'TOWER' && repairTowerIdx >= 0) {
						const t = gs.towers[repairTowerIdx];
						t.hp = Math.min(t.maxHp, t.hp + heal);
					}
					ctx.onRepairBuilding(heal, this.x);
				}
			}
			return;
		}

		// 默认在内城作坊巡逻
		const patrolX = GameConfig.MAP_LANDMARKS.INNER_GATE.x - 40 + ((this.id % 3) - 1) * 25;
		this.moveToward(patrolX, dt);
	}

	private updateCombat(dt: number, ctx: VillagerUpdateContext): void {
		const cfg = GameConfig.ROLES[this.role];
		const gs = GameState.instance;

		// 寻找最近敌人
		let nearestEnemy: Enemy | undefined = undefined;
		let bestDist = Infinity;
		for (const e of ctx.enemies) {
			if (e.dead) continue;
			const d = Math.abs(e.x - this.x);
			if (d < bestDist) {
				bestDist = d;
				nearestEnemy = e;
			}
		}

		// 若敌人在防线内或攻击范围内，迎敌交锋
		const canEngage =
			nearestEnemy !== undefined &&
			(bestDist <= cfg.attackRange || nearestEnemy.x <= GameConfig.SAFE_LINE_X + 60);

		if (canEngage && nearestEnemy) {
			if (bestDist > cfg.attackRange) {
				this.moveToward(nearestEnemy.x, dt);
			} else if (this.attackTimer <= 0) {
				// 攻速计算：断粮减半，忠义光环 +30%
				let speedMult = 1.0;
				if (gs.isLowFood) speedMult *= 0.5;
				if (ctx.playerInAura(this.x)) speedMult *= 1 + GameConfig.PLAYER.auraAttackSpeedBonus;

				this.attackTimer = cfg.attackInterval / speedMult;
				this.attackCount++;

				const dir = nearestEnemy.x >= this.x ? 1 : -1;
				nearestEnemy.takeDamage(cfg.attackDamage, dir * 12);

				// 王家拳武师每3次攻击触发范围震击并回血
				if (this.role === 'KUNG_FU' && this.attackCount % 3 === 0) {
					this.shockwaveTimer = 0.25;
					for (const e of ctx.enemies) {
						if (!e.dead && e !== nearestEnemy && Math.abs(e.x - this.x) <= 95) {
							e.takeDamage(Math.round(cfg.attackDamage * 0.75), dir * 24);
						}
					}
					this.hp = Math.min(this.maxHp, this.hp + 15);
					this.refreshVisual();
				}
			}
			return;
		}

		// 无近敌时：白天巡逻校场，夜晚驻守当前最前线
		const targetX =
			ctx.phase === 'DAY'
				? GameConfig.MAP_LANDMARKS.MAIN_WALL.x + ((this.id % 5) - 2) * 26
				: gs.getFrontDefenseX() + ((this.id % 5) - 2) * 16;
		this.moveToward(targetX, dt);
	}
}
