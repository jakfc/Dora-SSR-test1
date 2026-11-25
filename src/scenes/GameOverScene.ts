import { Color, DrawNode, Label, Node, Size, Vec2 } from 'Dora';
import { SceneManager } from 'src/scenes/SceneManager';
import { GameConfig } from 'src/config/GameConfig';
import { GameState } from 'src/config/GameState';
import { Screen } from 'src/config/Screen';
import { artStretch } from 'src/config/Assets';
import { createButton } from 'src/ui/HudLayer';
import { soundBgm } from 'src/audio/Sound';

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
 * 胜负结算界面
 */
export function GameOverScene(isVictory: boolean): Node.Type {
	const scene = Node();
	const gs = GameState.instance;
	soundBgm(isVictory ? 'victory' : 'defeat');
	// 结算界面属于 UI 空间：单位与设计分辨率一致，镜头拉近时不会被一起放大
	Screen.attachUi(scene);
	// 可视区域尺寸与设计框偏移
	const W = Screen.uiWidth;
	const H = Screen.uiHeight;
	const ox = Screen.uiOffsetX;
	const oy = Screen.uiOffsetY;

	const bg = DrawNode();
	// 结算底图（胜利 / 失败各一张）；有图就铺满屏，没图退回程序化底色 + 面板
	const overBg = artStretch(isVictory ? 'over_victory' : 'over_defeat', W, H);
	if (overBg !== undefined) {
		overBg.anchor = Vec2(0, 0);
		overBg.x = 0;
		overBg.y = 0;
		overBg.size = Size(W, H);
		scene.addChild(overBg);
		// 压暗一层，保证文字可读
		drawRect(bg, 0, 0, W, H, 0x8a10141c);
	} else {
		drawRect(bg, 0, 0, W, H, isVictory ? 0xff1b2a38 : 0xff221619);
		drawRect(
			bg,
			ox + 220,
			oy + 110,
			840,
			500,
			0xdd1a202c,
			isVictory ? 0xfff6e05e : 0xffe53e3e
		);
	}
	scene.addChild(bg);

	const title = Label('sarasa-mono-sc-regular', 44) as Label.Type;
	title.text = isVictory ? '八挫倭锋 · 永昌大捷' : '宗祠倾颓 · 守堡未成';
	title.x = W / 2;
	title.y = oy + 540;
	title.color = Color(isVictory ? 0xfff6e05e : 0xfffc8181);
	scene.addChild(title);

	const epilogue = Label('sarasa-mono-sc-regular', 18) as Label.Type;
	epilogue.text = isVictory
		? GameConfig.HISTORICAL_QUOTES.VICTORY_EPILOGUE
		: GameConfig.HISTORICAL_QUOTES.DEFEAT_EPILOGUE;
	epilogue.x = W / 2;
	epilogue.y = oy + 468;
	epilogue.textWidth = 740;
	epilogue.color = Color(0xffe2e8f0);
	scene.addChild(epilogue);

	const stats = Label('sarasa-mono-sc-regular', 20) as Label.Type;
	stats.x = W / 2;
	stats.y = oy + 345;
	stats.textWidth = 680;
	stats.color = Color(0xfffbd38d);
	stats.text =
		`守卫天数：第 ${gs.day} / ${GameConfig.TOTAL_NIGHTS} 夜（击退 ${gs.wavesCleared} 波）\n` +
		`斩杀倭寇：${gs.totalKills} 名\n` +
		`累计筹措白银：${gs.silverEarned} 两   |   置办工具：${gs.toolsCrafted} 件\n` +
		`幸存族丁：${gs.populationCount} 人`;
	scene.addChild(stats);

	const retryBtn = createButton('重整旗鼓 · 再战', 210, 50, 0xffc05621, () => {
		GameState.instance.reset();
		SceneManager.start('GAME');
	}, 18);
	retryBtn.x = ox + 400;
	retryBtn.y = oy + 165;
	scene.addChild(retryBtn);

	const homeBtn = createButton('返回主菜单', 210, 50, 0xff2b6cb0, () => {
		GameState.instance.reset();
		SceneManager.start('TITLE');
	}, 18);
	homeBtn.x = ox + 670;
	homeBtn.y = oy + 165;
	scene.addChild(homeBtn);

	return scene;
}
