from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.app import App
from kivy.core.window import Window

class CreditsScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        
        # พื้นหลังสีดำ
        layout = FloatLayout()
        self.add_widget(layout)
        
        # ข้อความ Credits (ตัวอย่างเบื้องต้น)
        credits_text = (
            "[b][size=60]APOCALITE[/size][/b]\n\n\n"
            "[size=40]Produced by[/size]\n"
            "Your Team Name\n\n\n"
            "[size=40]Game Design[/size]\n"
            "Developer Name\n\n\n"
            "[size=40]Programming[/size]\n"
            "Developer Name\n\n\n"
            "[size=40]Assets[/size]\n"
            "Asset Credits\n\n\n"
            "[size=40]Special Thanks[/size]\n"
            "You for Playing!\n\n\n\n\n\n\n"
            "Thank you for reaching the end."
        )
        
        self.credits_label = Label(
            text=credits_text,
            markup=True,
            halign='center',
            valign='top',
            size_hint=(1, None),
            height=2000, # กำหนดความสูงเพื่อให้เลื่อนได้ยาวๆ
            pos_hint={'center_x': 0.5},
            y=-2000 # เริ่มต้นจากด้านล่างหน้าจอ
        )
        
        layout.add_widget(self.credits_label)
        
        # อนิเมชันเลื่อนขึ้น (เลื่อนเป็นเวลา 20 วินาที)
        # เลื่อนจาก y=-2000 ไปยัง y=Window.height (เพื่อให้พ้นขอบบน)
        duration = 20
        anim = Animation(y=Window.height, duration=duration)
        anim.bind(on_complete=self.return_to_menu)
        anim.start(self.credits_label)
        
        # รองรับการกดข้าม (Esc หรือ Space)
        Window.bind(on_key_down=self._on_key_down)

    def _on_key_down(self, _win, key, *args):
        if key in (27, 32): # Esc หรือ Space
            self.return_to_menu()
            return True
        return False

    def return_to_menu(self, *args):
        Window.unbind(on_key_down=self._on_key_down)
        # ล้างอนิเมชันถ้ามี
        Animation.stop_all(self.credits_label)
        App.get_running_app().root.current = "main_menu"

    def on_leave(self):
        Window.unbind(on_key_down=self._on_key_down)
        Animation.stop_all(self.credits_label)
