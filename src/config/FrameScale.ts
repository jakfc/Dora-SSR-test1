// 本文件由 tools/gen_frame_scale.py 生成，请勿手改。
// 素材换新后跑一次: python tools/gen_frame_scale.py
// 作用：同一角色族的所有动作帧在屏幕上保持同一个人高。
// 原因：引擎按 Assets.ts 的 h + padTop/padBottom 反推显示尺寸，
// 而 AI 出的帧经常把攻击/走路画成 idle 的 6~7 成高（或反过来大 4 成），
// 不补这一刀，游戏里就会出现「攻击变小」「走路一高一低」。
// 倒地帧(fall)故意不归一：躺下本来就该矮。

/** 帧路径 -> 显示倍率（1 表示无需修正）。 */
export const FRAME_SCALE: Record<string, number> = {
  'assets/sprites/enemies/enemy_boss_attack_01.png': 0.775, // attack 高171 / 人高基准132
  'assets/sprites/enemies/enemy_samurai_attack_02.png': 1.278, // attack 高79 / 人高基准101
  'assets/sprites/enemies/enemy_samurai_attack_r_02.png': 1.295, // attack 高78 / 人高基准101
  'assets/sprites/enemies/enemy_scout_attack_01.png': 1.62, // attack 高96 / 人高基准156
  'assets/sprites/enemies/enemy_scout_attack_02.png': 1.92, // attack 高81 / 人高基准156
  'assets/sprites/enemies/enemy_scout_attack_r_02.png': 1.968, // attack 高79 / 人高基准156
  'assets/sprites/player/player_attack_01.png': 1.492, // attack 高118 / 人高基准176
  'assets/sprites/player/player_attack_02.png': 1.76, // attack 高100 / 人高基准176
  'assets/sprites/player/player_attack_03.png': 1.467, // attack 高120 / 人高基准176
  'assets/sprites/player/player_hurt_01.png': 1.285, // hurt 高137 / 人高基准176
  'assets/sprites/player/player_qilin_01.png': 1.333, // qilin 高132 / 人高基准176
  'assets/sprites/player/player_qilin_02.png': 1.313, // qilin 高134 / 人高基准176
  'assets/sprites/player/player_qilin_03.png': 1.344, // qilin 高131 / 人高基准176
  'assets/sprites/villagers/villager_kung_fu_walk_01.png': 0.694, // walk 高180 / 人高基准125
  'assets/sprites/villagers/villager_kung_fu_walk_02.png': 0.694, // walk 高180 / 人高基准125
  'assets/sprites/villagers/villager_kung_fu_walk_03.png': 0.698, // walk 高179 / 人高基准125
  'assets/sprites/villagers/villager_kung_fu_walk_05.png': 0.694, // walk 高180 / 人高基准125
  'assets/sprites/villagers/villager_kung_fu_walk_06.png': 0.694, // walk 高180 / 人高基准125
  'assets/sprites/villagers/villager_militia_attack_01.png': 1.579, // attack 高114 / 人高基准180
  'assets/sprites/villagers/villager_militia_attack_02.png': 1.714, // attack 高105 / 人高基准180
};

/** 取某帧的显示倍率；表里没有就是 1。 */
export function frameScaleOf(path: string): number {
	const k = FRAME_SCALE[path];
	return k === undefined ? 1 : k;
}
