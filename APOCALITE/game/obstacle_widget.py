from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
import os

class ObstacleWidget(Widget):
    TEXTURE = None

    def __init__(self, pos=(0, 0), size=(120, 70), **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        super().__init__(**kwargs)
        self.pos = pos
        self.size = size

        if ObstacleWidget.TEXTURE is None:
            car_path = "assets/maps/wrecked_car.png"
            if os.path.exists(car_path):
                try:
                    ObstacleWidget.TEXTURE = CoreImage(car_path).texture
                except:
                    pass

        with self.canvas:
            Color(1, 1, 1, 1)
            if ObstacleWidget.TEXTURE:
                self.rect = Rectangle(pos=self.pos, size=self.size, texture=ObstacleWidget.TEXTURE)
            else:
                Color(0.2, 0.2, 0.2, 1)
                self.rect = Rectangle(pos=self.pos, size=self.size)

    def collides_with(self, x, y, bw=64, bh=64):
        """AABB Collision Check"""
        return not (
            x + bw < self.pos[0] or
            x > self.pos[0] + self.size[0] or
            y + bh < self.pos[1] or
            y > self.pos[1] + self.size[1]
        )
