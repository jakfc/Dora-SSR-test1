import { Color, DrawNode, Label, Node, Size, Sprite, Vec2 } from 'Dora';
import { GameConfig, LandmarkId, NightWaveConfig } from 'src/config/GameConfig';
import { GameState } from 'src/config/GameState';
import { Screen } from 'src/config/Screen';
import { artAt, artHide, artInto, artSprite, artStretch } from 'src/config/Assets';
import { soundIsMuted, soundSfx, soundToggleMuted } from 'src/audio/Sound';

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
	fontSize = 15,
	iconId: string | undefined = undefined
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

	// 按钮左侧的工具小图标（有素材才显示）
	if (iconId !== undefined) {
		const icon = artSprite(iconId);
		if (icon !== undefined) {
			icon.anchor = Vec2(0, 0.5);
			icon.x = 10;
			icon.y = h / 2;
			btn.addChild(icon);
			lbl.x = w / 2 + 13;
		}
	}

	// 悬停轻触（sfx_ui_hover 很短，靠 SFX_GAP 限流，不会连成一片）
	btn.onMouseMove(() => soundSfx('ui_hover'));
	btn.onTapEnded(() => {
		soundSfx('ui_click');
		onClick();
	});
	return btn;
}

export interface HudCallbacks {
	onSkipDay: () => void;
	onInteract: (optionIndex?: number) => void;
	/** 普通攻击：短距离平A（空格 / L / 点按“拳”键） */
	onLightAttack: () => void;
	onQilinStep: () => void;
	onRally: () => void;
	onBribe: () => void;
	onVictoryModalConfirm: () => void;
}

/** 每帧交给 HUD 的额外态势（营建进度 / 招募读秒 / 城外未归人数 / 投银与民居） */
export interface HudExtraInfo {
	projects: { label: string; pct: number; workers: number }[];
	recruitRemain: number;
	stragglers: number;
	/** 民居：住得下多少人 / 其中几间还是空地 */
	housing: number;
	emptyLots: number;
	/** 民居自然添丁进度 0~1 */
	houseSpawn: number;
	/** 当前地标的投银进度（例：「宗祠营建 12/18 两」） */
	donation: string;
}

const TOP_BAR_HEIGHT = 64;
// 底栏已取消：地平线以下是城前水面，底栏会把整条倒影盖住。
// 想找回底栏把这里改回 76 即可（技能键会自动回到底部横排）。
const BOTTOM_BAR_HEIGHT = 0;

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
	// 工具小图标（提示条左侧）与 BOSS 血条
	private readonly hintIconNode: Node.Type;
	private readonly bossBar: Node.Type;
	private readonly bossBgArt: Sprite.Type | undefined;
	private readonly bossFill: DrawNode.Type;
	private readonly bossLabel: Label.Type;
	private bossWidth = 600;

	// 营建/招募读秒面板与黄昏未归警报
	private readonly workLabel: Label.Type;
	private readonly alertLabel: Label.Type;
	private alertPulse = 0;

	private toastTimer = 0;
	private currentLandmark: LandmarkId | undefined = undefined;
	private callbacks: HudCallbacks;

	constructor(callbacks: HudCallbacks) {
		this.callbacks = callbacks;
		this.node = Node();

		// 顶栏背景（e01 贴图优先，缺素材则用方块）
		this.topBg = DrawNode();
		this.node.addChild(this.topBg);

		this.topBarArt = artStretch('ui_top_bar', Screen.uiWidth, TOP_BAR_HEIGHT);
		if (this.topBarArt !== undefined) {
			this.topBarArt.anchor = Vec2(0, 0);
			this.topBarArt.size = Size(Screen.uiWidth, TOP_BAR_HEIGHT);
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

		// 营建/招募读秒
		this.workLabel = Label('sarasa-mono-sc-regular', 14) as Label.Type;
		this.workLabel.anchor = Vec2(0, 0.5);
		this.workLabel.color = Color(0xff9ae6b4);
		this.workLabel.visible = false;
		this.node.addChild(this.workLabel);

		// 黄昏未归 / 城外遇袭警报
		this.alertLabel = Label('sarasa-mono-sc-regular', 16) as Label.Type;
		this.alertLabel.color = Color(0xfffc8181);
		this.alertLabel.textWidth = Screen.uiWidth - 80;
		this.alertLabel.visible = false;
		this.node.addChild(this.alertLabel);

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

		this.bottomBarArt =
			BOTTOM_BAR_HEIGHT > 0 ? artStretch('ui_bottom_bar', Screen.uiWidth, BOTTOM_BAR_HEIGHT) : undefined;
		if (this.bottomBarArt !== undefined) {
			this.bottomBarArt.anchor = Vec2(0, 0);
			this.bottomBarArt.size = Size(Screen.uiWidth, BOTTOM_BAR_HEIGHT);
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

		// 提示条左侧的工具图标挂点（水田→锄头、盐课司→盐铲）
		this.hintIconNode = Node();
		this.hintIconNode.visible = false;
		this.node.addChild(this.hintIconNode);

		// 倭寇大将血条（顶栏下方居中，无 BOSS 时隐藏）
		this.bossBar = Node();
		this.bossBar.visible = false;
		this.node.addChild(this.bossBar);

		this.bossFill = DrawNode();
		this.bossBar.addChild(this.bossFill);

		this.bossBgArt = artStretch('ui_boss_bar', 600, 24);
		if (this.bossBgArt !== undefined) {
			this.bossBgArt.anchor = Vec2(0, 0);
			this.bossBgArt.x = -300;
			this.bossBgArt.y = 0;
			this.bossBar.addChild(this.bossBgArt);
		}

		this.bossLabel = Label('sarasa-mono-sc-regular', 15) as Label.Type;
		this.bossLabel.anchor = Vec2(0.5, 0.5);
		this.bossLabel.color = Color(0xfffefcbf);
		this.bossLabel.y = 12;
		this.bossBar.addChild(this.bossLabel);

		// 底部右侧技能快捷按钮
		const btnE = createButton('[E] 交互', 92, 38, 0xff2f855a, () => this.callbacks.onInteract(0), 14);
		this.node.addChild(btnE);

		// 普通攻击：轻、快、可连段（麒麟步是位移重击，这个是站着也能打的平A）
		const btnP = createButton('[空格] 出拳', 100, 38, 0xff718096, () => this.callbacks.onLightAttack(), 14);
		this.node.addChild(btnP);

		const btnJ = createButton('[J] 麒麟步', 98, 38, 0xffc05621, () => this.callbacks.onQilinStep(), 14);
		this.node.addChild(btnJ);

		const btnK = createButton('[K] 集结', 92, 38, 0xff9b2c2c, () => this.callbacks.onRally(), 14);
		this.node.addChild(btnK);

		// [F] 撒银退敌：开一袋银子买命，让倭寇掉头
		const btnF = createButton('[F] 撒银', 92, 38, 0xffb7791f, () => this.callbacks.onBribe(), 14);
		this.node.addChild(btnF);

		// 静音开关：一把拧总音量，标签随状态翻转（点它切换）
		const muteLabel = Label('sarasa-mono-sc-regular', 15) as Label.Type;
		muteLabel.color = Color(0xfffefcbf);
		muteLabel.x = 22;
		muteLabel.y = 19;
		muteLabel.text = soundIsMuted() ? '音×' : '音♪';
		const btnM = Node();
		btnM.size = Size(44, 38);
		btnM.touchEnabled = true;
		const muteBg = artStretch('ui_btn_normal', 44, 38);
		if (muteBg !== undefined) {
			muteBg.anchor = Vec2(0, 0);
			muteBg.size = Size(44, 38);
			btnM.addChild(muteBg);
		} else {
			const bg = DrawNode();
			drawRect(bg, 0, 0, 44, 38, 0xff4a5568, 0xffe2e8f0);
			btnM.addChild(bg);
		}
		btnM.addChild(muteLabel);
		btnM.onMouseMove(() => soundSfx('ui_hover'));
		btnM.onTapEnded(() => {
			const muted = soundToggleMuted();
			muteLabel.text = muted ? '音×' : '音♪';
		});
		this.node.addChild(btnM);

		// 布局时再定位，这里先记录引用（静音键排在最左）
		this.skillButtons = [btnM, btnE, btnP, btnJ, btnK, btnF];

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
		// HUD 属于 UI 空间：单位就是设计单位，镜头拉近也不会把界面一起放大
		Screen.attachUi(this.node);
		const w = Screen.uiWidth;
		const h = Screen.uiHeight;

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

		this.workLabel.x = 20;
		this.workLabel.y = h - TOP_BAR_HEIGHT - 56;
		this.alertLabel.x = w / 2;
		this.alertLabel.y = h - 132;
		this.alertLabel.textWidth = w - 80;

		// 底部操作条
		this.bottomBg.clear();
		if (this.bottomBarArt === undefined) {
			drawRect(this.bottomBg, 0, 0, w, BOTTOM_BAR_HEIGHT, 0xcc1a202c);
			drawRect(this.bottomBg, 0, BOTTOM_BAR_HEIGHT - 2, w, 2, 0xff4a5568);
		} else {
			this.bottomBarArt.size = Size(w, BOTTOM_BAR_HEIGHT);
		}

		this.hintLabel.x = 20;
		this.hintLabel.y = h - TOP_BAR_HEIGHT - 92;
		this.hintIconNode.x = 16;
		this.hintIconNode.y = h - TOP_BAR_HEIGHT - 92;
		if (this.hintIconNode.visible) this.hintLabel.x = 48;
		// 底栏没了，按键提示也不能压在水面上：跟左边一列信息排在一起
		this.controlsLabel.x = 20;
		this.controlsLabel.y = h - TOP_BAR_HEIGHT - 124;

		// BOSS 血条：随窗口宽度自适应，居中贴在顶栏下方
		this.bossWidth = Math.min(600, w - 240);
		this.bossBar.x = w / 2;
		this.bossBar.y = h - TOP_BAR_HEIGHT - 30;
		if (this.bossBgArt !== undefined) {
			this.bossBgArt.size = Size(this.bossWidth, 24);
			this.bossBgArt.x = -this.bossWidth / 2;
		}

		// 底栏取消后，技能键改到右上角竖排，下方整条水面留空给倒影
		const skillGap = 8;
		let skillY = h - TOP_BAR_HEIGHT - 12 - 38;
		for (let i = 0; i < this.skillButtons.length; i++) {
			const skillBtn = this.skillButtons[i];
			const btnW = skillBtn.size.width > 0 ? skillBtn.size.width : 92;
			skillBtn.x = w - 20 - btnW;
			skillBtn.y = skillY;
			skillY -= 38 + skillGap;
		}

		this.extraActionNode.x = 20;
		this.extraActionNode.y = h - TOP_BAR_HEIGHT - 12;

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

	public update(
		dt: number,
		nearestLandmark: LandmarkId | undefined,
		enemyCount: number,
		bossHp = 0,
		bossMaxHp = 0,
		bossName = '',
		info?: HudExtraInfo
	): void {
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

		this.silverLabel.text = `${gs.silver} ${GameConfig.SILVER_NAME}`;
		this.foodLabel.text = `${gs.food}${gs.isLowFood ? ' 断粮!' : ''}`;
		this.foodLabel.color = Color(gs.isLowFood ? 0xfffc8181 : 0xfffefcbf);
		this.popLabel.text = `${gs.populationCount}/${gs.maxPopulation}`;

		this.statusLabel.text =
			`宗祠: ${gs.ancestralHallHp}/${gs.ancestralHallMaxHp}   ` +
			`东门瓮城(${gs.eastGateOpen ? '开' : '闭'}): ${gs.eastGateHp}/${gs.eastGateMaxHp}   ` +
			`内城水门: ${gs.innerGateHp}/${gs.innerGateMaxHp}   ` +
			`农:${gs.getRoleCount('FARMER')} 灶:${gs.getRoleCount('SALT_WORKER')} 工:${gs.getRoleCount('BUILDER')} 兵:${gs.getRoleCount('MILITIA') + gs.getRoleCount('KUNG_FU')}`;

		this.skipDayBtn.visible = gs.phase === 'DAY' && !this.victoryModal.visible;

		// 营建 / 招募读秒 / 投银 / 民居添丁
		if (info !== undefined) {
			const parts: string[] = [];
			for (const p of info.projects) {
				const pct = Math.max(0, Math.min(100, Math.floor(p.pct * 100)));
				parts.push(`施工 ${p.label} ${pct}%${p.workers > 0 ? ` (匠${p.workers})` : ' (无匠)'}`);
			}
			if (info.recruitRemain > 0) parts.push(`募丁中 ${info.recruitRemain.toFixed(1)}s`);
			if (info.donation.length > 0) parts.push(`捐银 ${info.donation}`);
			if (info.emptyLots > 0) {
				parts.push(`民居空地 ${info.emptyLots} 处待投银起造（住房 ${info.housing}）`);
			} else if (info.houseSpawn > 0) {
				parts.push(`民居添丁 ${Math.floor(info.houseSpawn * 100)}%`);
			}
			if (parts.length > 0) {
				this.workLabel.text = parts.join('   ·   ');
				this.workLabel.visible = true;
			} else {
				this.workLabel.visible = false;
			}
		} else {
			this.workLabel.visible = false;
		}

		// 黄昏未归 / 城外遇袭警报（闪烁）
		this.alertPulse += dt * 5;
		const dangerWindow = gs.phase === 'NIGHT' || gs.dayTimer <= GameConfig.DUSK_RETURN_SECONDS;
		if (info !== undefined && info.stragglers > 0 && dangerWindow) {
			this.alertLabel.visible = Math.sin(this.alertPulse) > -0.35;
			this.alertLabel.text =
				gs.phase === 'NIGHT'
					? `⚔ 城外还有 ${info.stragglers} 名族人正遭倭寇追杀！`
					: `⚠ 黄昏将至，城外还有 ${info.stragglers} 名族人未归（[K] 鸣鼓召回）`;
		} else {
			this.alertLabel.visible = false;
		}

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

		// 提示条上的工具图标：水田→锄头、盐课司→盐铲
		const toolIconId =
			nearestLandmark === 'WEST_PADDY' || nearestLandmark === 'EAST_PADDY'
				? 'icon_tool_hoe'
				: (nearestLandmark === 'SALT_OFFICE' ? 'icon_tool_shovel' : undefined);
		if (toolIconId === undefined) {
			artHide(this.hintIconNode);
		} else {
			artInto(this.hintIconNode, toolIconId);
		}
		this.hintLabel.x = this.hintIconNode.visible ? 48 : 20;

		// BOSS 血条：仅在大将存活时显示
		const bossAlive = bossMaxHp > 0 && bossHp > 0;
		this.bossBar.visible = bossAlive;
		if (bossAlive) {
			const ratio = Math.max(0, Math.min(1, bossHp / bossMaxHp));
			this.bossFill.clear();
			drawRect(
				this.bossFill,
				-this.bossWidth / 2 + 3,
				3,
				(this.bossWidth - 6) * ratio,
				18,
				0xffe53e3e,
				0xff7b341e
			);
			this.bossLabel.text = `${bossName}  ${Math.ceil(bossHp)}/${bossMaxHp}`;
		}
	}

	private rebuildExtraButtons(landmark: LandmarkId | undefined): void {
		this.extraActionNode.removeAllChildren();
		if (!landmark) return;
		const gs = GameState.instance;

		if (landmark === 'ANCESTRAL_HALL') {
			const b1 = createButton(
				`招募族丁 (${GameConfig.RECRUIT_VILLAGER_COST}两)`,
				155,
				34,
				0xff2b6cb0,
				() => this.callbacks.onInteract(0),
				13
			);
			const b2 = createButton(
				`升级宗祠 Lv.${gs.ancestralHallLevel}→${Math.min(
					gs.ancestralHallLevel + 1,
					GameConfig.ANCESTRAL_HALL_MAX_LEVEL
				)} (士气↑)`,
				165,
				34,
				0xff805ad5,
				() => this.callbacks.onInteract(1),
				13
			);
			b2.x = 165;
			this.extraActionNode.addChild(b1);
			this.extraActionNode.addChild(b2);
		} else if (landmark === 'INNER_GATE') {
			const innerTower = gs.towers.find((t) => t.id === 'INNER_TOWER');
			const towerUnlocked = innerTower !== undefined && innerTower.unlocked;
			const innerTowerCost = GameConfig.TOWER_SLOTS.find((s) => s.id === 'INNER_TOWER')?.unlockCost ?? 0;
			const b1 = createButton(
				`置办木锤 (${GameConfig.ROLES.BUILDER.toolCost}两)`,
				155,
				34,
				0xffdd6b20,
				() => this.callbacks.onInteract(0),
				13,
				'icon_tool_hammer'
			);
			const b2 = createButton(
				towerUnlocked ? `内城炮台 Lv.${gs.innerGateLevel}` : `解锁内城炮台 (${innerTowerCost}两)`,
				160,
				34,
				0xff4a5568,
				() => this.callbacks.onInteract(1),
				13
			);
			b2.x = 155;
			const b3 = createButton(
				`加固水门 Lv.${gs.innerGateLevel}→${Math.min(gs.innerGateLevel + 1, GameConfig.INNER_GATE_MAX_LEVEL)}`,
				170,
				34,
				0xff805ad5,
				() => this.callbacks.onInteract(2),
				13
			);
			b3.x = 315;
			this.extraActionNode.addChild(b1);
			this.extraActionNode.addChild(b2);
			this.extraActionNode.addChild(b3);
		} else if (landmark === 'WEST_PADDY' || landmark === 'EAST_PADDY' || landmark === 'WEST_SALT_FLAT' || landmark === 'EAST_SALT_FLAT') {
			const isPaddy = landmark === 'WEST_PADDY' || landmark === 'EAST_PADDY';
			const kind = isPaddy ? 'PADDY' : 'SALT';
			const level = gs.landLevelOf(landmark);
			const toolText = isPaddy ? '置办锄头' : '置办盐铲';
			const toolIcon = isPaddy ? 'icon_tool_hoe' : 'icon_tool_shovel';
			const toolCost = isPaddy ? GameConfig.ROLES.FARMER.toolCost : GameConfig.ROLES.SALT_WORKER.toolCost;
			const b1 = createButton(
				`${toolText} (${toolCost}两)`,
				150,
				34,
				0xffdd6b20,
				() => this.callbacks.onInteract(0),
				13,
				toolIcon
			);
			const maxed = level >= GameConfig.RECLAIM.MAX_LEVEL;
			const nextCost = GameConfig.RECLAIM.COST[kind] * (level + 1);
			const b2 = createButton(
				maxed ? `熟田 Lv.${level}（已满）` : `开垦 Lv.${level}→${level + 1} (${nextCost}两)`,
				190,
				34,
				maxed ? 0xff4a5568 : 0xff2f855a,
				() => this.callbacks.onInteract(1),
				13
			);
			b2.x = 150;
			this.extraActionNode.addChild(b1);
			this.extraActionNode.addChild(b2);
		} else if (landmark === 'SALT_OFFICE') {
			const cost = GameConfig.ROLES.SALT_WORKER.toolCost;
			const b1 = createButton(
				`置办盐铲 (${cost}两)`,
				150,
				34,
				0xffdd6b20,
				() => this.callbacks.onInteract(0),
				13,
				'icon_tool_shovel'
			);
			this.extraActionNode.addChild(b1);
		} else if (landmark === 'MAIN_WALL') {
			const b1 = createButton(
				`置办长枪 (${GameConfig.ROLES.MILITIA.toolCost}两)`,
				155,
				34,
				0xff3182ce,
				() => this.callbacks.onInteract(0),
				13,
				'icon_tool_spear'
			);
			const b2 = createButton(
				`置办拳谱 (${GameConfig.ROLES.KUNG_FU.toolCost}两)`,
				165,
				34,
				0xffe53e3e,
				() => this.callbacks.onInteract(1),
				13,
				'icon_tool_manual'
			);
			b2.x = 165;
			this.extraActionNode.addChild(b1);
			this.extraActionNode.addChild(b2);
		} else if (landmark === 'EAST_GATE') {
			const b1 = createButton('开关东门', 115, 34, 0xff2f855a, () => this.callbacks.onInteract(0), 13);
			const b2 = createButton('加固东门/敌台', 145, 34, 0xff805ad5, () => this.callbacks.onInteract(1), 13);
			b2.x = 125;
			this.extraActionNode.addChild(b1);
			this.extraActionNode.addChild(b2);
		} else if (landmark === 'WEST_COAST' || landmark === 'EAST_COAST') {
			const b1 = createButton('东西登岸滩头', 140, 34, 0xff4a5568, () => this.callbacks.onInteract(0), 13);
			this.extraActionNode.addChild(b1);
		}
	}
}
