import { Color, DrawNode, Label, Node, Sprite, Vec2 } from 'Dora';
import { EnemyType, GameConfig } from 'src/config/GameConfig';
import { GameState } from 'src/config/GameState';
import { Villager } from 'src/entities/Villager';
import { ANIM_FPS, artAnimCount, artAnimInto, artHide, artReady, artStretch } from 'src/config/Assets';
import { soundSfx } from 'src/audio/Sound';

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
 * 倭寇敌人实体
 */
export class Enemy {
	public readonly type: EnemyType;
	/** 登岸方向：'E' 从东海（右）上岸向左推进，'W' 从西湾（左）上岸向右推进 */
	public readonly side: 'W' | 'E';
	/** 推进方向（-1 向左，+1 向右），登岸点到宗祠的方向 */
	public readonly dir: number;
	public readonly node: Node.Type;
	private readonly bodyDraw: DrawNode.Type;
	private readonly nameLabel: Label.Type;
	private readonly artNode: Node.Type;
	private readonly barBgArt: Sprite.Type | undefined;

	public x: number;
	public hp: number;
	public maxHp: number;
	public dead = false;
	/** 收了银子退兵（走到海边自行退场，不计击杀） */
	public bribed = false;
	/** 已退场（被撁退而不算阵亡） */
	public escaped = false;
	/** 阵亡倒地动画剩余时间（>0 时尸体留在场上，倒完才移除） */
	public dying = 0;
	private bribeStunTimer = 0;
	private attackTimer = 0;
	private hitFlashTimer = 0;
	private animClock = 0;
	private animPrevX: number;

	constructor(type: EnemyType, spawnX = GameConfig.SPAWN_EAST_X, side: 'W' | 'E' = 'E') {
		this.type = type;
		this.side = side;
		this.dir = side === 'E' ? -1 : 1;
		this.x = spawnX;
		this.animPrevX = spawnX;
		const cfg = GameConfig.ENEMIES[type];
		this.maxHp = cfg.maxHp;
		this.hp = cfg.maxHp;

		this.node = Node();
		this.node.x = this.x;
		this.node.y = GameConfig.GROUND_Y;

		this.bodyDraw = DrawNode();
		this.node.addChild(this.bodyDraw);

		// 美术挂点：位于方块层之上、名字之下
		this.artNode = Node();
		this.node.addChild(this.artNode);

		// 血条底框（e10 是空心边框，内部透明，程序化填色从后面透出来）
		const barW = cfg.width + 12;
		const barBg = artStretch('ui_bar_empty', barW, 10);
		if (barBg !== undefined) {
			barBg.anchor = Vec2(0, 0);
			barBg.x = -barW / 2;
			barBg.y = cfg.height + 3;
			this.node.addChild(barBg);
		}
		this.barBgArt = barBg;

		this.nameLabel = Label('sarasa-mono-sc-regular', type === 'BOSS' ? 16 : 12) as Label.Type;
		this.nameLabel.text = type === 'SCOUT' ? '倭探' : cfg.name;
		this.nameLabel.color = Color(type === 'BOSS' ? 0xfffeb2b2 : 0xffe2e8f0);
		this.nameLabel.y = cfg.height + 16;
		this.node.addChild(this.nameLabel);

		this.refreshVisual();
	}

	private refreshVisual(): void {
		const cfg = GameConfig.ENEMIES[this.type];
		const hw = cfg.width / 2;
		const fill = this.hitFlashTimer > 0 ? 0xffffffff : cfg.color;
		this.bodyDraw.clear();
		// 有美术素材（静态单帧或逐帧动画）时用精灵替掉方块倭寇
		const hasArt = artReady(`enemy_${this.type}`) || artAnimCount(`enemy_${this.type}`, `enemy_${this.type.toLowerCase()}`) > 0;
		if (!hasArt) {
			drawRect(this.bodyDraw, -hw, 0, cfg.width, cfg.height, fill, 0xff1a202c);
			// 倭刀指向目标：东面来敌朝左、西面来敌朝右
			if (this.dir === 1) {
				drawRect(this.bodyDraw, hw, cfg.height * 0.45, 16, 4, 0xffe2e8f0);
			} else {
				drawRect(this.bodyDraw, -hw - 16, cfg.height * 0.45, 16, 4, 0xffe2e8f0);
			}
		}
		// 血条（有底框素材时只画填充，底框由 e10 提供）
		const pct = Math.max(0, this.hp / this.maxHp);
		// 收银退兵的倭寇：名字变色，血条转成金色（不再流血）
		const baseName = this.type === 'SCOUT' ? '倭探' : cfg.name;
		if (this.bribed) {
			this.nameLabel.text = `${baseName}·收银退兵`;
			this.nameLabel.color = Color(0xfff6e05e);
		} else {
			this.nameLabel.text = baseName;
			this.nameLabel.color = Color(this.type === 'BOSS' ? 0xfffeb2b2 : 0xffe2e8f0);
		}
		if (this.barBgArt === undefined) {
			drawRect(this.bodyDraw, -hw - 4, cfg.height + 5, cfg.width + 8, 5, 0xff2d3748);
		}
		drawRect(this.bodyDraw, -hw - 4, cfg.height + 5, (cfg.width + 8) * pct, 5, this.bribed ? 0xfff6e05e : 0xffe53e3e);
	}

	public takeDamage(amount: number, knockbackX = 0): void {
		if (this.dead) return;
		this.hp -= amount;
		this.hitFlashTimer = 0.1;
		soundSfx('hurt');
		if (knockbackX !== 0) {
			this.x = Math.min(GameConfig.MAP_WIDTH - 40, this.x + knockbackX);
			this.node.x = this.x;
		}
		if (this.hp <= 0) {
			this.hp = 0;
			this.dead = true;
			const cfg = GameConfig.ENEMIES[this.type];
			GameState.instance.addSilver(cfg.rewardSilver);
			GameState.instance.totalKills++;
			this.dying = 0.7;
			soundSfx('enemy_die');
			this.tickAnim(0);
			return;
		}
		this.refreshVisual();
	}

	/** 撁银买命：倭寇收钱掉头，头目收钱也只能被撁住一阵 */
	public bribe(): void {
		if (this.dead || this.bribed) return;
		this.bribed = true;
		if (this.type === 'BOSS') {
			this.bribeStunTimer = GameConfig.BRIBE_BOSS_STUN_SECONDS;
		} else {
			this.bribeStunTimer = 0;
		}
		this.refreshVisual();
	}

	/** 每帧推进倭寇动画；阵亡后只倒在地上，倒完自行退场。 */
	private tickAnim(dt: number): void {
		const styleId = `enemy_${this.type}`;
		const base = `enemy_${this.type.toLowerCase()}`;
		let name = 'idle';
		if (this.dead) {
			name = 'fall';
		} else if (this.attackTimer > 0) {
			name = 'attack';
		} else if (Math.abs(this.x - this.animPrevX) > 0.5) {
			name = 'walk';
		}
		this.animPrevX = this.x;

		// 站立帧的命名是 `enemy_<type>_NN.png`（不带动作词），移动/出手/倒地才是 `_walk` / `_attack` / `_fall`
		let prefix = name === 'idle' ? base : `${base}_${name}`;
		let frames = artAnimCount(styleId, prefix);
		if (frames === 0 && name !== 'walk') {
			prefix = `${base}_walk`;
			frames = artAnimCount(styleId, prefix);
		}
		if (frames === 0) {
			prefix = base;
			frames = artAnimCount(styleId, prefix);
		}
		if (frames === 0) {
			artHide(this.artNode);
			return;
		}
		// 动画时钟不走 GAME_SPEED 的减速，和族丁/主角一致，保持步伐颚率
		this.animClock += dt * GameConfig.ANIM_TIME_SCALE;
		const fps = ANIM_FPS[name] !== undefined ? ANIM_FPS[name] : 6;
		artAnimInto(this.artNode, styleId, prefix, this.animClock * fps);
		// 逐帧图默认朝左；西面来敌整体镜像
		this.artNode.scaleX = this.dir === 1 ? -1 : 1;
	}

	public update(dt: number, villagers: Villager[]): void {
		// 阵亡：只播倒地动画，倒完移除节点（敌人已从战斗逻辑中除名）
		if (this.dead) {
			if (this.dying > 0) {
				this.dying = Math.max(0, this.dying - dt);
				this.tickAnim(dt);
				if (this.dying === 0) this.node.removeFromParent();
			}
			return;
		}
		if (this.escaped) return;

		this.tickAnim(dt);

		// 0. 收了银子就跑：头目只被撁住一阵，小兵直接掉头滚回海边
		if (this.bribed) {
			const cfg0 = GameConfig.ENEMIES[this.type];
			if (this.type === 'BOSS') {
				this.bribeStunTimer = Math.max(0, this.bribeStunTimer - dt);
				if (this.bribeStunTimer > 0) return;
				this.bribed = false;
				this.refreshVisual();
			} else {
				// 收银后退回自己登岸的那一头
				this.x += -this.dir * cfg0.moveSpeed * 1.3 * dt;
				this.node.x = this.x;
				if (this.x >= GameConfig.MAP_WIDTH - 130 || this.x <= 130) {
					this.escaped = true;
					this.node.removeFromParent();
				}
				return;
			}
		}

		if (this.attackTimer > 0) this.attackTimer = Math.max(0, this.attackTimer - dt);
		if (this.hitFlashTimer > 0) {
			this.hitFlashTimer = Math.max(0, this.hitFlashTimer - dt);
			if (this.hitFlashTimer === 0) this.refreshVisual();
		}

		const cfg = GameConfig.ENEMIES[this.type];
		const gs = GameState.instance;

		// 1. 优先检查攻击范围内的我方族丁
		let targetVillager: Villager | undefined = undefined;
		let bestDist = cfg.attackRange;
		for (const v of villagers) {
			if (v.dead) continue;
			const d = Math.abs(v.x - this.x);
			if (d <= bestDist) {
				bestDist = d;
				targetVillager = v;
			}
		}

		if (targetVillager) {
			if (this.attackTimer <= 0) {
				this.attackTimer = cfg.attackInterval;
				targetVillager.takeDamage(cfg.attackDamage);
			}
			return;
		}

		// 1.5 夜袭猎杀：天黑后主动追杀滞留在城外的族丁（玩家可用 [K] 鸣鼓召回或派兵救援）
		if (gs.phase === 'NIGHT') {
			const wallX =
				this.side === 'E'
					? GameConfig.MAP_LANDMARKS.EAST_GATE.x
					: GameConfig.MAP_LANDMARKS.INNER_GATE.x;
			let straggler: Villager | undefined = undefined;
			let huntDist = GameConfig.ENEMY_HUNT_RANGE;
			for (const v of villagers) {
				if (v.dead) continue;
				// 只猎杀自己这一侧城外的人
				const outside = this.side === 'E' ? v.x > wallX : v.x < wallX;
				if (!outside) continue;
				const d = Math.abs(v.x - this.x);
				if (d <= huntDist) {
					huntDist = d;
					straggler = v;
				}
			}
			if (straggler !== undefined) {
				if (huntDist <= cfg.attackRange) {
					if (this.attackTimer <= 0) {
						this.attackTimer = cfg.attackInterval;
						straggler.takeDamage(cfg.attackDamage);
					}
				} else {
					const dir = straggler.x > this.x ? 1 : -1;
					this.x += dir * cfg.moveSpeed * GameConfig.ENEMY_HUNT_SPEED_SCALE * dt;
					this.node.x = this.x;
				}
				return;
			}
		}

		// 2. 东面来敌：先叩东门（闭门且完好时）
		const eastGateX = GameConfig.MAP_LANDMARKS.EAST_GATE.x;
		if (this.side === 'E' && !gs.eastGateOpen && gs.eastGateHp > 0 && this.x >= eastGateX) {
			if (this.x - eastGateX <= cfg.attackRange + 24) {
				if (this.attackTimer <= 0) {
					this.attackTimer = cfg.attackInterval;
					gs.eastGateHp = Math.max(0, gs.eastGateHp - cfg.attackDamage);
				}
				return;
			}
		}

		// 3. 两路来敌都要先破内城水门（西面来敌从西侧凿门）
		const innerGateX = GameConfig.MAP_LANDMARKS.INNER_GATE.x;
		if (gs.innerGateHp > 0) {
			const reached = this.side === 'E' ? this.x >= innerGateX : this.x <= innerGateX;
			if (reached && Math.abs(this.x - innerGateX) <= cfg.attackRange + 20) {
				if (this.attackTimer <= 0) {
					this.attackTimer = cfg.attackInterval;
					gs.innerGateHp = Math.max(0, gs.innerGateHp - cfg.attackDamage);
				}
				return;
			}
		}

		// 4. 攻击王氏宗祠（两端来敌都得先打到城中）
		const hallX = GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x;
		if (Math.abs(this.x - hallX) <= cfg.attackRange + 36) {
			if (this.attackTimer <= 0) {
				this.attackTimer = cfg.attackInterval;
				gs.ancestralHallHp = Math.max(0, gs.ancestralHallHp - cfg.attackDamage);
			}
			return;
		}

		// 朝宗祠推进（东面来敌向左，西面来敌向右）
		this.x =
			this.side === 'E'
				? Math.max(hallX, this.x - cfg.moveSpeed * dt)
				: Math.min(hallX, this.x + cfg.moveSpeed * dt);
		this.node.x = this.x;
	}
}
