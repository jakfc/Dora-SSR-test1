import { Color, DrawNode, Label, Node, Vec2 } from 'Dora';
import { GameConfig, LandmarkId } from 'src/config/GameConfig';
import { Enemy } from 'src/entities/Enemy';
import { Villager } from 'src/entities/Villager';
import { artFace, artInto } from 'src/config/Assets';
import { playFx } from 'src/ui/Fx';

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
 * 主角：筑堡总指挥 · 王叔杲
 */
export class Player {
	public readonly node: Node.Type;
	private readonly bodyDraw: DrawNode.Type;
	private readonly fxDraw: DrawNode.Type;
	private readonly nameLabel: Label.Type;
	private readonly artNode: Node.Type;

	public x: number = GameConfig.PLAYER.startX;
	public facing = 1; // 1 = 右, -1 = 左
	public moveTargetX: number | undefined = undefined;

	public attackCooldownTimer = 0;
	public rallyCooldownTimer = 0;
	public auraTimer = 0;
	private slashFxTimer = 0;

	constructor() {
		this.node = Node();
		this.node.x = this.x;
		this.node.y = GameConfig.GROUND_Y;

		this.fxDraw = DrawNode();
		this.node.addChild(this.fxDraw);

		this.bodyDraw = DrawNode();
		this.node.addChild(this.bodyDraw);

		// 美术挂点：位置在方块层之上、姓名牌之下
		this.artNode = Node();
		this.node.addChild(this.artNode);

		this.nameLabel = Label('sarasa-mono-sc-regular', 16) as Label.Type;
		this.nameLabel.text = '王叔杲';
		this.nameLabel.color = Color(0xfffff3c4);
		this.nameLabel.y = 86;
		this.node.addChild(this.nameLabel);

		this.redrawBody();
	}

	private redrawBody(): void {
		this.bodyDraw.clear();
		// 有美术素材时用精灵替掉方块小人，并按朝向镜像
		const art = artInto(this.artNode, 'player_idle');
		if (art !== undefined) {
			artFace(art, 'player_idle', this.facing < 0);
			return;
		}
		// 官袍躯干
		drawRect(this.bodyDraw, -16, 0, 32, 54, GameConfig.PLAYER.color, 0xfffff3c4);
		// 头部与明代乌纱帽
		drawRect(this.bodyDraw, -10, 54, 20, 16, 0xfffbd38d);
		drawRect(this.bodyDraw, -13, 68, 26, 8, 0xff1a202c);
		// 佩剑朝向指示
		const swordX = this.facing > 0 ? 14 : -34;
		drawRect(this.bodyDraw, swordX, 26, 20, 5, 0xffe2e8f0);
	}

	private redrawFx(): void {
		this.fxDraw.clear();
		if (this.auraTimer > 0) {
			// 忠义光环范围提示圆环
			const r = GameConfig.PLAYER.auraRadius;
			const segments = 32;
			for (let i = 0; i < segments; i++) {
				const a1 = (i / segments) * Math.PI * 2;
				const a2 = ((i + 1) / segments) * Math.PI * 2;
				this.fxDraw.drawSegment(
					Vec2(Math.cos(a1) * r, 24 + Math.sin(a1) * 28),
					Vec2(Math.cos(a2) * r, 24 + Math.sin(a2) * 28),
					1.5,
					Color(0x66f6ad55)
				);
			}
		}
		if (this.slashFxTimer > 0) {
			const sx = this.facing > 0 ? 10 : -GameConfig.PLAYER.attackRange;
			drawRect(
				this.fxDraw,
				sx,
				12,
				GameConfig.PLAYER.attackRange - 10,
				40,
				0x88fefcbf,
				0xfff6e05e
			);
		}
	}

	public update(dt: number, moveInput: number): LandmarkId | undefined {
		if (this.attackCooldownTimer > 0) {
			this.attackCooldownTimer = Math.max(0, this.attackCooldownTimer - dt);
		}
		if (this.rallyCooldownTimer > 0) {
			this.rallyCooldownTimer = Math.max(0, this.rallyCooldownTimer - dt);
		}
		if (this.auraTimer > 0) {
			this.auraTimer = Math.max(0, this.auraTimer - dt);
		}
		if (this.slashFxTimer > 0) {
			this.slashFxTimer = Math.max(0, this.slashFxTimer - dt);
		}

		let dir = moveInput;
		if (dir !== 0) {
			this.moveTargetX = undefined;
		} else if (this.moveTargetX !== undefined) {
			const diff = this.moveTargetX - this.x;
			if (Math.abs(diff) <= 8) {
				this.moveTargetX = undefined;
			} else {
				dir = diff > 0 ? 1 : -1;
			}
		}

		if (dir !== 0) {
			const newFacing = dir > 0 ? 1 : -1;
			if (newFacing !== this.facing) {
				this.facing = newFacing;
				this.redrawBody();
			}
			this.x += dir * GameConfig.PLAYER.moveSpeed * dt;
			this.x = Math.max(40, Math.min(GameConfig.MAP_WIDTH - 40, this.x));
		}

		this.node.x = this.x;
		this.redrawFx();
		return this.findNearestLandmark();
	}

	public findNearestLandmark(): LandmarkId | undefined {
		let bestId: LandmarkId | undefined = undefined;
		let bestDist = GameConfig.PLAYER.interactRange;
		const landmarks = GameConfig.MAP_LANDMARKS;
		const keys = Object.keys(landmarks) as LandmarkId[];
		for (const key of keys) {
			if (key === 'DALUO_MOUNTAIN' || key === 'COAST_SPAWN' || key === 'OUTER_SALT_FLAT') {
				continue;
			}
			const lm = landmarks[key];
			const dist = Math.abs(this.x - lm.x);
			if (dist <= bestDist) {
				bestDist = dist;
				bestId = key;
			}
		}
		return bestId;
	}

	/**
	 * J 键 / 攻击按钮：王家拳 · 麒麟步
	 */
	public triggerQilinStep(enemies: Enemy[]): { triggered: boolean; hitCount: number } {
		if (this.attackCooldownTimer > 0) {
			return { triggered: false, hitCount: 0 };
		}

		this.attackCooldownTimer = GameConfig.PLAYER.attackCooldown;
		this.auraTimer = GameConfig.PLAYER.auraDuration;
		this.slashFxTimer = 0.22;
		this.moveTargetX = undefined;
		// 刀光：贴在身体前方，朝左时自动镜像
		playFx(
			this.node.parent,
			'fx_slash',
			this.x + this.facing * 46,
			GameConfig.GROUND_Y + 52,
			0.26,
			0.35,
			0,
			this.facing < 0
		);

		const oldX = this.x;
		this.x = Math.max(
			40,
			Math.min(GameConfig.MAP_WIDTH - 40, this.x + this.facing * GameConfig.PLAYER.dashDistance)
		);
		this.node.x = this.x;

		let hitCount = 0;
		for (const enemy of enemies) {
			if (enemy.dead) continue;
			const dx = enemy.x - oldX;
			const inFront = this.facing > 0 ? dx >= -20 && dx <= GameConfig.PLAYER.attackRange + 50 : dx <= 20 && dx >= -(GameConfig.PLAYER.attackRange + 50);
			const nearEnd = Math.abs(enemy.x - this.x) <= GameConfig.PLAYER.attackRange;
			if (inFront || nearEnd) {
				enemy.takeDamage(
					GameConfig.PLAYER.attackDamage,
					this.facing * GameConfig.PLAYER.knockbackDistance
				);
				hitCount++;
			}
		}

		this.redrawFx();
		return { triggered: true, hitCount };
	}

	/**
	 * K 键 / 号令按钮：鸣鼓集结
	 */
	public triggerRally(villagers: Villager[]): { triggered: boolean; recalledCount: number } {
		if (this.rallyCooldownTimer > 0) {
			return { triggered: false, recalledCount: 0 };
		}
		this.rallyCooldownTimer = GameConfig.PLAYER.rallyCooldown;
		let recalledCount = 0;

		for (const v of villagers) {
			if (v.dead) continue;
			if (v.x > GameConfig.MAP_LANDMARKS.EAST_GATE.x) {
				// 城外的族人：直接召回内城水门之内的安全区（盐田/海岸很远，得跑一阵）
				v.orderRally(
					GameConfig.MAP_LANDMARKS.INNER_GATE.x - 60 + ((v.id % 5) - 2) * 22,
					8.0
				);
				recalledCount++;
			} else if (v.role === 'MILITIA' || v.role === 'KUNG_FU') {
				v.orderRally(this.x, 3.0);
				recalledCount++;
			}
		}
		return { triggered: true, recalledCount };
	}

	public isInAura(targetX: number): boolean {
		return this.auraTimer > 0 && Math.abs(targetX - this.x) <= GameConfig.PLAYER.auraRadius;
	}
}
