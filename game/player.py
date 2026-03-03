from game.skills import AxeTSkill, SlashSkill, AoESkill, CHAR_DEFAULT_SKILLS


class PlayerStats:
    def __init__(self, name, hp, speed, damage, idle_frames, walk_frames, skill_loadout=None):
        self.name = name
        self.hp = hp
        self.speed = speed
        self.damage = damage
        self.idle_frames = idle_frames
        self.walk_frames = walk_frames
        # สามารถกำหนด skill_loadout เป็น list ของคลาสสกิลต่อ Player ได้ (ขยายสเกลง่าย)
        self.skill_loadout = skill_loadout
        self.reset()

    def reset(self):
        self.current_hp = self.hp
        self.level = 1
        self.exp = 0
        self.max_exp = 100

        # เลือกสกิลเริ่มต้นตามตัวละคร / loadout
        if self.skill_loadout:
            base_skills = self.skill_loadout
        else:
            base_skills = CHAR_DEFAULT_SKILLS.get(self.name, [])

        self.skills = [cls() for cls in base_skills]