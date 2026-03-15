import pytest
from unittest.mock import MagicMock, patch
from game.combat_manager import CombatManager

class MockGame:
    def __init__(self):
        self.player_pos = [100, 100]
        self.player_stats = MagicMock()
        self.player_stats.hp = 100
        self.player_stats.hp_max = 100
        self.player_stats.damage = 10
        self.player_stats.exp = 0
        self.player_stats.level = 1
        self.enemies = []
        self.player_bullets = []
        self.enemy_projectiles = []
        self.pickups = []
        self.exp_orbs = []
        self.world_layout = MagicMock()
        self.hud = MagicMock()

    def spawn_exp_orb(self, pos): pass
    def spawn_drop_item(self, pos): pass
    def gain_exp(self, amount): pass
    def take_damage(self, amount): pass

class MockEnemy:
    def __init__(self, pos=(0, 0), hp=50):
        self.pos = pos
        self.hp = hp
        self.enemy_size = (64, 64)
        self.is_dead = False
        self.parent = MagicMock()

    def take_damage(self, dmg):
        self.hp -= dmg

class MockBullet:
    def __init__(self, pos=(0, 0), damage=10):
        self.pos = pos
        self.damage = damage
        self.parent = MagicMock()

def test_combat_manager_init():
    game = MockGame()
    cm = CombatManager(game)
    assert cm.game == game

def test_bullet_enemy_collision():
    game = MockGame()
    cm = CombatManager(game)
    
    enemy = MockEnemy(pos=(100, 100), hp=50)
    bullet = MockBullet(pos=(110, 110), damage=20)
    
    game.enemies.append(enemy)
    game.player_bullets.append(bullet)
    
    # Mock _hit_enemy to avoid complex VFX/sound logic
    with patch('game.skills._hit_enemy') as mock_hit:
        cm._check_player_bullets(0.016)
        # In a real scenario, _hit_enemy would be called. 
        # Since we use mocks, we check if the logic identifies the collision.
        # CombatManager uses math.hypot(bx - (ex+20), by - (ey+20)) < 45
        # bx=110, ex+20=120 -> dx = -10
        # by=110, ey+20=120 -> dy = -10
        # dist = sqrt(100+100) = 14.14 < 45 -> Collision!
        assert mock_hit.called
        assert bullet in cm.game.player_bullets # CM doesn't remove bullet immediately in this method if it continues?
        # Actually CM removes bullet from list if it hits.
        # Wait, looking at combat_manager.py:
        # for b in list(self.game.player_bullets):
        #    ... if dist < 45: _hit_enemy(...); self.game.player_bullets.remove(b); ...
        assert bullet not in cm.game.player_bullets

def test_player_pickup_collision():
    game = MockGame()
    cm = CombatManager(game)
    
    # Player at (100, 100), center (132, 132)
    # Pickup at (130, 130)
    pickup = MagicMock()
    pickup.pos = (130, 130)
    pickup.parent = MagicMock()
    game.pickups.append(pickup)
    
    # dist = hypot(132 - (130+14), 132 - (130+14))  # pickup center approx ???
    # CM uses: dist = math.hypot(px - (item.pos[0] + 14), py - (item.pos[1] + 14))
    # px = 132, py = 132. item.pos+14 = 144. 132-144 = -12.
    # dist = sqrt(144+144) = 16.97 < 40 -> Pickup!
    
    cm._check_pickups(0.016)
    assert pickup not in game.pickups
