"""
game/entity.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BaseEntity — Widget พื้นฐานที่มีระบบ HP / Damage
ทุก object ในเกมที่มีชีวิต (player, enemy) ควร extend จากนี้
"""
from kivy.uix.widget import Widget


class BaseEntity(Widget):
    """Widget พื้นฐานสำหรับ entity ที่มีชีวิตในเกม"""

    def __init__(self, hp: float = 100, damage: float = 10, speed: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.hp: float = hp
        self.max_hp: float = hp
        self.damage: float = damage
        self.speed: float = speed

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: float, knockback_dir=(0, 0)):
        # เอาพวกเงื่อนไข if self.is_invincible: return ออกให้หมด
        self.hp -= amount
        # แสดงเอฟเฟกต์เลือดลดตามปกติ

    def heal(self, amount: float):
        self.hp = min(self.max_hp, self.hp + amount)
