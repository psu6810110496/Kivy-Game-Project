from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
import os

class ObstacleWidget(Widget):
    TEXTURE_H = None
    TEXTURE_V = None

    def __init__(self, pos=(0, 0), size=(120, 70), **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        super().__init__(**kwargs)
        self.pos = pos
        self.size = size

        # ตรวจสอบแนวของรถ: กว้าง > สูง = แนวนอน, สูง > กว้าง = แนวตั้ง
        self.is_horizontal = size[0] > size[1]

        # โหลด Texture ตามแนว
        self._load_textures()

        with self.canvas:
            Color(1, 1, 1, 1)
            tex = ObstacleWidget.TEXTURE_H if self.is_horizontal else ObstacleWidget.TEXTURE_V
            
            if tex:
                self.rect = Rectangle(pos=self.pos, size=self.size, texture=tex)
            else:
                # Fallback if no image found
                Color(0.2, 0.2, 0.3, 1) if self.is_horizontal else Color(0.3, 0.2, 0.2, 1)
                self.rect = Rectangle(pos=self.pos, size=self.size)

    def _load_textures(self):
        if self.is_horizontal and ObstacleWidget.TEXTURE_H is None:
            path = "assets/maps/car_h.png"
            if not os.path.exists(path): path = "assets/maps/wrecked_car.png" # Fallback
            if os.path.exists(path):
                try: ObstacleWidget.TEXTURE_H = CoreImage(path).texture
                except: pass
        
        if not self.is_horizontal and ObstacleWidget.TEXTURE_V is None:
            path = "assets/maps/car_v.png"
            if not os.path.exists(path): path = "assets/maps/wrecked_car.png" # Fallback
            if os.path.exists(path):
                try: ObstacleWidget.TEXTURE_V = CoreImage(path).texture
                except: pass

    def collides_with(self, x, y, bw=64, bh=64):
        """AABB Collision Check"""
        return not (
            x + bw < self.pos[0] or
            x > self.pos[0] + self.size[0] or
            y + bh < self.pos[1] or
            y > self.pos[1] + self.size[1]
        )
