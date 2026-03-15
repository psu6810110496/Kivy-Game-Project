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

from ui.game_over import GameOverPopup

class CreditsScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        self.returning = False # 🌟 Flag เพื่อกันการเรียก return_to_menu ซ้ำซ้อน
        
        # 1. พื้นหลังสีดำสนิท (Solid Black)
        layout = FloatLayout()
        with layout.canvas.before:
            Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(pos=(0, 0), size=Window.size)
        
        self.add_widget(layout)
        
        # 2. Credits Text Content (All White + Extra Spacing)
        credits_text = (
            "[b][size=160]APOCALITE[/size][/b]\n"
            "[size=35]THE ULTIMATE SURVIVAL[/size]\n" +
            "\n" * 12 +

            "[size=60]DEVELOPMENT TEAM[/size]\n" +
            "\n" * 3 +
            "[size=45]Phuminan Jivananthapravat[/size]\n"
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
            y=-4500,    # เลื่อนจุดเริ่มต้นให้ใกล้ขอบจอมากขึ้น จะได้ไม่เกิดจอดำนาน
            font_name=PIXEL_FONT,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(self.credits_label)
        
        # ── ANIMATION ──
        # อนิเมชั่นเดียว: เลื่อนด้วยความเร็วเท่ากันตั้งแต่เริ่มจนจบ (เพิ่มเวลาเป็น 90 วินาทีเพื่อให้เลื่อนช้าลง)
        anim_all = Animation(y=Window.height + 500, duration=90.0, t='linear')
        anim_all.bind(on_complete=self.return_to_menu)
        
        # เริ่มเลื่อนทันทีที่เข้าหน้าจอ (0.1 วิ)
        Clock.schedule_once(lambda dt: anim_all.start(self.credits_label), 0.1)
        
        # 3. Label "ESC to skip this"
        self.skip_label = Label(
            text="ESC to skip this",
            font_size=24,
            font_name=PIXEL_FONT,
            color=(1, 1, 0, 0),  # สีเหลือง ซ่อนไว้ก่อน
            pos_hint={'right': 0.98, 'y': 0.02},
            size_hint=(None, None),
            size=(200, 40)
        )
        layout.add_widget(self.skip_label)
        self.hide_label_event = None
        
        Window.bind(on_key_down=self._on_key_down)
        Window.bind(mouse_pos=self._on_mouse_move)

    def _on_mouse_move(self, window, pos):
        if not getattr(self, "returning", False) and hasattr(self, "skip_label"):
            # 🌟 เมื่อขยับเมาส์ ให้แสงปรากฏขึ้นมาเป็นสีเหลือง
            self.skip_label.color = (1, 1, 0, 1)
            
            # ถ้ายกเลิกคำสั่งซ่อนเดิมที่มีอยู่
            if self.hide_label_event:
                self.hide_label_event.cancel()
                
            # ตั้งเวลาให้หายไปหลังไม่ได้ขยับเมาส์ 2 วินาที
            self.hide_label_event = Clock.schedule_once(self._hide_skip_label, 2.0)

    def _hide_skip_label(self, dt):
        if hasattr(self, "skip_label"):
            # 🌟 ปรับสีกลับเป็นโปร่งใสเมื่อไม่ได้ขยับเมาส์
            self.skip_label.color = (1, 1, 0, 0)

    def _on_key_down(self, _win, key, *args):
        if key in (27, 32): # Esc or Space
            self.return_to_menu()
            return True
        return False

    def return_to_menu(self, *args):
        if getattr(self, "returning", False):
            return
        self.returning = True
        
        print("[Credits] Ending credits and returning to menu...")
        Window.unbind(on_key_down=self._on_key_down)
        Window.unbind(mouse_pos=self._on_mouse_move)
        if hasattr(self, "hide_label_event") and self.hide_label_event:
            self.hide_label_event.cancel()
        Animation.stop_all(self.credits_label)
        
        if self.manager:
            game_screen = self.manager.get_screen("game_screen")
            # 🌟 สลับไปหน้า Main Menu ก่อน เพื่อให้พื้นหลังดำของ Credits หายไป
            self.manager.current = "main_menu"
            
            # เปิด Popup ชัยชนะทับบนหน้า Main Menu
            popup = GameOverPopup(win=True, game_screen=game_screen)
            popup.open()

    def on_leave(self):
        Window.unbind(on_key_down=self._on_key_down)
        Window.unbind(mouse_pos=self._on_mouse_move)
        if hasattr(self, "hide_label_event") and self.hide_label_event:
            self.hide_label_event.cancel()
        Animation.stop_all(self.credits_label)
