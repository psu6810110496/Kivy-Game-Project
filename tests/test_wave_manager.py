import pytest
from unittest.mock import MagicMock, patch
from game.wave_manager import WaveManager

class MockGame:
    def __init__(self):
        self.enemies = []
        self.world_layout = MagicMock()
        self.hud = MagicMock()
        self.boss = None
        self.big_boss = None

class test_wave_manager_init():
    game = MockGame()
    wm = WaveManager(game)
    assert wm.game == game
    assert wm.current_wave == 1

@patch('game.wave_manager.resolve_path', return_value="dummy_path")
@patch('game.wave_manager.CoreImage')
def test_wave_manager_get_title(mock_core_image, mock_resolve):
    game = MockGame()
    wm = WaveManager(game)
    
    title = wm._get_wave_title(1)
    assert "Wave 1" in title
    
    title = wm._get_wave_title(10)
    assert "BOSS" in title.upper()
    
    title = wm._get_wave_title(45)
    assert "FINAL BOSS" in title.upper()

def test_enemy_spawn_counts():
    game = MockGame()
    wm = WaveManager(game)
    
    # Wave 1: Normal enemies
    # _get_spawn_count(1, "normal") -> 5 + (1-1)*1 = 5
    assert wm._get_spawn_count(1, "normal") == 5
    
    # Wave 5: Stalkers
    # _get_spawn_count(5, "stalker") -> 2 + (5-5)*1.2 = 2
    assert wm._get_spawn_count(5, "stalker") == 2
    
    # Wave 10: Boss
    assert wm._get_spawn_count(10, "boss") == 1

@patch('game.enemy_widget.EnemyWidget')
def test_spawn_enemies_regular_wave(mock_enemy_widget):
    game = MockGame()
    wm = WaveManager(game)
    
    # Simulate spawning for Wave 1
    wm._spawn_enemies(1)
    # Wave 1 spawned 5 normal enemies
    assert mock_enemy_widget.call_count == 5
