import { Color, DrawNode, Label, Node, Size, Sprite, Vec2 } from 'Dora';
import { GameConfig, LandmarkId, NightWaveConfig } from 'src/config/GameConfig';
import { GameState } from 'src/config/GameState';
import { Screen } from 'src/config/Screen';
import { artAt, artStretch } from 'src/config/Assets';

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

export function createButton(
	text: string,
	w: number,
	h: number,
	bgColor: number,
	onClick: () => void,
	fontSize = 15
): Node.Type {
	const btn = Node();
	btn.size = Size(w, h);
	btn.touchEnabled = true;

	// 按钮贴图（e04 普通态）；缺素材时回退为方块
	const art = artStretch('ui_btn_normal', w, h);
	if (art !== undefined) {
		art.anchor = Vec2(0, 0);
		art.size = Size(w, h);
		btn.addChild(art);
	} else {
		const bg = DrawNode();
		drawRect(bg, 0, 0, w, h, bgColor, 0xffe2e8f0);
		btn.addChild(bg);
	}

	const lbl = Label('sarasa-mono-sc-regular', fontSize) as Label.Type;
	lbl.text = text;
	lbl.color = Color(0xfffefcbf);
	lbl.x = w / 2;
	lbl.y = h / 2;
	btn.addChild(lbl);

	btn.onTapEnded(() => {
		onClick();
	});
	return btn;
}

export interface HudCallbacks {
	onSkipDay: () => void;
	onInteract: (optionIndex?: number) => void;
	onQilinStep: () => void;
	onRally: () => void;
	onVictoryModalConfirm: () => void;
}

const TOP_BAR_HEIGHT = 64;
const BOTTOM_BAR_HEIGHT = 76;

/**
 * 战斗 HUD 层：顶栏资源面板、底部操作条、地标快捷按钮、战报弹窗。
 * 所有元素位置由 `layout()` 依赖当前可视区域（Screen）计算，窗口尺寸变化时重新排布。
 */
export class HudLayer {
	public readonly node: Node.Type;
	private readonly topBg: DrawNode.Type;
	private readonly bottomBg: DrawNode.Type;
	private readonly topLabel: Label.Type;
	private readonly statusLabel: Label.Type;
	private readonly hintLabel: Label.Type;
	private readonly toastLabel: Label.Type;
	private readonly controlsLabel: Label.Type;
	private readonly skipDayBtn: Node.Type;
	private readonly extraActionNode: Node.Type;
	private readonly victoryModal: Node.Type;
	private readonly modalDim: DrawNode.Type;
	private readonly victoryBox: DrawNode.Type;
	private readonly victoryTitleLabel: Label.Type;
	private readonly victoryBodyLabel: Label.Type;
	private readonly confirmBtn: Node.Type;

	// —— 美术贴图（缺文件时全部回退为程序化绘制）——
	private readonly topBarArt: Sprite.Type | undefined;
	private readonly bottomBarArt: Sprite.Type | undefined;
	private readonly modalArt: Sprite.Type | undefined;
	private readonly dayIcon: Sprite.Type | undefined;
	private readonly nightIcon: Sprite.Type | undefined;
	private readonly silverIcon: Sprite.Type | undefined;
	private readonly grainIcon: Sprite.Type | undefined;
	private readonly popIcon: Sprite.Type | undefined;
	private readonly silverLabel: Label.Type;
	private readonly foodLabel: Label.Type;
	private readonly popLabel: Label.Type;

	private toastTimer = 0;
	private currentLandmark: LandmarkId | undefined = undefined;
	private callbacks: HudCallbacks;

	constructor(callbacks: HudCallbacks) {
		this.callbacks = callbacks;
		this.node = Node();

		// 顶栏背景（e01 贴图优先，缺素材则用方块）
		this.topBg = DrawNode();
		this.node.addChild(this.topBg);

		this.topBarArt = artStretch('ui_top_bar', Screen.width, TOP_BAR_HEIGHT);
		if (this.topBarArt !== undefined) {
			this.topBarArt.anchor = Vec2(0, 0);
			this.topBarArt.size = Size(Screen.width, TOP_BAR_HEIGHT);
			this.node.addChild(this.topBarArt);
		}

		this.topLabel = Label('sarasa-mono-sc-regular', 16) as Label.Type;
		this.topLabel.anchor = Vec2(0, 0.5);
		this.topLabel.color = Color(0xfffefcbf);
		this.node.addChild(this.topLabel);

		// 昼夜图标与资源图标（白银 / 粮草 / 族丁）
		this.dayIcon = artAt(this.node, 'icon_day', 0, 0);
		this.nightIcon = artAt(this.node, 'icon_night', 0, 0);
		this.silverIcon = artAt(this.node, 'icon_silver', 0, 0);
		this.grainIcon = artAt(this.node, 'icon_grain', 0, 0);
		this.popIcon = artAt(this.node, 'icon_population', 0, 0);
		if (this.dayIcon !== undefined) this.dayIcon.anchor = Vec2(0, 0.5);
		if (this.nightIcon !== undefined) this.nightIcon.anchor = Vec2(0, 0.5);
		if (this.silverIcon !== undefined) this.silverIcon.anchor = Vec2(0, 0.5);
		if (this.grainIcon !== undefined) this.grainIcon.anchor = Vec2(0, 0.5);
		if (this.popIcon !== undefined) this.popIcon.anchor = Vec2(0, 0.5);

		this.silverLabel = Label('sarasa-mono-sc-regular', 15) as Label.Type;
		this.silverLabel.anchor = Vec2(0, 0.5);
		this.silverLabel.color = Color(0xfff6e05e);
		this.node.addChild(this.silverLabel);

		this.foodLabel = Label('sarasa-mono-sc-regular', 15) as Label.Type;
		this.foodLabel.anchor = Vec2(0, 0.5);
		this.foodLabel.color = Color(0xfffefcbf);
		this.node.addChild(this.foodLabel);

		this.popLabel = Label('sarasa-mono-sc-regular', 15) as Label.Type;
		this.popLabel.anchor = Vec2(0, 0.5);
		this.popLabel.color = Color(0xffcbd5e0);
		this.node.addChild(this.popLabel);

		this.statusLabel = Label('sarasa-mono-sc-regular', 14) as Label.Type;
		this.statusLabel.anchor = Vec2(0, 0.5);
		this.statusLabel.color = Color(0xffcbd5e0);
		this.node.addChild(this.statusLabel);

		this.skipDayBtn = createButton('提前入夜', 112, 36, 0xff2b6cb0, () => {
			this.callbacks.onSkipDay();
		}, 14);
		this.node.addChild(this.skipDayBtn);

		// 中央飘字预警条
		this.toastLabel = Label('sarasa-mono-sc-regular', 20) as Label.Type;
		this.toastLabel.color = Color(0xfff6e05e);
		this.toastLabel.visible = false;
		this.node.addChild(this.toastLabel);

		// 底部交互提示条（e02 贴图优先）
		this.bottomBg = DrawNode();
		this.node.addChild(this.bottomBg);

		this.bottomBarArt = artStretch('ui_bottom_bar', Screen.width, BOTTOM_BAR_HEIGHT);
		if (this.bottomBarArt !== undefined) {
			this.bottomBarArt.anchor = Vec2(0, 0);
			this.bottomBarArt.size = Size(Screen.width, BOTTOM_BAR_HEIGHT);
			this.node.addChild(this.bottomBarArt);
		}

		this.hintLabel = Label('sarasa-mono-sc-regular', 15) as Label.Type;
		this.hintLabel.anchor = Vec2(0, 0.5);
		this.hintLabel.color = Color(0xfffefcbf);
		this.node.addChild(this.hintLabel);

		this.controlsLabel = Label('sarasa-mono-sc-regular', 13) as Label.Type;
		this.controlsLabel.anchor = Vec2(0, 0.5);
		this.controlsLabel.color = Color(0xffa0aec0);
		this.controlsLabel.text = '操作：[A/D]或方向键/点击地面移动   [E] 十八号包干交互   [J] 王家拳·麒麟步   [K] 鸣鼓集结';
		this.node.addChild(this.controlsLabel);

		// 底部右侧技能快捷按钮
		const btnE = createButton('[E] 交互', 92, 38, 0xff2f855a, () => this.callbacks.onInteract(0), 14);
		this.node.addChild(btnE);

		const btnJ = createButton('[J] 麒麟步', 98, 38, 0xffc05621, () => this.callbacks.onQilinStep(), 14);
		this.node.addChild(btnJ);

		const btnK = createButton('[K] 集结', 92, 38, 0xff9b2c2c, () => this.callbacks.onRally(), 14);
		this.node.addChild(btnK);
		// 布局时再定位，这里先记录引用
		this.skillButtons = [btnE, btnJ, btnK];

		// 地标多选项浮动按钮容器
		this.extraActionNode = Node();
		this.node.addChild(this.extraActionNode);

		// 胜利战报弹窗
		this.victoryModal = Node();
		this.victoryModal.visible = false;
		this.modalDim = DrawNode();
		this.victoryModal.addChild(this.modalDim);

		this.victoryBox = DrawNode();
		this.victoryModal.addChild(this.victoryBox);

		this.modalArt = artStretch('ui_modal', 600, 340);
		if (this.modalArt !== undefined) {
			this.modalArt.anchor = Vec2(0, 0);
			this.modalArt.size = Size(600, 340);
			this.victoryModal.addChild(this.modalArt);
		}

		this.victoryTitleLabel = Label('sarasa-mono-sc-regular', 26) as Label.Type;
		this.victoryTitleLabel.color = Color(0xfff6e05e);
		this.victoryModal.addChild(this.victoryTitleLabel);

		this.victoryBodyLabel = Label('sarasa-mono-sc-regular', 18) as Label.Type;
		this.victoryBodyLabel.color = Color(0xffe2e8f0);
		this.victoryModal.addChild(this.victoryBodyLabel);

		this.confirmBtn = createButton('整备堡务 · 迎接翌晨', 220, 48, 0xff2f855a, () => {
			this.victoryModal.visible = false;
			this.callbacks.onVictoryModalConfirm();
		}, 17);
		this.victoryModal.addChild(this.confirmBtn);

		this.node.addChild(this.victoryModal);

		// 资源图标挂在顶栏文字之上，避免被贴图遮挡

		this.layout();
	}

	private readonly skillButtons: Node.Type[] = [];

	/** 窗口尺寸变化后重新排布 HUD 元素 */
	public relayout(): void {
		this.layout();
	}

	private layout(): void {
		const w = Screen.width;
		const h = Screen.height;

		// 顶栏
		this.topBg.clear();
		if (this.topBarArt === undefined) {
			drawRect(this.topBg, 0, h - TOP_BAR_HEIGHT, w, TOP_BAR_HEIGHT, 0xcc1a202c);
			drawRect(this.topBg, 0, h - 2, w, 2, 0xff4a5568);
		} else {
			this.topBarArt.x = 0;
			this.topBarArt.y = h - TOP_BAR_HEIGHT;
			this.topBarArt.size = Size(w, TOP_BAR_HEIGHT);
		}

		const rowY = h - 22;
		this.topLabel.x = 20;
		this.topLabel.y = rowY;
		this.statusLabel.x = 20;
		this.statusLabel.y = h - 46;

		// 第一行右侧：白银 / 粮草 / 族丁（图标 + 数字）
		const setIcon = (ic: Sprite.Type | undefined, x: number, y: number) => {
			if (ic === undefined) return;
			ic.x = x;
			ic.y = y;
		};
		if (this.dayIcon !== undefined) {
			this.dayIcon.x = 20;
			this.dayIcon.y = rowY;
		}
		if (this.nightIcon !== undefined) {
			this.nightIcon.x = 20;
			this.nightIcon.y = rowY;
		}
		if (this.dayIcon !== undefined) this.topLabel.x = 50;

		setIcon(this.silverIcon, w - 470, rowY);
		this.silverLabel.x = this.silverIcon === undefined ? w - 470 : w - 444;
		this.silverLabel.y = rowY;

		setIcon(this.grainIcon, w - 330, rowY);
		this.foodLabel.x = this.grainIcon === undefined ? w - 330 : w - 304;
		this.foodLabel.y = rowY;

		setIcon(this.popIcon, w - 200, rowY);
		this.popLabel.x = this.popIcon === undefined ? w - 200 : w - 174;
		this.popLabel.y = rowY;

		this.skipDayBtn.x = w - 130;
		this.skipDayBtn.y = h - 50;

		this.toastLabel.x = w / 2;
		this.toastLabel.y = h - 102;

		// 底部操作条
		this.bottomBg.clear();
		if (this.bottomBarArt === undefined) {
			drawRect(this.bottomBg, 0, 0, w, BOTTOM_BAR_HEIGHT, 0xcc1a202c);
			drawRect(this.bottomBg, 0, BOTTOM_BAR_HEIGHT - 2, w, 2, 0xff4a5568);
		} else {
			this.bottomBarArt.size = Size(w, BOTTOM_BAR_HEIGHT);
		}

		this.hintLabel.x = 20;
		this.hintLabel.y = 48;
		this.controlsLabel.x = 20;
		this.controlsLabel.y = 20;

		const rightEdge = w - 320;
		for (let i = 0; i < this.skillButtons.length; i++) {
			this.skillButtons[i].x = rightEdge + i * 104;
			this.skillButtons[i].y = 18;
		}

		this.extraActionNode.x = 20;
		this.extraActionNode.y = 86;

		// 胜利战报弹窗
		const boxW = Math.min(700, w - 60);
		const boxH = Math.min(380, h - 100);
		const boxX = (w - boxW) / 2;
		const boxY = (h - boxH) / 2;

		this.modalDim.clear();
		drawRect(this.modalDim, 0, 0, w, h, 0xaa000000);

		this.victoryBox.clear();
		if (this.modalArt === undefined) {
			drawRect(this.victoryBox, boxX, boxY, boxW, boxH, 0xff1a202c, 0xfff6ad55);
		} else {
			this.modalArt.x = boxX;
			this.modalArt.y = boxY;
			this.modalArt.size = Size(boxW, boxH);
		}

		this.victoryTitleLabel.x = w / 2;
		this.victoryTitleLabel.y = boxY + boxH - 60;
		this.victoryBodyLabel.x = w / 2;
		this.victoryBodyLabel.y = boxY + boxH / 2 - 5;
		this.victoryBodyLabel.textWidth = boxW - 100;
		this.confirmBtn.x = w / 2 - 110;
		this.confirmBtn.y = boxY + 30;
	}

	public showToast(msg: string, duration = 3.0): void {
		this.toastLabel.text = msg;
		this.toastLabel.visible = true;
		this.toastTimer = duration;
	}

	public showVictoryModal(wave: NightWaveConfig): void {
		this.victoryTitleLabel.text = `${wave.title} · 捷报`;
		this.victoryBodyLabel.text =
			`${wave.historicalNote}\n\n` +
			`${wave.victorySpeech}\n\n` +
			`【战果赏银】 +${wave.rewardSilver} 白银`;
		this.victoryModal.visible = true;
	}

	public update(dt: number, nearestLandmark: LandmarkId | undefined, enemyCount: number): void {
		if (this.toastTimer > 0) {
			this.toastTimer = Math.max(0, this.toastTimer - dt);
			if (this.toastTimer === 0) {
				this.toastLabel.visible = false;
			}
		}

		const gs = GameState.instance;
		const phaseText =
			gs.phase === 'DAY'
				? `白昼经营 (${Math.ceil(gs.dayTimer)}s)`
				: `黑夜抗倭 (余贼 ${enemyCount})`;

		this.topLabel.text = `第 ${gs.day}/${GameConfig.TOTAL_NIGHTS} 夜 · ${phaseText}`;
		this.topLabel.color = Color(0xfffefcbf);

		if (this.dayIcon !== undefined) this.dayIcon.visible = gs.phase === 'DAY';
		if (this.nightIcon !== undefined) this.nightIcon.visible = gs.phase === 'NIGHT';

		this.silverLabel.text = `${gs.silver}`;
		this.foodLabel.text = `${gs.food}${gs.isLowFood ? ' 断粮!' : ''}`;
		this.foodLabel.color = Color(gs.isLowFood ? 0xfffc8181 : 0xfffefcbf);
		this.popLabel.text = `${gs.populationCount}/${gs.maxPopulation}`;

		this.statusLabel.text =
			`宗祠: ${gs.ancestralHallHp}/${gs.ancestralHallMaxHp}   ` +
			`东门瓮城(${gs.eastGateOpen ? '开' : '闭'}): ${gs.eastGateHp}/${gs.eastGateMaxHp}   ` +
			`内城水门: ${gs.innerGateHp}/${gs.innerGateMaxHp}   ` +
			`农:${gs.getRoleCount('FARMER')} 灶:${gs.getRoleCount('SALT_WORKER')} 工:${gs.getRoleCount('BUILDER')} 兵:${gs.getRoleCount('MILITIA') + gs.getRoleCount('KUNG_FU')}`;

		this.skipDayBtn.visible = gs.phase === 'DAY' && !this.victoryModal.visible;

		if (nearestLandmark !== this.currentLandmark) {
			this.currentLandmark = nearestLandmark;
			this.rebuildExtraButtons(nearestLandmark);
		}

		if (nearestLandmark) {
			const lm = GameConfig.MAP_LANDMARKS[nearestLandmark];
			this.hintLabel.text = `【${lm.name}】${lm.interactHint}`;
		} else {
			this.hintLabel.text = '沿永昌堡巡视防务：前往宗祠募丁、水田/盐课司造具、东门控制闸门。';
		}
	}

	private rebuildExtraButtons(landmark: LandmarkId | undefined): void {
		this.extraActionNode.removeAllChildren();
		if (!landmark) return;

		if (landmark === 'ANCESTRAL_HALL') {
			const b1 = createButton('招募族丁 (80银)', 155, 34, 0xff2b6cb0, () => this.callbacks.onInteract(0), 13);
			const b2 = createButton('升级宗祠 (+4人口)', 165, 34, 0xff805ad5, () => this.callbacks.onInteract(1), 13);
			b2.x = 165;
			this.extraActionNode.addChild(b1);
			this.extraActionNode.addChild(b2);
		} else if (landmark === 'INNER_GATE') {
			const b1 = createButton('置办木锤 (70银)', 155, 34, 0xffdd6b20, () => this.callbacks.onInteract(0), 13);
			const b2 = createButton('解锁内城炮台 (150银)', 180, 34, 0xff4a5568, () => this.callbacks.onInteract(1), 13);
			b2.x = 165;
			this.extraActionNode.addChild(b1);
			this.extraActionNode.addChild(b2);
		} else if (landmark === 'MAIN_WALL') {
			const b1 = createButton('置办长枪 (75银)', 155, 34, 0xff3182ce, () => this.callbacks.onInteract(0), 13);
			const b2 = createButton('置办拳谱 (110银)', 165, 34, 0xffe53e3e, () => this.callbacks.onInteract(1), 13);
			b2.x = 165;
			this.extraActionNode.addChild(b1);
			this.extraActionNode.addChild(b2);
		} else if (landmark === 'EAST_GATE') {
			const b1 = createButton('开关东门', 115, 34, 0xff2f855a, () => this.callbacks.onInteract(0), 13);
			const b2 = createButton('加固东门/敌台', 145, 34, 0xff805ad5, () => this.callbacks.onInteract(1), 13);
			b2.x = 125;
			this.extraActionNode.addChild(b1);
			this.extraActionNode.addChild(b2);
		}
	}
}
