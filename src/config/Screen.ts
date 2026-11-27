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
 *   - UI 布局读 Screen.uiWidth / uiHeight 以及 **内容安全框
 *     Screen.uiBoxX / uiBoxY / uiBoxW / uiBoxH**（居中、按 1280x720 比例、随分辨率自动缩放），
 *     并在自己节点上调用 Screen.attachUi(node)。
 */
export class Screen {
	/**
	 * 镜头拉近倍数。
	 * 1.0 = 设计原尺寸（一个设计框 1280x720 铺满可视区，宽屏两侧会多看到世界）
	 * 1.85 = 当前手感：可视世界约 1280/1.85 ≈ 690 单位宽，
	 *        人物和屋舍看得清，水田/盐田也正好摆在画面里而不显空旷。
	 */
	public static readonly WORLD_ZOOM = 1.25;

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
	 * HUD 节点被 attachUi 缩到 uiZoom/camZoom，所以它 1 个设计单位在世界上只有这么多。
	 */
	public static uiToWorld(uiUnits: number): number {
		return (uiUnits * Screen.uiZoom) / Screen.camZoom;
	}

	/** 世界单位 → UI 单位。 */
	public static worldToUi(worldUnits: number): number {
		return (worldUnits * Screen.camZoom) / Screen.uiZoom;
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
	 * UI 内容安全框（左上角 X）。
	 *
	 * 这是一块**始终按 1280x720 设计比例居中**的矩形，随分辨率自动缩放：
	 *   - 窗口比设计更宽（超宽屏）时，框比 UI 空间窄，左右自动留白；
	 *   - 窗口比设计更窄时，框顶到边界，不会越出屏幕。
	 *
	 * HUD 的**内容**（文字、图标、面板、弹窗）都排在这个框里；
	 * 只有顶栏/底栏的底板横跨整块屏幕（用 uiWidth）。
	 *
	 * 为什么要这样：`uiWidth = 窗口宽 / uiZoom`，而 uiZoom = min(宽/1280, 高/720)，
	 * 所以 3440x1369 这种 2.5:1 的窗口 uiWidth ≈ 1809。以前直接拿 uiWidth 当
	 * 「内容宽」排布，左侧信息与右侧资源就各自贴到屏幕两个角上（相隔 1800 单位），
	 * 看起来就是「不居中、到处偏移」。
	 */
	public static get uiBoxX(): number {
		return Math.max(0, Screen.uiOffsetX);
	}

	/** UI 内容安全框（下边缘 Y） */
	public static get uiBoxY(): number {
		return Math.max(0, Screen.uiOffsetY);
	}

	/** UI 内容安全框的宽（不超过设计宽 1280） */
	public static get uiBoxW(): number {
		return Math.min(Screen.uiWidth, GameConfig.SCREEN_WIDTH);
	}

	/** UI 内容安全框的高（不超过设计高 720） */
	public static get uiBoxH(): number {
		return Math.min(Screen.uiHeight, GameConfig.SCREEN_HEIGHT);
	}

	/** UI 内容安全框的右边缘 */
	public static get uiBoxRight(): number {
		return Screen.uiBoxX + Screen.uiBoxW;
	}

	/** UI 内容安全框的水平中心（= 屏幕中心） */
	public static get uiBoxCenterX(): number {
		return Screen.uiBoxX + Screen.uiBoxW / 2;
	}

	/**
	 * 把节点挂到 UI 空间：抵消镜头放大，使其 1 单位 = 1 设计单位。
	 * HUD / 标题 / 结算界面的根节点都要调用一次。
	 */
	public static attachUi(node: Node.Type): void {
		// 摄像机放了 camZoom 倍，UI 要缩回去：uiZoom/camZoom 正好让 1 单位 = 1 设计单位
		const s = Screen.camZoom > 0 ? Screen.uiZoom / Screen.camZoom : 1;
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
		// 镜头缩放：【修】以「世界视野高度」为准，而不是简单乘 WORLD_ZOOM。
		// 超宽屏（如 3440x1369）以前会把世界视野挤到 389 高 ——
		// 构图全挤在中间一条窄带里，地下泥土层占掉屏幕快一半。
		// 现在锁定目标视野高度（CAMERA_VIEW_HEIGHT / WORLD_ZOOM，约 416 单位），
		// 再给一个最小可见宽度（窄窗口时改按宽度装），宽出来的部分就多看两边。
		const targetH = Math.max(240, GameConfig.CAMERA_VIEW_HEIGHT / Screen.WORLD_ZOOM);
		const zoomH = pixelH / targetH;
		const zoomW = pixelW / Math.max(480, GameConfig.CAMERA_VIEW_WIDTH * 0.9);
		Screen.camZoom = Math.min(zoomH, zoomW);

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
