import {
	BlendFunc,
	BlendOp,
	Content,
	Node,
	Rect,
	Size,
	Sprite,
	Texture2D,
	TextureFilter,
	Vec2,
} from 'Dora';

/**
 * pixelfx 导出的精灵表规格（可直接粘贴 `scripts/export_dora.mjs` 输出）。
 * 注意：pixelfx 的 pivot 原点在每帧左上角（Y 向下），本模块会自动换算为 Dora 的左下角锚点（Y 向上）。
 */
export interface PixelFxSpec {
	/** 相对项目根目录的精灵表 PNG 路径，如 `assets/fx/pixelfx/double-slash.png`。 */
	path: string;
	/** 单帧宽度（像素）。 */
	frameW: number;
	/** 单帧高度（像素）。 */
	frameH: number;
	/** 精灵表列数。 */
	cols: number;
	/** 总帧数。 */
	frames: number;
	/** 播放帧率（每秒帧数）。 */
	fps: number;
	/** 是否循环播放，默认 false。 */
	loop?: boolean;
	/** 帧内锚点 X（像素，从左边起），默认居中的 frameW * 0.5。 */
	pivotX?: number;
	/** 帧内锚点 Y（像素，从顶边起，pixelfx 坐标系），默认居中的 frameH * 0.5。 */
	pivotY?: number;
}

export interface PixelFxOptions {
	/** 整数像素放大倍数（默认 2，保持 Point 锐利像素边缘）。 */
	scale?: number;
	/** 是否水平镜像（朝左）。 */
	facingLeft?: boolean;
	/** 是否启用叠加发光混合 `SrcAlpha + One`（适合夜晚/暗底火焰与闪电）。 */
	additive?: boolean;
	/** 覆盖 spec.loop。 */
	loop?: boolean;
	/** 旋转角度（度）。 */
	angle?: number;
	/** 不透明度（0..1），默认 1。 */
	opacity?: number;
	/** 节点渲染顺序。 */
	zOrder?: number;
}

export interface PixelFxHandle {
	readonly node: Node.Type;
	stop(): void;
	isDone(): boolean;
}

interface ActivePixelFx {
	holder: Node.Type;
	sprite: Sprite.Type;
	spec: PixelFxSpec;
	loop: boolean;
	elapsed: number;
	lastIdx: number;
	done: boolean;
}

const texCache: Record<string, Texture2D.Type> = {};
const activeList: ActivePixelFx[] = [];

function loadTextureCached(path: string): Texture2D.Type | undefined {
	const cached = texCache[path];
	if (cached !== undefined) return cached;
	if (!Content.exist(path)) return undefined;
	const tex = Texture2D(path);
	if (tex !== undefined) {
		texCache[path] = tex;
	}
	return tex;
}

function applyFrameRect(sprite: Sprite.Type, spec: PixelFxSpec, idx: number): void {
	const col = idx % spec.cols;
	const row = Math.floor(idx / spec.cols);
	sprite.textureRect = Rect(col * spec.frameW, row * spec.frameH, spec.frameW, spec.frameH);
}

/**
 * 在世界/UI 节点下播放一个由 pixelfx 导出的逐帧像素特效。
 * 贴图缺失时安全返回 undefined，不抛错。
 */
export function playPixelFx(
	parent: Node.Type | undefined,
	spec: PixelFxSpec,
	x: number,
	y: number,
	opts?: PixelFxOptions
): PixelFxHandle | undefined {
	if (parent === undefined || spec.frames <= 0 || spec.cols <= 0 || spec.fps <= 0) {
		return undefined;
	}
	const tex = loadTextureCached(spec.path);
	if (tex === undefined) return undefined;

	const holder = Node();
	holder.x = x;
	holder.y = y;
	if (opts?.angle !== undefined) holder.angle = opts.angle;
	if (opts?.zOrder !== undefined) holder.order = opts.zOrder;

	const sprite = Sprite(tex, Rect(0, 0, spec.frameW, spec.frameH));
	if (sprite === undefined) return undefined;

	sprite.filter = TextureFilter.Point;
	const pivotX = spec.pivotX !== undefined ? spec.pivotX : spec.frameW * 0.5;
	const pivotY = spec.pivotY !== undefined ? spec.pivotY : spec.frameH * 0.5;
	sprite.anchor = Vec2(pivotX / spec.frameW, 1 - pivotY / spec.frameH);

	const scale = opts?.scale !== undefined ? opts.scale : 2;
	sprite.size = Size(spec.frameW * scale, spec.frameH * scale);
	if (opts?.facingLeft === true) {
		sprite.scaleX = -1;
	}
	if (opts?.additive === true) {
		sprite.blendFunc = BlendFunc(BlendOp.SrcAlpha, BlendOp.One);
	}
	if (opts?.opacity !== undefined) {
		sprite.opacity = opts.opacity;
	}

	holder.addChild(sprite);
	parent.addChild(holder);

	const loop = opts?.loop !== undefined ? opts.loop : spec.loop === true;
	const entry: ActivePixelFx = {
		holder,
		sprite,
		spec,
		loop,
		elapsed: 0,
		lastIdx: 0,
		done: false,
	};
	activeList.push(entry);

	return {
		node: holder,
		stop(): void {
			if (entry.done) return;
			entry.done = true;
			entry.holder.removeFromParent(true);
		},
		isDone(): boolean {
			return entry.done;
		},
	};
}

/** 推进全部 pixelfx 特效帧；在主循环 `tickFx(dt)` 内自动调用。 */
export function tickPixelFx(dt: number): void {
	for (let i = activeList.length - 1; i >= 0; i--) {
		const item = activeList[i];
		if (item.done) {
			activeList.splice(i, 1);
			continue;
		}
		item.elapsed += dt;
		const rawIdx = Math.floor(item.elapsed * item.spec.fps);
		let idx = rawIdx;
		if (item.loop) {
			idx = ((rawIdx % item.spec.frames) + item.spec.frames) % item.spec.frames;
		} else if (rawIdx >= item.spec.frames) {
			item.done = true;
			item.holder.removeFromParent(true);
			activeList.splice(i, 1);
			continue;
		}
		if (idx !== item.lastIdx) {
			item.lastIdx = idx;
			applyFrameRect(item.sprite, item.spec, idx);
		}
	}
}

/** 清空全部活动中的 pixelfx 特效节点（切换场景时随 `clearFx()` 调用）。 */
export function clearPixelFx(): void {
	for (const item of activeList) {
		if (!item.done) {
			item.done = true;
			item.holder.removeFromParent(true);
		}
	}
	activeList.splice(0, activeList.length);
}
