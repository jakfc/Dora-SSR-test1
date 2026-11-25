// @preview-file on clear
import { Director } from 'Dora';
import { GameState } from 'src/config/GameState';
import { SceneManager } from 'src/scenes/SceneManager';
import { soundPreload, soundTick } from 'src/audio/Sound';
import { TitleScene } from 'src/scenes/TitleScene';
import { GameScene } from 'src/scenes/GameScene';
import { GameOverScene } from 'src/scenes/GameOverScene';

SceneManager.register('TITLE', TitleScene);
SceneManager.register('GAME', GameScene);
SceneManager.register('GAMEOVER', () => GameOverScene(GameState.instance.isVictory));

GameState.instance.reset();
soundPreload();
SceneManager.start('TITLE');

// 屏幕自适应：每帧跟随窗口尺寸更新缩放，并把场景根节点定位到可视区域左下角
// 窗口尺寸变化时由 SceneManager.tick() 自动重排当前场景
Director.entry.onUpdate((dt: number) => {
	SceneManager.tick();
	soundTick(dt);
	return false;
});
