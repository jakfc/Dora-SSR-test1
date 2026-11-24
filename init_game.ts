// 临时预览入口：直接进入游戏场景，方便截图核对美术接入效果。
// 仅用于本地验证（`dora cli agent preview --entry init_game`），验证完可删。
import { Director } from 'Dora';
import { GameState } from 'src/config/GameState';
import { SceneManager } from 'src/scenes/SceneManager';
import { TitleScene } from 'src/scenes/TitleScene';
import { GameScene } from 'src/scenes/GameScene';
import { GameOverScene } from 'src/scenes/GameOverScene';

SceneManager.register('TITLE', TitleScene);
SceneManager.register('GAME', GameScene);
SceneManager.register('GAMEOVER', () => GameOverScene(GameState.instance.isVictory));

GameState.instance.reset();
SceneManager.start('GAME');

Director.entry.onUpdate(() => {
	SceneManager.tick();
	return false;
});
