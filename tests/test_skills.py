import pytest
from unittest.mock import MagicMock
from game.skills import BaseSkill, StackSkill, DinoCircle, DinoSummon

class MockGame:
    def __init__(self):
        self.enemies = [MagicMock()]
        self.player_pos = [0, 0]
        self.player_stats = MagicMock()
        self.player_stats.damage = 10
        self.mouse_dir = [1, 0]
        self.world_layout = MagicMock()
        self.player_bullets = []

def test_base_skill_cooldown():
    skill = BaseSkill()
    skill.level = 1
    assert skill.cooldown == 2.0
    
    skill.tick(1.0, MockGame())
    assert skill._timer == 1.0 # 2.0 - 1.0 (assuming it was reset)
    # Note: BaseSkill.tick logic: self._timer -= dt; if <=0: activate(); _timer = cooldown

def test_stack_skill():
    skill = StackSkill()
    skill.stacks = 3
    
    game = MockGame()
    assert skill.manual_activate(game) is True
    assert skill.stacks == 2
    
    skill.manual_activate(game)
    skill.manual_activate(game)
    assert skill.stacks == 0
    assert skill.manual_activate(game) is False

def test_dino_circle_upgrade():
    skill = DinoCircle()
    assert skill.dino_count == 1
    
    skill.level = 5
    skill._on_upgrade()
    # dino_count = 1 + (5//2) + (5//12) = 1 + 2 + 0 = 3
    assert skill.dino_count == 3

def test_dino_summon_cooldown():
    skill = DinoSummon()
    initial_cd = skill.cooldown
    
    skill.level = 2
    skill._on_upgrade()
    new_cd = skill.cooldown
    assert new_cd < initial_cd
