import { Color, DrawNode, Label, Node, Vec2 } from 'Dora';
import { GameConfig, VillagerRole } from 'src/config/GameConfig';
import { GameState, BuildProject } from 'src/config/GameState';
import { Enemy } from 'src/entities/Enemy';
import { animAccByMove, animAccByTime, animFrameOf, artAnimCount, artAnimFace, artAnimInto, artHide, artReady } from 'src/config/Assets';
import { soundSfx } from 'src/audio/Sound';

export interface ToolDrop {
	id: number;
	x: number;
	role: VillagerRole;
	claimed: boolean;
	node: Node.Type;
}

export interface VillagerUpdateContext {
	phase: 'DAY' | 'NIGHT';
	dayTimer: number;
	enemies: Enemy[];
	tools: ToolDrop[];
	projects: BuildProject[];
	playerInAura: (x: number) => boolean;
	onProduceResource: (kind: 'FOOD' | 'SILVER', amount: number, x: number) => void;
	onRepairBuilding: (amount: number, x: number) => void;
	onSaltGathered: (x: number) => void;
	onCargoDropped: (x: number) => void;
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
	/** 灶户是否已经背着一擔盐（负盐跑得慢，路上被截会丢担） */
	public carrying = false;

	private wanderTargetX: number;
	private rallyTargetX: number | undefined = undefined;
	private rallyTimer = 0;
	private saltTimer = 0;

	private produceTimer = 0;
	private attackTimer = 0;
	private attackCount = 0;
	private repairAccum = 0;
	private shockwaveTimer = 0;

	// 逐帧动画状态
	private animName = '';
	private animAcc = 0;
	private animPrevX: number;
	/** 朝向：+1 向右，-1 向左。由实际位移推出，走路时转身 */
	private facing = 1;

	constructor(startX: number, role: VillagerRole = 'IDLE') {
		this.id = Villager.nextId++;
		this.x = startX;
		this.animPrevX = startX;
		this.wanderTargetX = startX;
		const cfg = GameConfig.ROLES[role];
		this.role = role;
		// 宗祠士气：每级 +8% 气血上限，新丁生来就带
		const hpScale = 1 + GameState.instance.moraleHpBonus;
		this.maxHp = Math.round(cfg.maxHp * hpScale);
		this.hp = this.maxHp;

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
		this.maxHp = Math.round(cfg.maxHp * (1 + GameState.instance.moraleHpBonus));
		this.hp = Math.max(20, Math.round(this.maxHp * ratio));
		this.produceTimer = 0;
		this.attackTimer = 0;
		this.attackCount = 0;
		this.carrying = false;
		this.saltTimer = 0;
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
			soundSfx('enemy_die');
			this.node.removeFromParent();
			return;
		}
		soundSfx('hurt');
		this.refreshVisual();
	}

	public refreshVisual(): void {
		const cfg = GameConfig.ROLES[this.role];
		this.bodyDraw.clear();
		// 有美术素材时按职业换精灵
		// 有美术素材（静态单帧或逐帧动画）时用精灵替掉程序化方块
		const hasArt =
			artReady(`villager_${this.role}`) ||
			artAnimCount(`villager_${this.role}`, `villager_${this.role.toLowerCase()}`) > 0;
		if (!hasArt) {
			// 躯干
			drawRect(this.bodyDraw, -11, 0, 22, 40, cfg.color, 0xff1a202c);
			// 头部
			drawRect(this.bodyDraw, -7, 40, 14, 12, 0xfffbd38d);
		}
		// 背上的一擔盐（灶户负盐状态）
		if (this.carrying) {
			drawRect(this.bodyDraw, -19, 24, 13, 15, 0xffe2e8f0, 0xff4a5568);
			drawRect(this.bodyDraw, -19, 37, 13, 3, 0xffd6b36a);
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
		this.roleLabel.text = this.carrying ? '灶户·负盐' : cfg.name;
		this.roleLabel.textWidth = 150; // 不设宽度会被裁成半截字
		this.roleLabel.color = Color(this.carrying ? 0xfff6e05e : 0xffe2e8f0);
	}

	/** 每帧推进角色动画：按当前动作挑前缀，缺帧时逐级回退。 */
	private tickAnim(dt: number): void {
		const dx = this.x - this.animPrevX;
		const moving = Math.abs(dx) > 0.5;
		if (moving) this.facing = dx > 0 ? 1 : -1;
		this.animPrevX = this.x;
		let name = 'idle';
		if (this.attackTimer > 0) name = 'attack';
		else if (moving) name = 'walk';
		else if (
			this.carrying ||
			this.role === 'FARMER' ||
			this.role === 'SALT_WORKER' ||
			this.role === 'BUILDER'
		) {
			name = 'work';
		}

		const styleId = `villager_${this.role}`;
		const base = `villager_${this.role.toLowerCase()}`;
		// 站立帧的命名是 `villager_<role>_NN.png`（不带动作词），移动/劳作才是 `_walk` / `_work`
		let prefix = name === 'idle' ? base : `${base}_${name}`;
		let frames = artAnimCount(styleId, prefix);
		if (frames === 0 && name !== 'walk' && name !== 'work') {
			// 先退到劳作帧（静止的劳作帧比走路帧安静得多）
			prefix = `${base}_work`;
			frames = artAnimCount(styleId, prefix);
		}
		if (frames === 0 && name !== 'walk') {
			// 该动作没有专属帧：退到走路帧，好歹还在动
			prefix = `${base}_walk`;
			frames = artAnimCount(styleId, prefix);
		}
		if (frames === 0) {
			// 连走路帧也没有：退回静态单帧
			prefix = base;
			frames = artAnimCount(styleId, prefix);
		}
		if (frames === 0) {
			artHide(this.artNode);
			return;
		}
		// 换动作就把推进量归零：出拳/劳作一定从第 1 帧起，不从半截插入
		if (this.animName !== name) {
			this.animName = name;
			this.animAcc = 0;
		}
		const animDt = dt * GameConfig.ANIM_TIME_SCALE;
		// 走路按实际走过的距离推进（脚步跟地，不打滑）；其余按该动作的整轮时长推进
		this.animAcc =
			name === 'walk'
				? animAccByMove(this.animAcc, frames, Math.abs(dx))
				: animAccByTime(name, this.animAcc, frames, animDt);
		// 站立/劳作时把帧错开（用 id），免得一村人同手同脚
		const idleOffset = name === 'walk' || name === 'attack' ? 0 : this.id % Math.max(1, frames);
		artAnimInto(this.artNode, styleId, prefix, animFrameOf(name, this.animAcc, frames) + idleOffset);
		// 村民也要转身：以前这里的挂点从不镜像，向左走的人一直倒着走
		artAnimFace(this.artNode, styleId, this.facing < 0);
	}

	private moveToward(targetX: number, dt: number, speedScale = 1): boolean {
		const speed = GameConfig.ROLES[this.role].moveSpeed * speedScale;
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

		this.tickAnim(dt);

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
				this.updateFarmer(dt, ctx);
				break;
			case 'SALT_WORKER':
				this.updateSaltWorker(dt, ctx);
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

	private updateFarmer(dt: number, ctx: VillagerUpdateContext): void {
		if (ctx.phase === 'NIGHT') {
			const shelterX = GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x + ((this.id % 5) - 2) * 20;
			this.moveToward(shelterX, dt, GameConfig.SALT_FETCH.panicSpeedScale);
			return;
		}

		// 东西各一片水田，按 id 分派；只有开垦过的田才出粮，荒地先回宗祠等待
		const paddyId = this.id % 2 === 0 ? 'WEST_PADDY' : 'EAST_PADDY';
		const paddy = GameConfig.MAP_LANDMARKS[paddyId];
		if (!GameState.instance.isLandReady(paddyId)) {
			const idleX = GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x + ((this.id % 5) - 2) * 20;
			this.moveToward(idleX, dt);
			return;
		}
		const bonus = GameState.instance.landLevelOf(paddyId) * GameConfig.RECLAIM.PADDY_YIELD_PER_LEVEL;

		const workX = paddy.x + ((this.id % 5) - 2) * 22;
		if (this.moveToward(workX, dt)) {
			const cfg = GameConfig.ROLES.FARMER;
			this.produceTimer += dt;
			if (this.produceTimer >= cfg.produceInterval) {
				this.produceTimer -= cfg.produceInterval;
				GameState.instance.addFood(cfg.produceAmount + bonus);
				soundSfx('farm_hoe');
				ctx.onProduceResource('FOOD', cfg.produceAmount + bonus, this.x);
			}
		}
	}

	/**
	 * 灶户取盐：出城到盐田装盐 -> 背盐回盐课司入库（一趟 120 银）。
	 * 负盐跑得慢，黄昏/入夜自动往回赶；赶不回来就会死在城外，盐担也会失落。
	 */
	private updateSaltWorker(dt: number, ctx: VillagerUpdateContext): void {
		const cfg = GameConfig.ROLES.SALT_WORKER;
		const hallX = GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x + ((this.id % 5) - 2) * 20;
		const officeX = GameConfig.MAP_LANDMARKS.SALT_OFFICE.x + ((this.id % 5) - 2) * 24;
		// 按 id 分派东西两片盐田；未开垦的盐田出不了盐
		const yardId = this.id % 2 === 0 ? 'WEST_SALT_FLAT' : 'EAST_SALT_FLAT';
		const yardBaseX = GameConfig.MAP_LANDMARKS[yardId].x;
		const yardX = yardBaseX + ((this.id % 7) - 3) * 90;
		const isNight = ctx.phase === 'NIGHT';
		const yardReady = GameState.instance.isLandReady(yardId);

		// 自己那半边盐田还没开垦：白天空守宗祠，入夜照旧回城避难
		if (!yardReady && !isNight) {
			this.moveToward(hallX, dt);
			return;
		}

		// 入库结算
		const deposit = () => {
			const level = GameState.instance.landLevelOf(yardId);
			const gain =
				GameConfig.SALT_FETCH.tripSilver + level * GameConfig.RECLAIM.SALT_YIELD_PER_LEVEL;
			GameState.instance.addSilver(gain);
			ctx.onProduceResource('SILVER', gain, this.x);
			this.carrying = false;
			this.saltTimer = 0;
			this.refreshVisual();
		};

		if (isNight) {
			// 天黑后往内城狂奔；背着一担盐跑得更慢，近处有倭寇就会弃担逃命
			if (this.carrying) {
				let threat = Infinity;
				for (const e of ctx.enemies) {
					if (e.dead) continue;
					const d = Math.abs(e.x - this.x);
					if (d < threat) threat = d;
				}
				if (threat < GameConfig.SALT_FETCH.dropSaltThreatRange) {
					this.carrying = false;
					this.refreshVisual();
					ctx.onCargoDropped(this.x);
				}
			}
			const fleeScale =
				GameConfig.SALT_FETCH.panicSpeedScale *
				(this.carrying ? GameConfig.SALT_FETCH.carrySpeedScale : 1);
			if (this.moveToward(hallX, dt, fleeScale) && this.carrying) {
				deposit();
			}
			return;
		}

		if (this.carrying) {
			if (this.moveToward(officeX, dt, GameConfig.SALT_FETCH.carrySpeedScale)) {
				deposit();
			}
			return;
		}

		// 掂量一下来回脚程：只留 25% 余量就敢再跑一趟（撑不住就会被天黑吃掉）
		const tripTime =
			(Math.abs(yardX - officeX) * 2) / cfg.moveSpeed + GameConfig.SALT_FETCH.gatherSeconds;
		if (ctx.dayTimer <= tripTime * 0.75) {
			this.moveToward(officeX, dt);
			return;
		}

		if (this.moveToward(yardX, dt)) {
			this.saltTimer += dt;
			if (this.saltTimer >= GameConfig.SALT_FETCH.gatherSeconds) {
				this.saltTimer = 0;
				this.carrying = true;
				soundSfx('farm_hoe');
				this.refreshVisual();
				ctx.onSaltGathered(this.x);
			}
		}
	}

	private updateBuilder(dt: number, ctx: VillagerUpdateContext): void {
		const gs = GameState.instance;
		const eastGateX = GameConfig.MAP_LANDMARKS.EAST_GATE.x;

		// 0. 有在建工程时优先赶去工地（进度由主循环按在场工匠数推进）
		let site: BuildProject | undefined = undefined;
		let siteDist = Infinity;
		for (const p of ctx.projects) {
			if (ctx.phase === 'NIGHT' && p.x > eastGateX) continue; // 夜里不冒险出城施工
			const d = Math.abs(p.x - this.x);
			if (d < siteDist) {
				siteDist = d;
				site = p;
			}
		}
		if (site !== undefined) {
			this.moveToward(site.x + ((this.id % 3) - 1) * 26, dt);
			return;
		}

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
				// 攻速计算：断粮减半，忠义光环 +30%，宗祠士气每级 +12%
				let speedMult = 1.0;
				if (gs.isLowFood) speedMult *= 0.5;
				if (ctx.playerInAura(this.x)) speedMult *= 1 + GameConfig.PLAYER.auraAttackSpeedBonus;
				speedMult *= 1 + gs.moraleBonus;

				this.attackTimer = cfg.attackInterval / speedMult;
				this.attackCount++;
				soundSfx('sword_slash');

				const dir = nearestEnemy.x >= this.x ? 1 : -1;
				const moraleDmg = 1 + gs.moraleBonus;
				nearestEnemy.takeDamage(Math.round(cfg.attackDamage * moraleDmg), dir * 12);

				// 王家拳武师每3次攻击触发范围震击并回血
				if (this.role === 'KUNG_FU' && this.attackCount % 3 === 0) {
					this.shockwaveTimer = 0.25;
					for (const e of ctx.enemies) {
						if (!e.dead && e !== nearestEnemy && Math.abs(e.x - this.x) <= 95) {
							e.takeDamage(Math.round(cfg.attackDamage * 0.75 * moraleDmg), dir * 24);
						}
					}
					this.hp = Math.min(this.maxHp, this.hp + 15);
					this.refreshVisual();
				}
			}
			return;
		}

		// 无近敌时：白天巡逻校场，夜晚按单双号分守东西两线
		const targetX =
			ctx.phase === 'DAY'
				? GameConfig.MAP_LANDMARKS.MAIN_WALL.x + ((this.id % 5) - 2) * 26
				: (this.id % 2 === 0 ? gs.getWestDefenseX() : gs.getFrontDefenseX()) +
					((this.id % 5) - 2) * 16;
		this.moveToward(targetX, dt);
	}
}
