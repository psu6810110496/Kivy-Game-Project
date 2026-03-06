"""game/player.py"""
from game.skills import CHAR_SKILL3, CHAR_SPEED_CAP


class PlayerStats:
    def __init__(
        self, name: str, hp: float, speed: float, damage: float,
        idle_frames: list, walk_frames: list,
        skill_loadout: list | None = None,
        size: tuple = (64, 64),
        melee_cooldown: float = 0.5,
    ):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.damage = damage
        self.size = size
        self.melee_cooldown = melee_cooldown   # ใช้ใน engine.perform_melee_attack
        self.idle_frames = idle_frames
        self.walk_frames = walk_frames
        self.skill_loadout = skill_loadout
        self.speed_cap = CHAR_SPEED_CAP.get(name, 10.0)
        self.reset()

    def reset(self):
        self.current_hp = self.hp
        self.level = 1
        self.exp = 0.0
        self.max_exp = 300.0

        # ไม่มีสกิลเริ่มต้น — ได้จาก Level Up เท่านั้น
        self.skills = []    # auto skills (S1, S2)
        self.skill3 = None  # manual/stack skill (S3)
        # (melee ถูกจัดการโดย engine.perform_melee_attack โดยตรง ไม่ต้องเก็บ object)

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0

    def heal(self, amount: float):
        self.current_hp = min(self.hp, self.current_hp + amount)
