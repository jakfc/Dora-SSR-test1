import { Color, DrawNode, Label, Node, Size, Vec2 } from 'Dora';
import { SceneManager } from 'src/scenes/SceneManager';
import { GameConfig } from 'src/config/GameConfig';
import { GameState } from 'src/config/GameState';
import { Screen } from 'src/config/Screen';
import { artAt, artStretch } from 'src/config/Assets';
import { createButton } from 'src/ui/HudLayer';

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
 * 主菜单场景：水墨背景、标题、《永昌堡史料图鉴》弹窗、开始按钮
 */
export function TitleScene(): Node.Type {
	const scene = Node();
	// 可视区域尺寸与设计框偏移（窗口尺寸变化时本场景会被 SceneManager 重建）
	const W = Screen.width;
	const H = Screen.height;
	const OY = Screen.offsetY;

	// 水墨风背景与城墙剪影
	const bg = DrawNode();
	drawRect(bg, 0, 0, W, H, 0xff161e29);
	// 远山剪影
	const ox = Screen.offsetX;
	bg.drawPolygon(
		[
			Vec2(0, 140),
			Vec2(ox + 280, 420),
			Vec2(ox + 560, 220),
			Vec2(ox + 880, 380),
			Vec2(ox + 1280, 180),
			Vec2(W, 140),
		],
		Color(0xff222e3d)
	);
	// 城墙剪影（贴底铺满）
	drawRect(bg, 0, 0, W, 140, 0xff2d3748, 0xff4a5568);
	for (let x = 40; x < W; x += 90) {
		drawRect(bg, x, 140, 48, 28, 0xff2d3748, 0xff4a5568);
	}
	scene.addChild(bg);

	// 美术贴图：封面大图优先；没有封面就用夜色天空铺底 + 大罗山剪影 + 城墙地面
	// （连夜空都没有时保留上面的程序化水墨）
	const cover = artStretch('title_bg', W, H);
	const backdrop = cover !== undefined ? cover : artStretch('sky_night', W, H);
	if (backdrop !== undefined) {
		backdrop.anchor = Vec2(0, 0);
		backdrop.x = 0;
		backdrop.y = 0;
		backdrop.size = Size(W, H);
		scene.addChild(backdrop);
		bg.clear();
	}
	if (cover === undefined) {
		for (let i = 0; i < Math.ceil(W / 1280); i++) {
			artAt(scene, 'horizon', i * 1280, 140);
		}
		for (let i = 0; i < Math.ceil(W / 640) + 1; i++) {
			artAt(scene, 'ground_city', i * 640, 0);
		}
	}

	// 标题文案
	const title = Label('sarasa-mono-sc-regular', 54) as Label.Type;
	title.text = '永昌堡：铁血筑城';
	title.x = W / 2;
	title.y = OY + 530;
	title.color = Color(0xfff6e05e);
	scene.addChild(title);

	const subtitle = Label('sarasa-mono-sc-regular', 20) as Label.Type;
	subtitle.text = GameConfig.HISTORICAL_QUOTES.TITLE_SUBTITLE;
	subtitle.x = W / 2;
	subtitle.y = OY + 468;
	subtitle.color = Color(0xffcbd5e0);
	scene.addChild(subtitle);

	const intro = Label('sarasa-mono-sc-regular', 16) as Label.Type;
	intro.text = '王叔杲辍试归乡，捐资七千余金，行“十八号分段包干”之制，筑城十一月，八挫倭锋。';
	intro.x = W / 2;
	intro.y = OY + 422;
	intro.color = Color(0xffa0aec0);
	scene.addChild(intro);

	// 史料图鉴弹窗（内部按 1280x720 设计坐标布局，整体平移 offset）
	const codexModal = Node();
	codexModal.visible = false;
	codexModal.x = ox;
	codexModal.y = OY;
	const dim = DrawNode();
	drawRect(dim, 0, 0, W, H, 0xbb000000);
	codexModal.addChild(dim);

	const panel = DrawNode();
	drawRect(panel, 200, 100, 880, 520, 0xff1a202c, 0xfff6ad55);
	const panelArt = artStretch('ui_modal', 880, 520);
	if (panelArt !== undefined) {
		panelArt.anchor = Vec2(0, 0);
		panelArt.x = 200;
		panelArt.y = 100;
		panelArt.size = Size(880, 520);
		codexModal.addChild(panelArt);
		panel.clear();
	}
	codexModal.addChild(panel);

	const codexTitle = Label('sarasa-mono-sc-regular', 26) as Label.Type;
	codexTitle.text = '《永昌堡史料图鉴》';
	codexTitle.x = 640;
	codexTitle.y = 582;
	codexTitle.color = Color(0xfff6e05e);
	codexModal.addChild(codexTitle);

	let yPos = 520;
	for (const entry of GameConfig.HISTORY_CODEX) {
		const head = Label('sarasa-mono-sc-regular', 17) as Label.Type;
		head.anchor = Vec2(0, 0.5);
		head.x = 240;
		head.y = yPos;
		head.color = Color(0xfffbd38d);
		head.text = `【${entry.title}】 (${entry.period})`;
		codexModal.addChild(head);

		const body = Label('sarasa-mono-sc-regular', 15) as Label.Type;
		body.anchor = Vec2(0, 1);
		body.x = 240;
		body.y = yPos - 16;
		body.textWidth = 800;
		body.color = Color(0xffe2e8f0);
		body.text = entry.content;
		codexModal.addChild(body);

		yPos -= 96;
	}

	const closeBtn = createButton('关闭图鉴', 160, 44, 0xff9b2c2c, () => {
		codexModal.visible = false;
	}, 16);
	closeBtn.x = 560;
	closeBtn.y = 122;
	codexModal.addChild(closeBtn);

	// 主菜单按钮
	const startBtn = createButton('开始筑堡抗倭', 240, 54, 0xffc05621, () => {
		GameState.instance.reset();
		SceneManager.start('GAME');
	}, 20);
	startBtn.x = W / 2 - 120;
	startBtn.y = OY + 290;
	scene.addChild(startBtn);

	const codexBtn = createButton('永昌堡史料图鉴', 240, 48, 0xff2b6cb0, () => {
		codexModal.visible = true;
	}, 18);
	codexBtn.x = W / 2 - 120;
	codexBtn.y = OY + 220;
	scene.addChild(codexBtn);

	scene.addChild(codexModal);
	return scene;
}
