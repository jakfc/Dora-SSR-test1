import { Node, Sprite } from 'Dora';
import { artFace, artInto } from 'src/config/Assets';

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

const items: FxItem[] = [];

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
}

/** 清场（切换场景时调用，避免残留节点）。 */
export function clearFx(): void {
	for (const it of items) {
		it.holder.removeFromParent(true);
	}
	items.splice(0, items.length);
}
