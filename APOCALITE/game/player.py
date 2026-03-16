"""game/player.py"""
from game.skills import CHAR_SKILL3, CHAR_SPEED_CAP


class PlayerStats:
    def __init__(
        self, name: str, hp: float, speed: float, damage: float,
        idle_frames: list, walk_frames: list,
        skill_loadout: list | None = None,
        size: tuple = (64, 64),
        melee_cooldown: float = 0.5,
        heal_small_tex: str = "",
        heal_large_tex: str = "",
    ):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.damage = damage
        self.size = size
        self.melee_cooldown = melee_cooldown   # ใช้ใน engine.perform_melee_attack
        self.heal_small_tex = heal_small_tex
        self.heal_large_tex = heal_large_tex
        self.idle_frames = idle_frames
        self.walk_frames = walk_frames
        self.skill_loadout = skill_loadout
        self.speed_cap = CHAR_SPEED_CAP.get(name, 10.0)
        self.reset()

    def reset(self):
        self.current_hp = self.hp
        self.level = 1
        self.exp = 0.0
        self.update_max_exp()

        # ไม่มีสกิลเริ่มต้น — ได้จาก Level Up เท่านั้น
        self.skills = []    # auto skills (S1, S2)
        self.skill3 = None  # manual/stack skill (S3)
        # (melee ถูกจัดการโดย engine.perform_melee_attack โดยตรง ไม่ต้องเก็บ object)

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0

    def heal(self, amount: float):
        self.current_hp = min(self.hp, self.current_hp + amount)

    def apply_level_up_bonus(self):
        """เพิ่มค่าสถานะพื้นฐานโดยอัตโนมัติเมื่อเลเวลอัป"""
        # 1. HP: เพิ่มเลือดสูงสุดและฮีลให้เต็ม
        self.hp += 20
        self.current_hp = self.hp
        
        # 2. Damage: เพิ่มพลังโจมตีพื้นฐาน
        self.damage += 2
        
        # 3. Speed: เพิ่มความเร็ว (แต่ไม่เกิน Speed Cap ของตัวละคร)
        if self.speed < self.speed_cap:
            self.speed = min(self.speed_cap, self.speed + 0.1)

    def update_max_exp(self):
        """คำนวณ EXP ที่ต้องการสำหรับเลเวลถัดไป: เก็บง่ายทั้งเกม"""
        # เริ่มต้นที่ 50 และเพิ่มขึ้นเพียงทีละ 20 ต่อเลเวล เพื่อให้เก็บเลเวลได้ไวตลอดทั้งเกม
        self.max_exp = 50.0 + (self.level - 1) * 20.0
