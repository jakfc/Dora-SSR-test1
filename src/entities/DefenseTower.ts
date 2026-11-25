import { Color, DrawNode, Label, Node, Vec2 } from 'Dora';
import { GameConfig } from 'src/config/GameConfig';
import { GameState, TowerState } from 'src/config/GameState';
import { Enemy } from 'src/entities/Enemy';
import { artHide, artInto, artSprite } from 'src/config/Assets';
import { playFx } from 'src/ui/Fx';

interface Projectile {
	x: number;
	y: number;
	targetX: number;
	speed: number;
	elapsed: number;
	duration: number;
	startX: number;
	startY: number;
	damage: number;
	splashRadius: number;
	isCannon: boolean;
	/** 有美术素材时该弹道的精灵节点（否则回退到 DrawNode 绘制）。 */
	art: Node.Type | undefined;
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
		draw.drawPolygon(verts, Color(fillColor), 1.5, Color(borderColor));
	} else {
		draw.drawPolygon(verts, Color(fillColor));
	}
}

/**
 * 敌台箭楼 / 佛郎机炮台
 */
export class DefenseTower {
	public readonly state: TowerState;
	public readonly node: Node.Type;
	private readonly bodyDraw: DrawNode.Type;
	private readonly projDraw: DrawNode.Type;
	private readonly titleLabel: Label.Type;
	private readonly artNode: Node.Type;

	private cooldownTimer = 0;
	private projectiles: Projectile[] = [];

	constructor(state: TowerState) {
		this.state = state;

		this.node = Node();
		this.node.x = state.x;
		this.node.y = GameConfig.GROUND_Y;

		this.bodyDraw = DrawNode();
		this.node.addChild(this.bodyDraw);

		// 美术挂点
		this.artNode = Node();
		this.node.addChild(this.artNode);

		this.projDraw = DrawNode();
		this.node.addChild(this.projDraw);

		this.titleLabel = Label('sarasa-mono-sc-regular', 13) as Label.Type;
		this.titleLabel.y = 148;
		this.node.addChild(this.titleLabel);

		this.refreshVisual();
	}

	public refreshVisual(): void {
		this.bodyDraw.clear();
		const stats = GameConfig.TOWER_STATS[this.state.type];
		if (!this.state.unlocked) {
			artHide(this.artNode);
			drawRect(this.bodyDraw, -24, 0, 48, 24, 0x664a5568, 0xffa0aec0);
			this.titleLabel.text = '炮台空位(未修)';
			this.titleLabel.color = Color(0xffa0aec0);
			this.titleLabel.y = 38;
			return;
		}

		// 石砌敌台底座 + 箭楼/炮位
		// 有美术素材时用精灵替掉程序化炮台
		// 有美术素材时用精灵替掉程序化炮台（2 级换升级版贴图）
		const baseArt = this.state.type === 'CANNON' ? 'tower_cannon' : 'tower_arrow';
		const towerArt = artInto(this.artNode, this.state.level >= 2 ? `${baseArt}_lv2` : baseArt);
		if (towerArt === undefined) {
			drawRect(this.bodyDraw, -28, 0, 56, 105, 0xff4a5568, 0xffa0aec0);
		}
		drawRect(this.bodyDraw, -32, 105, 64, 24, stats.color, 0xffe2e8f0);
		if (this.state.type === 'CANNON') {
			drawRect(this.bodyDraw, 12, 112, 26, 8, 0xff1a202c);
		}
		// 耐久条
		const pct = Math.max(0, this.state.hp / this.state.maxHp);
		drawRect(this.bodyDraw, -26, 134, 52, 5, 0xff2d3748);
		drawRect(this.bodyDraw, -26, 134, 52 * pct, 5, 0xff63b3ed);

		this.titleLabel.text = `${stats.name} Lv.${this.state.level}`;
		this.titleLabel.color = Color(0xfffefcbf);
		this.titleLabel.y = 150;
	}

	public update(dt: number, enemies: Enemy[]): void {
		// 更新飞行中的弹道（以塔自身为局部坐标系）
		this.projDraw.clear();
		const remaining: Projectile[] = [];
		for (const p of this.projectiles) {
			p.elapsed += dt;
			const t = Math.min(1, p.elapsed / p.duration);
			p.x = p.startX + (p.targetX - p.startX) * t;
			const arc = p.isCannon ? Math.sin(t * Math.PI) * 55 : Math.sin(t * Math.PI) * 24;
			p.y = p.startY * (1 - t) + 28 * t + arc;

			const localX = p.x - this.state.x;
			if (p.art !== undefined) {
				p.art.x = localX;
				p.art.y = p.y;
			} else if (p.isCannon) {
				this.projDraw.drawDot(Vec2(localX, p.y), 6, Color(0xfff6ad55));
			} else {
				this.projDraw.drawSegment(
					Vec2(localX - 8, p.y),
					Vec2(localX + 8, p.y),
					2,
					Color(0xfffefcbf)
				);
			}

			if (t >= 1) {
				if (p.art !== undefined) {
					p.art.removeFromParent();
				}
				this.applyImpact(p, enemies);
			} else {
				remaining.push(p);
			}
		}
		this.projectiles = remaining;

		if (!this.state.unlocked || this.state.hp <= 0) {
			return;
		}

		if (this.cooldownTimer > 0) {
			this.cooldownTimer = Math.max(0, this.cooldownTimer - dt);
			return;
		}

		const stats = GameConfig.TOWER_STATS[this.state.type];
		let target: Enemy | undefined = undefined;
		let bestDist = stats.range;
		for (const e of enemies) {
			if (e.dead) continue;
			const d = Math.abs(e.x - this.state.x);
			if (d <= bestDist) {
				bestDist = d;
				target = e;
			}
		}

		if (!target) return;

		this.cooldownTimer = stats.cooldown;
		// 宗祠士气亦鼓舞炮手：每级 +12% 威力
		const dmg = Math.round(
			stats.damage * (1 + 0.25 * (this.state.level - 1)) * (1 + GameState.instance.moraleBonus)
		);
		const speed = this.state.type === 'CANNON' ? 480 : 680;
		const dist = Math.max(40, Math.abs(target.x - this.state.x));
		const projArt = artSprite(this.state.type === 'CANNON' ? 'proj_cannonball' : 'proj_arrow');
		if (projArt !== undefined) {
			projArt.x = 0;
			projArt.y = 116;
			this.node.addChild(projArt);
		}
		this.projectiles.push({
			x: this.state.x,
			y: 116,
			startX: this.state.x,
			startY: 116,
			targetX: target.x,
			speed,
			elapsed: 0,
			duration: dist / speed,
			damage: dmg,
			splashRadius: this.state.type === 'CANNON' ? GameConfig.TOWER_STATS.CANNON.splashRadius : 0,
			isCannon: this.state.type === 'CANNON',
			art: projArt,
		});
	}

	private applyImpact(p: Projectile, enemies: Enemy[]): void {
		// 箭矢 / 炮弹落点炸开一下（素材缺失则什么都不画）
		playFx(
			this.node.parent,
			p.isCannon ? 'fx_cannon_hit' : 'fx_arrow_hit',
			p.targetX,
			GameConfig.GROUND_Y + (p.isCannon ? 38 : 58),
			0.3,
			0.35,
			0
		);
		if (p.splashRadius > 0) {
			for (const e of enemies) {
				if (!e.dead && Math.abs(e.x - p.targetX) <= p.splashRadius) {
					e.takeDamage(p.damage, 18);
				}
			}
			return;
		}

		let hit: Enemy | undefined = undefined;
		let bestDist = 45;
		for (const e of enemies) {
			if (e.dead) continue;
			const d = Math.abs(e.x - p.targetX);
			if (d < bestDist) {
				bestDist = d;
				hit = e;
			}
		}
		if (hit) {
			hit.takeDamage(p.damage, 6);
		}
	}
}
