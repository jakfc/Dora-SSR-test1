/**
 * 音频总管（BGM / 音效）。
 *
 * 设计原则与 `Assets.ts` 一致：**素材缺了也不能崩**。
 * 音频文件不在（或叫别的名字）就静默跳过，并记在 `soundReportMissing()` 里；
 * 想换曲子只改 `BGM_FILES` / `SFX_FILES` 的文件名，玩法代码一行不用动。
 *
 * 用法：
 *   soundPreload();              // 进游戏前查一次文件在不在
 *   soundTick(dt);               // 每帧（只在 init.ts 里调一次），用来给同音效做节流
 *   soundBgm('day' | 'night' | 'title' | 'victory' | 'defeat');
 *   soundSfx('sword_slash');     // 见下面 SFX_FILES 的键名
 *   soundToggleMuted();          // 静音开关（HUD 的 [M] 键）
 */
import { Audio, Content } from 'Dora';

const SFX_DIR = 'assets/audio/sfx/';
const BGM_DIR = 'assets/audio/bgm/';

/** 音效 id -> 文件名（换素材只改这里） */
const SFX_FILES: Record<string, string> = {
	arrow_shoot: 'sfx_arrow_shoot.wav',
	arrow_hit: 'sfx_arrow_hit.wav',
	cannon_fire: 'sfx_cannon_fire.wav',
	cannon_hit: 'sfx_cannon_hit.wav',
	sword_slash: 'sfx_sword_slash.wav',
	qilin_punch: 'sfx_qilin_punch.wav',
	shockwave: 'sfx_shockwave.wav',
	hurt: 'sfx_hurt.wav',
	enemy_die: 'sfx_enemy_die.wav',
	coin_silver: 'sfx_coin_silver.wav',
	build_hammer: 'sfx_build_hammer.wav',
	farm_hoe: 'sfx_farm_hoe.wav',
	upgrade: 'sfx_upgrade.wav',
	recruit: 'sfx_recruit.wav',
	drum_rally: 'sfx_drum_rally.wav',
	gate_open: 'sfx_gate_open.wav',
	wave_horn: 'sfx_wave_horn.wav',
	ui_click: 'sfx_ui_click.wav',
	ui_hover: 'sfx_ui_hover.wav',
};

/** 背景乐 id -> 文件名 */
const BGM_FILES: Record<string, string> = {
	title: 'bgm_title.wav',
	day: 'bgm_day.wav',
	night: 'bgm_night.wav',
	victory: 'bgm_victory.wav',
	defeat: 'bgm_defeat.wav',
};

/**
 * 同一个音效两次播放的最小间隔（秒）。
 * 混战里几十个兵同时挥刀，不节流会糊成噪音又爆音。
 */
const SFX_GAP: Record<string, number> = {
	build_hammer: 0.34,
	farm_hoe: 0.4,
	sword_slash: 0.14,
	qilin_punch: 0.22,
	arrow_shoot: 0.14,
	cannon_fire: 0.3,
	hurt: 0.22,
	enemy_die: 0.05,
	coin_silver: 0.1,
	ui_hover: 0.25,
};
const SFX_GAP_DEFAULT = 0.05;

let sfxOn = true;
let bgmOn = true;
let muted = false;
let clock = 0;
let currentBgm = '';
let bgmToken = '';
/** id -> 文件在不在（查过一次就记住，避免每帧走 IO） */
const sfxReady: Record<string, boolean> = {};
const lastPlay: Record<string, number> = {};
const missing: string[] = [];

/** 进游戏前调用一次：提前确认音频文件是否存在，缺什么会在控制台报出来 */
export function soundPreload(): void {
	for (const id in SFX_FILES) {
		sfxFilePath(id);
	}
	for (const id in BGM_FILES) {
		if (!Content.exist(BGM_DIR + BGM_FILES[id])) {
			missing.push(`bgm:${id}`);
		}
	}
	if (missing.length > 0) {
		print(`[Sound] 缺少音频素材：${soundReportMissing()}`);
	}
}

/** 每帧推进内部时钟（只给节流用，不影响玩法时间） */
export function soundTick(dt: number): void {
	clock += dt;
}

function sfxFilePath(id: string): string | undefined {
	const file = SFX_FILES[id];
	if (file === undefined) return undefined;
	if (sfxReady[id] === undefined) {
		const path = SFX_DIR + file;
		const ok = Content.exist(path);
		sfxReady[id] = ok;
		if (!ok) missing.push(id);
	}
	if (sfxReady[id] !== true) return undefined;
	return SFX_DIR + file;
}

/** 放一个音效（自动节流；素材缺失或静音时什么也不做） */
export function soundSfx(id: string): void {
	if (!sfxOn || muted) return;
	const gap = SFX_GAP[id] === undefined ? SFX_GAP_DEFAULT : SFX_GAP[id];
	const last = lastPlay[id];
	if (last !== undefined && clock - last < gap) return;
	const path = sfxFilePath(id);
	if (path === undefined) return;
	lastPlay[id] = clock;
	Audio.play(path);
}

/**
 * 放一个音效，且只在镜头附近响（远处山头上的厮杀不必吵到玩家）。
 * @param x 事件世界坐标；viewCenterX/viewWidth 为当前可视区域
 */
export function soundSfxNear(id: string, x: number, viewCenterX: number, viewWidth: number): void {
	if (Math.abs(x - viewCenterX) > viewWidth * 0.62) return;
	soundSfx(id);
}

/** 切换背景乐（同一首重复调用不会重头播；素材缺失则静默） */
export function soundBgm(id: string): void {
	if (currentBgm === id) return;
	const file = BGM_FILES[id];
	if (file === undefined) return;
	const path = BGM_DIR + file;
	if (!Content.exist(path)) {
		if (missing.indexOf(`bgm:${id}`) < 0) missing.push(`bgm:${id}`);
		return;
	}
	currentBgm = id;
	bgmToken = path;
	if (bgmOn && !muted) {
		// 流式播放：BGM 有几十秒，不必整段读进内存；crossFadeTime 让换曲不突兀
		Audio.playStream(path, true, 1.0);
	}
}

export function soundStopBgm(): void {
	if (currentBgm === '') return;
	currentBgm = '';
	bgmToken = '';
	Audio.stopStream(0.8);
}

/** 静音开关：一把拧总音量，BGM 与音效同时静/响 */
export function soundSetMuted(value: boolean): void {
	muted = value;
	Audio.globalVolume = muted ? 0 : 1;
}

export function soundIsMuted(): boolean {
	return muted;
}

export function soundToggleMuted(): boolean {
	soundSetMuted(!muted);
	if (!muted && currentBgm !== '' && bgmToken !== '') {
		// 解除静音时把当前 BGM 重新推上去（静音期间可能已经换过场景）
		Audio.playStream(bgmToken, true, 0.6);
	}
	return muted;
}

export function soundSetSfxEnabled(value: boolean): void {
	sfxOn = value;
}

export function soundSetBgmEnabled(value: boolean): void {
	bgmOn = value;
	if (!value) {
		Audio.stopStream(0.4);
	} else if (!muted && bgmToken !== '') {
		Audio.playStream(bgmToken, true, 0.4);
	}
}

/** 缺哪些音频素材（逗号分隔），调试用 */
export function soundReportMissing(): string {
	let out = '';
	let i = 0;
	while (i < missing.length) {
		if (i > 0) out += ',';
		out += missing[i];
		i++;
	}
	return out;
}
