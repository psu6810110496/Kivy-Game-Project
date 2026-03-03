from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.app import App

class GameOverPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = ""
        self.separator_height = 0
        self.size_hint = (0.5, 0.4)
        self.auto_dismiss = False
        self.background_color = (0, 0, 0, 0.9)

        # เก็บปุ่มสำหรับรองรับจอย (ถึงแม้จะมีปุ่มเดียว)
        self.menu_btn = None
        self.bind(on_open=self._setup_joy, on_dismiss=self._remove_joy)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # ข้อความแจ้งเตือน
        die_label = Label(
            text="YOU DIED",
            font_size=50,
            color=(1, 0, 0, 1), # สีแดง
            bold=True
        )
        
        # ปุ่มกลับหน้าเมนู
        menu_btn = Button(
            text="BACK TO MENU",
            size_hint_y=None,
            height=60,
            background_color=(0.2, 0.2, 0.2, 1)
        )
        menu_btn.bind(on_press=self.return_to_menu)
        self.menu_btn = menu_btn

        layout.add_widget(die_label)
        layout.add_widget(menu_btn)
        self.content = layout

    def return_to_menu(self, instance):
        self.dismiss()
        # เปลี่ยนหน้าไปที่ main_menu
        App.get_running_app().root.current = "main_menu"

    # ================================
    # --- รองรับจอยตอน Game Over ---
    # ================================
    def _setup_joy(self, *args):
        Window.bind(on_joy_button_down=self._on_joy_button_down)

    def _remove_joy(self, *args):
        Window.unbind(on_joy_button_down=self._on_joy_button_down)

    def _on_joy_button_down(self, window, stickid, buttonid):
        # ปุ่ม A (0) = กลับไป Main Menu
        if buttonid == 0 and self.menu_btn:
            self.menu_btn.dispatch("on_press")