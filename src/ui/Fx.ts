import { Node, Sprite } from 'Dora';
import { artFace, artInto } from 'src/config/Assets';
import { clearPixelFx, tickPixelFx } from 'src/ui/PixelFx';
export { playPixelFx } from 'src/ui/PixelFx';
export type { PixelFxHandle, PixelFxOptions, PixelFxSpec } from 'src/ui/PixelFx';

interface FxItem {
	holder: Node.Type;
	sprite: Sprite.Type | undefined;
	life: number;
	total: number;
	grow: number;
	rise: number;
	baseY: number;
	sign: number;
}

interface PulseItem {
	node: Node.Type;
	t: number;
	dur: number;
	intensity: number;
}

interface MoveYItem {
	node: Node.Type;
	fromY: number;
	toY: number;
	t: number;
	dur: number;
}

const items: FxItem[] = [];
const pulses: PulseItem[] = [];
const moveYs: MoveYItem[] = [];

/** 让建筑/场景节点播放一次 Q 弹交互回弹动画（投银、置办工具、竣工升级时调用）。 */
export function pulseNode(node: Node.Type | undefined, intensity = 0.08, dur = 0.32): void {
	if (node === undefined) return;
	for (let i = pulses.length - 1; i >= 0; i--) {
		if (pulses[i].node === node) {
			pulses.splice(i, 1);
		}
	}
	pulses.push({ node, t: 0, dur, intensity });
}

/** 平滑移动节点的 Y 坐标（例如东门瓮城闸门升降）。 */
export function animateMoveY(node: Node.Type | undefined, toY: number, dur = 0.42): void {
	if (node === undefined) return;
	for (let i = moveYs.length - 1; i >= 0; i--) {
		if (moveYs[i].node === node) {
			moveYs.splice(i, 1);
		}
	}
	if (Math.abs(node.y - toY) < 1) {
		node.y = toY;
		return;
	}
	moveYs.push({ node, fromY: node.y, toY, t: 0, dur });
}

/**
 * 在世界层播一个一次性特效：life 秒内放大 grow 倍并淡出，然后自动回收。
 *
 * 素材缺失时什么都不画（也不报错），所以没有美术资源游戏照样能跑。
 * @param parent 挂在哪个节点下（一般是世界层，保证画在角色之上）
 * @param id     `Assets.ts` 里的素材 id，例如 `fx_slash`
 * @param x,y    世界坐标
 * @param life   持续时间（秒）
 * @param grow   结束时额外放大的比例，0.45 表示放大到 1.45 倍
 * @param rise   结束时向上飘的像素高度
 * @param facingLeft 是否朝左（自动镜像）
 */
export function playFx(
	parent: Node.Type | undefined,
	id: string,
	x: number,
	y: number,
	life = 0.22,
	grow = 0.45,
	rise = 0,
	facingLeft = false
): void {
	if (parent === undefined) return;
	const holder = Node();
	holder.x = x;
	holder.y = y;
	parent.addChild(holder);

	const sprite = artInto(holder, id);
	let sign = 1;
	if (sprite !== undefined) {
		artFace(sprite, id, facingLeft);
		sign = sprite.scaleX < 0 ? -1 : 1;
	}
	items.push({ holder, sprite, life, total: life, grow, rise, baseY: y, sign: sign });
}

/** 每帧推进所有特效；特效播完自动从场景里摘掉。 */
export function tickFx(dt: number): void {
	for (let i = items.length - 1; i >= 0; i--) {
		const it = items[i];
		it.life -= dt;
		if (it.life <= 0) {
			it.holder.removeFromParent(true);
			items.splice(i, 1);
			continue;
		}
		const t = 1 - it.life / it.total;
		if (it.sprite !== undefined) {
			const scale = 1 + it.grow * t;
			it.sprite.scaleX = it.sign * scale;
			it.sprite.scaleY = scale;
			it.sprite.opacity = Math.max(0, 1 - t);
		}
		if (it.rise !== 0) {
			it.holder.y = it.baseY + it.rise * t;
		}
	}

	for (let i = pulses.length - 1; i >= 0; i--) {
		const p = pulses[i];
		p.t += dt;
		if (p.t >= p.dur) {
			p.node.scaleX = 1;
			p.node.scaleY = 1;
			pulses.splice(i, 1);
			continue;
		}
		const u = p.t / p.dur;
		const wave = Math.sin(u * Math.PI * 2) * (1 - u);
		p.node.scaleX = 1 + p.intensity * wave;
		p.node.scaleY = 1 - p.intensity * wave;
	}

	for (let i = moveYs.length - 1; i >= 0; i--) {
		const m = moveYs[i];
		m.t += dt;
		if (m.t >= m.dur) {
			m.node.y = m.toY;
			moveYs.splice(i, 1);
			continue;
		}
		const u = m.t / m.dur;
		const ease = 1 - (1 - u) * (1 - u) * (1 - u);
		m.node.y = m.fromY + (m.toY - m.fromY) * ease;
	}

	tickPixelFx(dt);
}

/** 清场（切换场景时调用，避免残留节点）。 */
export function clearFx(): void {
	for (const it of items) {
		it.holder.removeFromParent(true);
	}
	items.splice(0, items.length);
	for (const p of pulses) {
		p.node.scaleX = 1;
		p.node.scaleY = 1;
	}
	pulses.splice(0, pulses.length);
	moveYs.splice(0, moveYs.length);
	clearPixelFx();
}
