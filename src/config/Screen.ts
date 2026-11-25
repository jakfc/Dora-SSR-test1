import { Director, Node, TypeName, View, tolua } from 'Dora';
import { GameConfig } from 'src/config/GameConfig';

/**
 * 屏幕自适应 + 镜头缩放。
 *
 * 设计分辨率固定为 GameConfig.SCREEN_WIDTH x SCREEN_HEIGHT（1280 x 720）。
 *
 * 两套坐标空间：
 *   1) 世界空间（地面 / 地标 / 人物 / 敌人）——按「镜头」缩放，
 *      zoom = fit * WORLD_ZOOM，其中 fit = min(窗口像素宽/1280, 窗口像素高/720)。
 *      所以 WORLD_ZOOM 就是「镜头拉近倍数」：调大它 → 视角收窄、画面放大、
 *      人物与建筑看起来更大更清楚（"视角太广"就是它太小）。
 *   2) UI 空间（HUD / 标题 / 结算）——由 attachUi 抵消镜头放大，
 *      单位恒等于设计单位，窗口再宽也不会把界面拉变形。
 *
 * 用法：
 *   - 每帧调用 Screen.sync()（SceneManager.tick 里已挂）；
 *   - 世界布局读 Screen.width / height / offsetX / offsetY；
 *   - UI 布局读 Screen.uiWidth / uiHeight / uiOffsetX / uiOffsetY，
 *     并在自己节点上调用 Screen.attachUi(node)。
 */
export class Screen {
	/**
	 * 镜头拉近倍数。
	 * 1.0 = 设计原尺寸（一个设计框 1280x720 铺满可视区，宽屏两侧会多看到世界）
	 * 1.4 = 当前手感：可视世界约 1280/1.4 ≈ 915 单位宽，人物/建筑明显放大
	 */
	public static readonly WORLD_ZOOM = 1.4;

	private static camZoom = 1;
	private static uiZoom = 1;
	private static lastPixelW = 0;
	private static lastPixelH = 0;

	/** 当前世界渲染缩放（摄像机 zoom） */
	public static get zoom(): number {
		return Screen.camZoom;
	}

	/** 可视世界宽度（世界单位） */
	public static get width(): number {
		return View.size.width / Screen.camZoom;
	}

	/** 可视世界高度（世界单位） */
	public static get height(): number {
		return View.size.height / Screen.camZoom;
	}

	/** 1280x720 设计框在可视世界中的水平偏移（居中） */
	public static get offsetX(): number {
		return (Screen.width - GameConfig.SCREEN_WIDTH) / 2;
	}

	/** 1280x720 设计框在可视世界中的垂直偏移（居中） */
	public static get offsetY(): number {
		return (Screen.height - GameConfig.SCREEN_HEIGHT) / 2;
	}

	/** 可视世界右边界 */
	public static get right(): number {
		return Screen.width;
	}

	/**
	 * UI 单位 → 世界单位。
	 * HUD 被 attachUi 缩小了 1/WORLD_ZOOM，所以它的 70/80 单位在世界上只有 70/80 ÷ WORLD_ZOOM。
	 */
	public static uiToWorld(uiUnits: number): number {
		return uiUnits / Screen.WORLD_ZOOM;
	}

	/** 世界单位 → UI 单位。 */
	public static worldToUi(worldUnits: number): number {
		return worldUnits * Screen.WORLD_ZOOM;
	}

	/** UI 空间宽度（设计单位，等价于改动前的 Screen.width） */
	public static get uiWidth(): number {
		return View.size.width / Screen.uiZoom;
	}

	/** UI 空间高度（设计单位） */
	public static get uiHeight(): number {
		return View.size.height / Screen.uiZoom;
	}

	/** 1280x720 设计框在 UI 空间中的水平偏移（居中） */
	public static get uiOffsetX(): number {
		return (Screen.uiWidth - GameConfig.SCREEN_WIDTH) / 2;
	}

	/** 1280x720 设计框在 UI 空间中的垂直偏移（居中） */
	public static get uiOffsetY(): number {
		return (Screen.uiHeight - GameConfig.SCREEN_HEIGHT) / 2;
	}

	/**
	 * 把节点挂到 UI 空间：抵消镜头放大，使其 1 单位 = 1 设计单位。
	 * HUD / 标题 / 结算界面的根节点都要调用一次。
	 */
	public static attachUi(node: Node.Type): void {
		const s = 1 / Screen.WORLD_ZOOM;
		node.scaleX = s;
		node.scaleY = s;
	}

	/**
	 * 每帧同步：重算缩放、更新摄像机、把根节点摆到可视区域左下角。
	 * @param root 场景根节点（SceneManager.root）
	 */
	public static sync(root?: Node.Type): void {
		const pixelW = View.size.width;
		const pixelH = View.size.height;
		if (pixelW <= 0 || pixelH <= 0) return;

		// fit：让 1280x720 设计框刚好装进窗口（取宽高比中较小的那个）
		const fit = Math.min(pixelW / GameConfig.SCREEN_WIDTH, pixelH / GameConfig.SCREEN_HEIGHT);
		const safeFit = fit > 0 ? fit : 1;

		Screen.uiZoom = safeFit;
		Screen.camZoom = safeFit * Screen.WORLD_ZOOM;

		const camera = tolua.cast(Director.currentCamera, TypeName.Camera2D);
		if (camera !== undefined) {
			camera.zoom = Screen.camZoom;
		}

		if (root !== undefined) {
			root.x = -Screen.width / 2;
			root.y = -Screen.height / 2;
		}

		// 记录窗口像素尺寸变化（首次同步不算变化，避免启动时重建场景）
		Screen.resized =
			Screen.lastPixelW !== 0 && (pixelW !== Screen.lastPixelW || pixelH !== Screen.lastPixelH);
		Screen.lastPixelW = pixelW;
		Screen.lastPixelH = pixelH;
	}

	/** 本帧是否刚检测到窗口像素尺寸变化（由 sync 写入） */
	public static resized = false;
}
