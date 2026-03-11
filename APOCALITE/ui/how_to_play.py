from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Rectangle, Color
from kivy.core.window import Window
from ui.font import PIXEL_FONT
from ui.main_menu import RainEffect
from kivy.uix.widget import Widget

class HowToPlayScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next_screen = "char_select_screen"
        
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = Rectangle(source="assets/Menu/MenuTest.png", pos=self.pos, size=Window.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        root = FloatLayout()
        root.add_widget(RainEffect())
        
        # Black overlay for readability
        overlay = Widget()
        with overlay.canvas:
            Color(0, 0, 0, 0.7)
            self.overlay_rect = Rectangle(pos=self.pos, size=Window.size)
        root.add_widget(overlay)
        self.bind(pos=self._update_overlay, size=self._update_overlay)
        
        content = BoxLayout(orientation='vertical', padding=[50, 50], spacing=20, 
                            size_hint=(0.8, 0.8), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        
        content.add_widget(Label(
            text="HOW TO PLAY", font_size=72, font_name=PIXEL_FONT,
            color=(1, 0.8, 0.2, 1), size_hint_y=0.2
        ))
        
        instructions = (
            "[b][color=ffcc00]MOVEMENT:[/color][/b]\n"
            "WASD to Move\n"
            "Space to Dash\n\n"
            "[b][color=ffcc00]COMBAT:[/color][/b]\n"
            "Auto-attack melee nearest enemies\n"
            "Mouse to Aim\n"
            "Left Click to use Skill 3\n\n"
            "[b][color=ffcc00]PROGRESSION:[/color][/b]\n"
            "Collect EXP Orbs or Eliminate enemies to Level Up\n"
            "Choose Upgrades to get stronger\n"
            "Survive the waves and defeat bosses!"
        )
        
        desc = Label(
            text=instructions, markup=True, font_size=32, font_name=PIXEL_FONT,
            halign='center', valign='middle', line_height=1.2
        )
        desc.bind(size=desc.setter('text_size'))
        content.add_widget(desc)
        
        btn_start = Button(
            text="[ UNDERSTOOD ]", font_size=40, font_name=PIXEL_FONT,
            size_hint=(0.4, 0.15), pos_hint={'center_x': 0.5},
            background_normal='', background_color=(0.2, 0.6, 0.2, 0.8),
            color=(1, 1, 1, 1)
        )
        btn_start.bind(on_release=self.go_next)
        content.add_widget(btn_start)
        
        root.add_widget(content)
        self.add_widget(root)

    def _update_bg(self, i, v): self.bg.pos = i.pos; self.bg.size = i.size
    def _update_overlay(self, i, v): self.overlay_rect.pos = i.pos; self.overlay_rect.size = i.size

    def go_next(self, *args):
        self.manager.current = self.next_screen

    def on_enter(self):
        Window.bind(on_key_down=self._on_key_down)

    def on_leave(self):
        Window.unbind(on_key_down=self._on_key_down)

    def _on_key_down(self, window, key, *args):
        # 32 = Space, 13 = Enter
        if key in (32, 13):
            self.go_next()
            return True
        # 27 = ESC -> Return to menu
        elif key == 27:
            self.manager.current = "main_menu"
            return True
        return False
