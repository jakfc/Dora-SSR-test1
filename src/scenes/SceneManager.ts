import { Director, Node } from 'Dora';
import { Screen } from 'src/config/Screen';

/**
 * 场景管理器：负责在 TitleScene / GameScene / GameOverScene 之间切换
 */
export class SceneManager {
	private static root: Node.Type | undefined = undefined;
	private static currentScene: Node.Type | undefined = undefined;
	private static currentName: string | undefined = undefined;
	private static relayout: (() => void) | undefined = undefined;
	private static factories: Record<string, (() => Node.Type) | undefined> = {};

	/**
	 * 注册场景工厂，避免各场景之间互相 import 造成循环 require
	 */
	public static register(name: string, factory: () => Node.Type): void {
		SceneManager.factories[name] = factory;
	}

	public static start(name: string): void {
		const factory = SceneManager.factories[name];
		if (factory !== undefined) {
			SceneManager.currentName = name;
			// 先清空上一场景的重排回调，再构建新场景（新场景可在构建时重新注册）
			SceneManager.relayout = undefined;
			// 先同步一次屏幕缩放：保证场景工厂构建时读到的 Screen.width / height
			// 已经是正确的可视区域（否则首帧会按未缩放的窗口像素尺寸布局）
			Screen.sync(SceneManager.root);
			SceneManager.switchTo(factory());
		}
	}

	public static switchTo(nextScene: Node.Type): void {
		if (!SceneManager.root) {
			SceneManager.root = Node();
			Director.entry.addChild(SceneManager.root);
		}
		if (SceneManager.currentScene) {
			SceneManager.currentScene.removeFromParent();
			SceneManager.currentScene = undefined;
		}
		SceneManager.currentScene = nextScene;
		SceneManager.root.addChild(nextScene);
		SceneManager.applyScreen();
	}

	/**
	 * 注册当前场景的“重排”回调。
	 *
	 * 窗口尺寸变化时优先调用它（例如 GameScene 只需重排 HUD，不能重建场景，
	 * 否则会丢失游戏进度）；没有注册时则重新构建当前场景（Title / GameOver 都是无状态的）。
	 */
	public static setRelayout(handler: (() => void) | undefined): void {
		SceneManager.relayout = handler;
	}

	/**
	 * 把根节点对齐到当前可视区域的左下角。
	 * 这样各场景内部就可以始终按「可视区域左下角 = (0,0)」来布局。
	 */
	public static applyScreen(): void {
		Screen.sync(SceneManager.root);
	}

	/** 每帧驱动：同步缩放，并在窗口像素尺寸变化时重排当前场景 */
	public static tick(): void {
		SceneManager.applyScreen();
		if (!Screen.resized) return;
		if (SceneManager.relayout !== undefined) {
			SceneManager.relayout();
			return;
		}
		// 无状态场景：直接重建，成本极低
		if (SceneManager.currentName !== undefined) {
			SceneManager.start(SceneManager.currentName);
		}
	}
}
