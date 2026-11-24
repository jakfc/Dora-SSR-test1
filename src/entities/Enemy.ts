import { Color, DrawNode, Label, Node, Sprite, Vec2 } from 'Dora';
import { EnemyType, GameConfig } from 'src/config/GameConfig';
import { GameState } from 'src/config/GameState';
import { Villager } from 'src/entities/Villager';
import { artInto, artStretch } from 'src/config/Assets';

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
	public readonly node: Node.Type;
	private readonly bodyDraw: DrawNode.Type;
	private readonly nameLabel: Label.Type;
	private readonly artNode: Node.Type;
	private readonly barBgArt: Sprite.Type | undefined;

	public x: number;
	public hp: number;
	public maxHp: number;
	public dead = false;
	private attackTimer = 0;
	private hitFlashTimer = 0;

	constructor(type: EnemyType, spawnX = GameConfig.SPAWN_X) {
		this.type = type;
		this.x = spawnX;
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
		// 有美术素材时用精灵替掉方块倭寇
		if (artInto(this.artNode, `enemy_${this.type}`) === undefined) {
			drawRect(this.bodyDraw, -hw, 0, cfg.width, cfg.height, fill, 0xff1a202c);
			// 倭刀朝左指示
			drawRect(this.bodyDraw, -hw - 16, cfg.height * 0.45, 16, 4, 0xffe2e8f0);
		}
		// 血条（有底框素材时只画填充，底框由 e10 提供）
		const pct = Math.max(0, this.hp / this.maxHp);
		if (this.barBgArt === undefined) {
			drawRect(this.bodyDraw, -hw - 4, cfg.height + 5, cfg.width + 8, 5, 0xff2d3748);
		}
		drawRect(this.bodyDraw, -hw - 4, cfg.height + 5, (cfg.width + 8) * pct, 5, 0xffe53e3e);
	}

	public takeDamage(amount: number, knockbackX = 0): void {
		if (this.dead) return;
		this.hp -= amount;
		this.hitFlashTimer = 0.1;
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
			this.node.removeFromParent();
			return;
		}
		this.refreshVisual();
	}

	public update(dt: number, villagers: Villager[]): void {
		if (this.dead) return;

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

		// 2. 检查是否被东门阻挡（关闭且有耐久）
		const eastGateX = GameConfig.MAP_LANDMARKS.EAST_GATE.x;
		if (!gs.eastGateOpen && gs.eastGateHp > 0 && this.x >= eastGateX) {
			if (this.x - eastGateX <= cfg.attackRange + 24) {
				if (this.attackTimer <= 0) {
					this.attackTimer = cfg.attackInterval;
					gs.eastGateHp = Math.max(0, gs.eastGateHp - cfg.attackDamage);
				}
				return;
			}
		}

		// 3. 检查是否被内城水门阻挡
		const innerGateX = GameConfig.MAP_LANDMARKS.INNER_GATE.x;
		if (gs.innerGateHp > 0 && this.x >= innerGateX) {
			if (this.x - innerGateX <= cfg.attackRange + 20) {
				if (this.attackTimer <= 0) {
					this.attackTimer = cfg.attackInterval;
					gs.innerGateHp = Math.max(0, gs.innerGateHp - cfg.attackDamage);
				}
				return;
			}
		}

		// 4. 攻击王氏宗祠
		const hallX = GameConfig.MAP_LANDMARKS.ANCESTRAL_HALL.x;
		if (this.x - hallX <= cfg.attackRange + 36) {
			if (this.attackTimer <= 0) {
				this.attackTimer = cfg.attackInterval;
				gs.ancestralHallHp = Math.max(0, gs.ancestralHallHp - cfg.attackDamage);
			}
			return;
		}

		// 向左推进
		this.x = Math.max(hallX, this.x - cfg.moveSpeed * dt);
		this.node.x = this.x;
	}
}
