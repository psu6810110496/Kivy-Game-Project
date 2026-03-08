import random
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.animation import Animation
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from game.sound_manager import sound_manager
from ui.font import PIXEL_FONT

class CreditsScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        
        # 1. พื้นหลังสีดำสนิท (Solid Black)
        layout = FloatLayout()
        with layout.canvas.before:
            Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(pos=(0, 0), size=Window.size)
        
        self.add_widget(layout)
        
        # 2. Credits Text Content (All White + Extra Spacing)
        credits_text = (
            "\n" * 15 +
            "[b][size=160]APOCALITE[/size][/b]\n"
            "[size=35]THE ULTIMATE SURVIVAL[/size]\n" +
            "\n" * 12 +

            "[size=60]DEVELOPMENT TEAM[/size]\n" +
            "\n" * 3 +
            "[size=45]Phuminan Jivanantapravat[/size]\n"
            "[size=30](psu6810010266)[/size]\n" +
            "\n" * 4 +
            "[size=45]Chappawit Chuchai[/size]\n"
            "[size=30](psu6810110455)[/size]\n" +
            "\n" * 4 +
            "[size=45]Phuwadon Thapthrai[/size]\n"
            "[size=30](psu6810110496)[/size]\n" +
            "\n" * 12 +

            "[size=60]GAME DESIGN & PROGRAMMING[/size]\n" +
            "\n" * 3 +
            "[size=40]Project Development Team[/size]\n"
            "[size=35]Driven by Passion for Roguelikes[/size]\n" +
            "\n" * 12 +

            "[size=60]RESOURCES & ENGINE[/size]\n" +
            "\n" * 3 +
            "[size=40]Powered by Kivy 2.3 Framework[/size]\n"
            "[size=35]Custom Sprites, Effects & Skills[/size]\n"
            "[size=35]Assembled specifically for this adventure[/size]\n" +
            "\n" * 12 +

            "[size=60]SPECIAL THANKS[/size]\n" +
            "\n" * 3 +
            "[size=45]YOU[/size]\n"
            "[size=35]for surviving the Apocalypse[/size]\n"
            "[size=40]Thank you for playing our game![/size]\n" +
            "\n" * 15 +
            
            "[size=50]- THE END -[/size]\n"
            "[size=28]YOU ARE THE TRUE SURVIVOR[/size]\n" +
            "\n" * 10
        )
        
        # ฟ้อนต์ถูก register ไว้แล้วใน ui.font

        # Create Scrolling Label
        self.credits_label = Label(
            text=credits_text,
            markup=True,
            halign='center',
            valign='top',
            size_hint=(1, None),
            height=6500, # เพิ่มความสูงเล็กน้อย
            pos_hint={'center_x': 0.5},
            y=-6500,    # เริ่มที่ต่ำกว่าขอบล่าง
            font_name=PIXEL_FONT,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(self.credits_label)
        
        # ── ANIMATION ──
        # ส่วนที่ 1: พุ่งขึ้นมาเร็วๆ ในช่วงแรก (2 วินาที) เพื่อให้ชื่อเกมโผล่ขึ้นมาทันใจ
        # เราจะเลื่อนขึ้นมาประมาณ 1500 pixel เพื่อให้หัวข้อแรกเริ่มปรากฏ
        anim_fast = Animation(y=-5000, duration=2.5, t='out_quad')
        
        # ส่วนที่ 2: ค่อยๆ เลื่อนขึ้นช้าๆ แบบ Cinematic (ค่อยๆ ไหลไปเรื่อยๆ)
        anim_slow = Animation(y=Window.height + 500, duration=70, t='linear')
        
        # เชื่อมอนิเมชั่นเข้าด้วยกัน
        anim_fast.bind(on_complete=lambda *args: anim_slow.start(self.credits_label))
        anim_slow.bind(on_complete=self.return_to_menu)
        
        # เริ่มเล่น!
        anim_fast.start(self.credits_label)
        
        Window.bind(on_key_down=self._on_key_down)

    def _on_key_down(self, _win, key, *args):
        if key in (27, 32): # Esc or Space
            self.return_to_menu()
            return True
        return False

    def return_to_menu(self, *args):
        Window.unbind(on_key_down=self._on_key_down)
        Animation.stop_all(self.credits_label)
        
        from ui.game_over import GameOverPopup
        from kivy.clock import Clock
        
        if self.manager:
            game_screen = self.manager.get_screen("game_screen")
            popup = GameOverPopup(win=True, game_screen=game_screen)
            Clock.schedule_once(lambda dt: popup.open(), 0.1)

    def on_leave(self):
        Window.unbind(on_key_down=self._on_key_down)
        Animation.stop_all(self.credits_label)
