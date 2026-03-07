from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
import os
import random

class ObstacleWidget(Widget):
    TEXTURES_H = []
    TEXTURES_V = []

    def __init__(self, pos=(0, 0), size=(140, 80), **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        super().__init__(**kwargs)
        self.pos = pos
        self.size = size

        # ตรวจสอบแนวของรถ: กว้าง > สูง = แนวนอน, สูง > กว้าง = แนวตั้ง
        self.is_horizontal = size[0] > size[1]

        # โหลด Texture แบบสุ่มจากโฟลเดอร์ car (ถ้ามี)
        self._load_textures()

        with self.canvas:
            Color(1, 1, 1, 1)
            
            # เลือกสุ่ม Texture ตามแนว
            tex = None
            if self.is_horizontal:
                if ObstacleWidget.TEXTURES_H:
                    tex = random.choice(ObstacleWidget.TEXTURES_H)
            else:
                if ObstacleWidget.TEXTURES_V:
                    tex = random.choice(ObstacleWidget.TEXTURES_V)
                elif ObstacleWidget.TEXTURES_H: # ถ้าไม่มีแนวตั้ง ใช้แนวนอนขัดตาทัพ (อาจจะเอียงถ้ารองรับ rotation)
                    tex = random.choice(ObstacleWidget.TEXTURES_H)
            
            if tex:
                self.rect = Rectangle(pos=self.pos, size=self.size, texture=tex)
            else:
                # Fallback if no image found
                Color(0.2, 0.2, 0.3, 1) if self.is_horizontal else Color(0.3, 0.2, 0.2, 1)
                self.rect = Rectangle(pos=self.pos, size=self.size)

    def _load_textures(self):
        """โหลดไฟล์แบบเข้มงวด: carv -> แนวนอน, carh -> แนวตั้ง (เท่านั้น)"""
        if ObstacleWidget.TEXTURES_H or ObstacleWidget.TEXTURES_V:
            return 

        car_dir = "assets/maps/car"
        if os.path.exists(car_dir):
            for f in os.listdir(car_dir):
                f_lower = f.lower()
                if f_lower.endswith(".png"):
                    path = os.path.join(car_dir, f).replace('\\', '/')
                    try:
                        tex = CoreImage(path).texture
                        if f_lower.startswith("carv"):
                            ObstacleWidget.TEXTURES_H.append(tex)
                        elif f_lower.startswith("carh"):
                            ObstacleWidget.TEXTURES_V.append(tex)
                    except:
                        pass
        # ลบ Fallback ทั้งหมดออกเพื่อให้ใช้แค่ไฟล์ที่กำหนดเท่านั้นตามคำสั่ง


    def collides_with(self, x, y, bw=64, bh=64):
        """AABB Collision Check"""
        return not (
            x + bw < self.pos[0] or
            x > self.pos[0] + self.size[0] or
            y + bh < self.pos[1] or
            y > self.pos[1] + self.size[1]
        )
