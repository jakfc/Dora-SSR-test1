import { Node, Rect, Size, Sprite, Texture2D, Vec2 } from 'Dora';

/**
 * ============================================================
 *  美术资源接入层（唯一出口）
 * ============================================================
 *
 * 设计约定见 `docs/美术素材清单与AI生成规范.md`：
 *   - 所有图片放在项目根目录的 `assets/` 下，路径写在本文件的 `ART` 表里；
 *   - 表里是「设计像素」尺寸，引擎按当前窗口自动等比缩放；
 *   - 表中每一项都可缺失：文件不存在时自动回退到原来的程序化方块绘制，
 *     所以**换素材不需要改代码**，只要把同名文件放进对应路径即可。
 *
 * 换正式美术时的三种情况：
 *   1) 尺寸/构图与占位素材一致  → 直接覆盖同名文件，什么都不用改；
 *   2) 想改目标大小            → 改这一项的 h（内容显示高度）或 w（宽度）；
 *   3) 想换别的文件名/目录      → 改这一项的 path。
 *
 * padTop / padBottom 是「占位素材实测的内容空白比例」：
 * 占位图按画布底部对齐、四周留白，所以按内容高度换算画布高度。
 * 正式美术若按画布满幅绘制（推荐），把这两项删掉即可（默认 0）。
 */

/** 总开关：改成 false 可一次性回到纯程序化绘制（对比用）。 */
export const USE_ART = true;

export interface ArtSpec {
	/** 相对项目根目录的图片路径。 */
	path: string;
	/** 目标「内容」显示高度（设计像素）。按纹理比例推算宽度，不会拉伸。 */
	h?: number;
	/** 目标显示宽度（设计像素）。给了 h 时以 h 为准。 */
	w?: number;
	/** 需要由调用方在运行时设定 size 的图（背景、UI 底板等）。 */
	stretch?: boolean;
	/** 锚点，默认 (0.5, 0) 即底边水平居中，正好贴地。 */
	ax?: number;
	ay?: number;
	/** 纹理顶部/底部留白占画布的比例（占位素材实测值，正式素材填 0）。 */
	padTop?: number;
	padBottom?: number;
	/** 从纹理顶部按比例裁掉（0~1），用于「城门开启」等状态。 */
	cropTop?: number;
	/** 需要水平镜像的素材。 */
	flipX?: boolean;
}

export const ART: Record<string, ArtSpec> = {
	// ---------- 背景层 ----------
	'sky_day': { path: 'assets/bg/d01_sky_day.png', stretch: true, ax: 0, ay: 0 },
	'sky_dusk': { path: 'assets/bg/d02_sky_dusk.png', stretch: true, ax: 0, ay: 0 },
	'sky_night': { path: 'assets/bg/d03_sky_night.png', stretch: true, ax: 0, ay: 0 },
	'night_mask': { path: 'assets/bg/d07_night_mask.png', stretch: true, ax: 0, ay: 0 },
	// 地面横向平铺（每块 640x160 = 设计尺寸，正好等于 GROUND_Y）
	'ground_city': { path: 'assets/bg/d04_ground_fortress.png', w: 640, h: 160, stretch: true, ax: 0, ay: 0 },
	'ground_beach': { path: 'assets/bg/d05_ground_beach.png', w: 640, h: 160, stretch: true, ax: 0, ay: 0 },
	'horizon': { path: 'assets/bg/d06_horizon_silhouette.png', w: 1280, h: 160, stretch: true, ax: 0, ay: 0 },

	// 中景村舍 / 标题封面 / 结算画面
	'mid_houses': { path: 'assets/bg/d08_mid_houses.png', w: 1280, h: 160, stretch: true, ax: 0, ay: 0 },
	'title_bg': { path: 'assets/bg/d09_title_bg.png', stretch: true, ax: 0, ay: 0 },
	'over_victory': { path: 'assets/bg/d10_victory.png', stretch: true, ax: 0, ay: 0 },
	'over_defeat': { path: 'assets/bg/d11_defeat.png', stretch: true, ax: 0, ay: 0 },

	// ---------- 地标建筑 ----------
	'lm_ANCESTRAL_HALL': { path: 'assets/buildings/b01_shrine.png', w: 180, padBottom: 0.011 },
	'lm_ANCESTRAL_HALL_lv2': { path: 'assets/buildings/b01_shrine_lv2.png', w: 180, padBottom: 0.011 },
	'lm_PADDY_FIELD': { path: 'assets/buildings/b02_paddy.png', w: 220, padBottom: 0.045 },
	'lm_SALT_OFFICE': { path: 'assets/buildings/b03_salt_office.png', w: 170 },
	'lm_INNER_GATE': { path: 'assets/buildings/b04_inner_water_gate.png', w: 130, padBottom: 0.003 },
	'lm_INNER_GATE_broken': { path: 'assets/buildings/b04_inner_water_gate_broken.png', w: 130, padBottom: 0.003 },
	'lm_MAIN_WALL': { path: 'assets/buildings/b05_main_wall.png', w: 180 },
	'lm_EAST_GATE': { path: 'assets/buildings/b06_east_gate_barbican.png', w: 140, padBottom: 0.009 },
	// 东门开启后的状态：把画布上半部分裁掉
	'lm_EAST_GATE_open': { path: 'assets/buildings/b06_east_gate_barbican.png', w: 140, padBottom: 0.009, cropTop: 0.47 },
	// 城门被攻破（耐久归零）后的破损态
	'lm_EAST_GATE_broken': { path: 'assets/buildings/b06_east_gate_broken.png', w: 140, padBottom: 0.009 },
	// 敌台：lv1 是低矮炮台、lv2 画布更宽更高，按可见内容同宽折算保持像素比例
	'tower_arrow': { path: 'assets/buildings/b07_tower_arrow.png', w: 72 },
	'tower_cannon': { path: 'assets/buildings/b08_tower_cannon.png', w: 72, padBottom: 0.019 },
	'tower_arrow_lv2': { path: 'assets/buildings/b07_tower_arrow_lv2.png', w: 93 },
	'tower_cannon_lv2': { path: 'assets/buildings/b08_tower_cannon_lv2.png', w: 77 },

	// 远景与城外（位置已留好，丢文件即可生效；缺文件时仍用色块）
	'lm_DALUO_MOUNTAIN': { path: 'assets/bg/b09_daluo_mountain.png', h: 380 },
	'lm_OUTER_SALT_FLAT': { path: 'assets/bg/b10_outer_salt_flat.png', w: 560 },
	'lm_COAST_SPAWN': { path: 'assets/bg/b11_coast.png', w: 260 },

	// ---------- 角色 ----------
	'player_idle': { path: 'assets/sprites/player/player_idle_01.png', h: 54, padTop: 0.042, padBottom: 0.042 },
	'villager_IDLE': { path: 'assets/sprites/villagers/villager_idle_01.png', h: 50, padTop: 0.031, padBottom: 0.031 },
	'villager_FARMER': { path: 'assets/sprites/villagers/villager_farmer_01.png', h: 50, padTop: 0.031, padBottom: 0.031 },
	'villager_SALT_WORKER': { path: 'assets/sprites/villagers/villager_salt_worker_01.png', h: 50, padTop: 0.031, padBottom: 0.031 },
	'villager_BUILDER': { path: 'assets/sprites/villagers/villager_builder_01.png', h: 50, padTop: 0.031, padBottom: 0.031 },
	'villager_MILITIA': { path: 'assets/sprites/villagers/villager_militia_01.png', h: 50, padTop: 0.031, padBottom: 0.031 },
	'villager_KUNG_FU': { path: 'assets/sprites/villagers/villager_kung_fu_01.png', h: 50, padTop: 0.318, padBottom: 0.031 },
	'enemy_SCOUT': { path: 'assets/sprites/enemies/enemy_scout_01.png', h: 52, padTop: 0.156, padBottom: 0.031 },
	'enemy_SAMURAI': { path: 'assets/sprites/enemies/enemy_samurai_01.png', h: 62, padTop: 0.443, padBottom: 0.031 },
	'enemy_BOSS': { path: 'assets/sprites/enemies/enemy_boss_01.png', h: 82, padTop: 0.457, padBottom: 0.023 },

	// ---------- 投射物 / 掉落物 / 特效 ----------
	'proj_arrow': { path: 'assets/sprites/props/proj_arrow.png', h: 10, ay: 0.5 },
	'proj_cannonball': { path: 'assets/sprites/props/proj_cannonball.png', h: 14, ay: 0.5 },
	'tool_hoe': { path: 'assets/sprites/tools/tool_hoe.png', h: 26, padTop: 0.188, padBottom: 0.042 },
	'tool_shovel': { path: 'assets/sprites/tools/tool_shovel.png', h: 26, padTop: 0.083, padBottom: 0.042 },
	'tool_hammer': { path: 'assets/sprites/tools/tool_hammer.png', h: 26, padTop: 0.042, padBottom: 0.042 },
	'tool_spear': { path: 'assets/sprites/tools/tool_spear.png', h: 26, padTop: 0.042, padBottom: 0.042 },
	'tool_manual': { path: 'assets/sprites/tools/tool_manual.png', h: 26, padTop: 0.042, padBottom: 0.042 },
	'salvage_driftwood': { path: 'assets/sprites/tools/salvage_driftwood.png', h: 24 },
	'salvage_salt_bag': { path: 'assets/sprites/tools/salvage_salt_bag.png', h: 24 },
	'fx_shockwave': { path: 'assets/sprites/props/fx_shockwave.png', w: 90, h: 18, stretch: true },
	'fx_halo_loyalty': { path: 'assets/sprites/props/fx_halo_loyalty.png', w: 120, h: 120, stretch: true },
	'fx_torch_glow': { path: 'assets/sprites/props/fx_torch_glow.png', w: 130, h: 130, stretch: true },

	// 命中 / 施法特效
	'fx_slash': { path: 'assets/sprites/props/fx_slash.png', w: 110, h: 110, stretch: true },
	'fx_arrow_hit': { path: 'assets/sprites/props/fx_arrow_hit.png', w: 44, h: 44, stretch: true },
	'fx_cannon_hit': { path: 'assets/sprites/props/fx_cannon_hit.png', w: 60, h: 60, stretch: true },
	'fx_recruit': { path: 'assets/sprites/props/fx_recruit.png', h: 200 },
	'fx_levelup': { path: 'assets/sprites/props/fx_levelup.png', h: 200 },

	// ---------- HUD 底板 / 控件 ----------
	'ui_top_bar': { path: 'assets/ui/e01_top_bar.png', stretch: true, ax: 0, ay: 0 },
	'ui_bottom_bar': { path: 'assets/ui/e02_bottom_bar.png', stretch: true, ax: 0, ay: 0 },
	'ui_modal': { path: 'assets/ui/e03_modal_dialog.png', stretch: true },
	'ui_btn_normal': { path: 'assets/ui/e04_btn_normal.png', stretch: true },
	'ui_btn_hover': { path: 'assets/ui/e04_btn_hover.png', stretch: true },
	'ui_btn_pressed': { path: 'assets/ui/e04_btn_pressed.png', stretch: true },
	'ui_btn_disabled': { path: 'assets/ui/e04_btn_disabled.png', stretch: true },
	'ui_bar_health': { path: 'assets/ui/e07_bar_health.png', stretch: true, ax: 0, ay: 0 },
	'ui_bar_stamina': { path: 'assets/ui/e08_bar_stamina.png', stretch: true, ax: 0, ay: 0 },
	'ui_prompt_bubble': { path: 'assets/ui/e09_prompt_bubble.png', stretch: true },
	'ui_cursor': { path: 'assets/ui/e12_cursor.png', w: 24 },
	'ui_bar_empty': { path: 'assets/ui/e10_bar_empty.png', w: 64, h: 8, stretch: true },
	'ui_boss_bar': { path: 'assets/ui/e11_boss_bar.png', w: 600, h: 24, stretch: true },

	// ---------- HUD 图标 ----------
	'icon_day': { path: 'assets/ui/icons/icon_day.png', h: 22 },
	'icon_night': { path: 'assets/ui/icons/icon_night.png', h: 22 },
	'icon_silver': { path: 'assets/ui/icons/icon_silver.png', h: 20 },
	'icon_grain': { path: 'assets/ui/icons/icon_grain.png', h: 20 },
	'icon_population': { path: 'assets/ui/icons/icon_population.png', h: 20 },
	'icon_east_gate': { path: 'assets/ui/icons/icon_east_gate.png', h: 20 },
	'icon_water_gate': { path: 'assets/ui/icons/icon_water_gate.png', h: 20 },
	'icon_shrine': { path: 'assets/ui/icons/icon_shrine.png', h: 20 },
	'icon_tower': { path: 'assets/ui/icons/icon_tower.png', h: 20 },
	'icon_op_attack': { path: 'assets/ui/icons/icon_op_attack.png', h: 22 },
	'icon_op_build': { path: 'assets/ui/icons/icon_op_build.png', h: 22 },
	'icon_op_move': { path: 'assets/ui/icons/icon_op_move.png', h: 22 },
	'icon_op_rest': { path: 'assets/ui/icons/icon_op_rest.png', h: 22 },
	'icon_role_villager': { path: 'assets/ui/icons/icon_role_villager.png', h: 22 },
	'icon_role_farmer': { path: 'assets/ui/icons/icon_role_farmer.png', h: 22 },
	'icon_role_salt': { path: 'assets/ui/icons/icon_role_salt.png', h: 22 },
	'icon_role_builder': { path: 'assets/ui/icons/icon_role_builder.png', h: 22 },
	'icon_role_militia': { path: 'assets/ui/icons/icon_role_militia.png', h: 22 },
	'icon_role_kungfu': { path: 'assets/ui/icons/icon_role_kungfu.png', h: 22 },
	// 地标可置办的工具图标（HUD 提示用）
	'icon_tool_hoe': { path: 'assets/ui/icons/icon_tool_hoe.png', h: 22 },
	'icon_tool_shovel': { path: 'assets/ui/icons/icon_tool_shovel.png', h: 22 },
	'icon_tool_hammer': { path: 'assets/ui/icons/icon_tool_hammer.png', h: 22 },
	'icon_tool_spear': { path: 'assets/ui/icons/icon_tool_spear.png', h: 22 },
	'icon_tool_manual': { path: 'assets/ui/icons/icon_tool_manual.png', h: 22 },
};

/** 已经确认不存在的路径（避免每帧重复尝试加载）。 */
const missingPaths: Record<string, boolean> = {};

function specOf(id: string): ArtSpec | undefined {
	if (!USE_ART) return undefined;
	const spec = ART[id];
	if (spec === undefined || missingPaths[spec.path] === true) return undefined;
	return spec;
}

interface Fit {
	w: number;
	h: number;
	anchorY: number;
	crop: Rect.Type | undefined;
}

function fitOf(spec: ArtSpec, texW: number, texH: number): Fit {
	const padTop = spec.padTop ?? 0;
	const padBottom = spec.padBottom ?? 0;
	const cropTop = spec.cropTop ?? 0;
	const visible = 1 - cropTop;
	let w = 0;
	let h = 0;
	if (spec.h !== undefined) {
		// 以「内容高度」为基准，推回整张画布的显示高度
		h = (spec.h / Math.max(0.05, 1 - padTop - padBottom)) * visible;
		w = h * (texW / texH);
	} else if (spec.w !== undefined) {
		w = spec.w;
		h = w * (texH / texW) * visible;
	} else {
		w = texW;
		h = texH * visible;
	}
	const denom = cropTop > 0 ? visible : 1;
	const anchorY = spec.ay !== undefined ? spec.ay : padBottom / Math.max(0.05, denom);
	const crop = cropTop > 0 ? Rect(0, texH * cropTop, texW, texH * visible) : undefined;
	return { w, h, anchorY, crop };
}

/**
 * 按 id 造一个美术精灵（每次调用都是新实例，可重复挂到不同节点）。
 * 素材不存在时返回 undefined，调用方应回退到程序化绘制。
 */
export function artSprite(id: string, applySize = true): Sprite.Type | undefined {
	const spec = specOf(id);
	if (spec === undefined) return undefined;
	const dim = Texture2D(spec.path);
	if (dim === undefined || dim.width <= 0 || dim.height <= 0) {
		missingPaths[spec.path] = true;
		return undefined;
	}
	const sprite = Sprite(dim);
	if (sprite === undefined) {
		missingPaths[spec.path] = true;
		return undefined;
	}
	const fit = fitOf(spec, dim.width, dim.height);
	if (fit.crop !== undefined) sprite.textureRect = fit.crop;
	sprite.anchor = Vec2(spec.ax !== undefined ? spec.ax : 0.5, fit.anchorY);
	if (applySize) sprite.size = Size(fit.w, fit.h);
	if (spec.flipX === true) sprite.scaleX = -1;
	return sprite;
}

/** 素材是否存在（不产生节点）。 */
export function artReady(id: string): boolean {
	const spec = specOf(id);
	return spec !== undefined && Texture2D(spec.path) !== undefined;
}

/** 按 id 的设计显示尺寸；素材缺失时返回 undefined。 */
export function artSize(id: string): Size.Type | undefined {
	const spec = specOf(id);
	if (spec === undefined) return undefined;
	const dim = Texture2D(spec.path);
	if (dim === undefined || dim.width <= 0 || dim.height <= 0) {
		missingPaths[spec.path] = true;
		return undefined;
	}
	const fit = fitOf(spec, dim.width, dim.height);
	return Size(fit.w, fit.h);
}

/**
 * 刷新一个「美术挂点」节点：按 id 放入精灵（同一 id 会复用，不重复创建）。
 * @returns 精灵实例；素材缺失时返回 undefined —— 调用方应回退到程序化绘制。
 */
export function artInto(holder: Node.Type, id: string): Sprite.Type | undefined {
	if (holder.tag !== id) {
		holder.removeAllChildren();
		holder.tag = id;
		const sprite = artSprite(id);
		if (sprite === undefined) {
			holder.tag = '';
			holder.visible = false;
			return undefined;
		}
		sprite.tag = 'art';
		holder.addChild(sprite);
		holder.visible = true;
	}
	return holder.getChildByTag('art') as Sprite.Type | undefined;
}

/** 让精灵按朝向镜像（自动遵守素材的 flipX 约定）。 */
export function artFace(sprite: Sprite.Type, id: string, facingLeft: boolean): void {
	const spec = ART[id];
	const base = spec !== undefined && spec.flipX === true ? -1 : 1;
	sprite.scaleX = facingLeft ? -base : base;
}

/** 隐藏一个美术挂点（例如特效结束）。 */
export function artHide(holder: Node.Type): void {
	if (holder.tag !== '') {
		holder.removeAllChildren();
		holder.tag = '';
	}
	holder.visible = false;
}

/** 直接往场景里摆一个美术节点；素材缺失返回 undefined。 */
export function artAt(parent: Node.Type, id: string, x: number, y: number): Sprite.Type | undefined {
	const sprite = artSprite(id);
	if (sprite === undefined) return undefined;
	sprite.x = x;
	sprite.y = y;
	parent.addChild(sprite);
	return sprite;
}

/** 需要运行时设定尺寸的图（背景 / UI 底板）。 */
export function artStretch(id: string, w: number, h: number): Sprite.Type | undefined {
	const sprite = artSprite(id, false);
	if (sprite === undefined) return undefined;
	sprite.size = Size(w, h);
	return sprite;
}
