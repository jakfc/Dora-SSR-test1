import { Director, Node, TypeName, View, tolua } from 'Dora';
import { GameConfig } from 'src/config/GameConfig';

/**
 * 屏幕自适应。
 *
 * 设计分辨率固定为 GameConfig.SCREEN_WIDTH x SCREEN_HEIGHT（1280 x 720）。
 * 运行时按窗口像素尺寸等比缩放（取宽高比中较小的那个），保证：
 *   - 设计框整体可见，不会被裁掉；
 *   - 至少有一个方向刚好等于设计尺寸，另一个方向只会更大（不留黑边）；
 *   - 所有场景的坐标原点位于可视区域左下角，x 向右、y 向上。
 *
 * 用法：
 *   - 每帧调用 Screen.sync()（init.ts 里已挂全局调度）；
 *   - 布局时读 Screen.width / Screen.height 作为"可视区域"；
 *   - 读 Screen.offsetX / offsetY 得到 1280x720 设计框在可视区域中的左下角偏移。
 */
export class Screen {
	private static camZoom = 1;
	private static lastPixelW = 0;
	private static lastPixelH = 0;

	/** 当前渲染缩放倍数（摄像机 zoom） */
	public static get zoom(): number {
		return Screen.camZoom;
	}

	/** 可视区域宽度（设计单位，>= SCREEN_WIDTH） */
	public static get width(): number {
		return View.size.width / Screen.camZoom;
	}

	/** 可视区域高度（设计单位，>= SCREEN_HEIGHT） */
	public static get height(): number {
		return View.size.height / Screen.camZoom;
	}

	/** 设计框在可视区域中的水平偏移（居中） */
	public static get offsetX(): number {
		return (Screen.width - GameConfig.SCREEN_WIDTH) / 2;
	}

	/** 设计框在可视区域中的垂直偏移（居中） */
	public static get offsetY(): number {
		return (Screen.height - GameConfig.SCREEN_HEIGHT) / 2;
	}

	/** 可视区域右边界（设计单位） */
	public static get right(): number {
		return Screen.width;
	}

	/**
	 * 每帧同步：重算缩放、更新摄像机、把根节点摆到可视区域左下角。
	 * @param root 场景根节点（SceneManager.root）
	 */
	public static sync(root?: Node.Type): void {
		const pixelW = View.size.width;
		const pixelH = View.size.height;
		if (pixelW <= 0 || pixelH <= 0) return;

		const zoom = Math.min(pixelW / GameConfig.SCREEN_WIDTH, pixelH / GameConfig.SCREEN_HEIGHT);
		Screen.camZoom = zoom > 0 ? zoom : 1;

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
