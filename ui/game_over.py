from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.app import App

class GameOverPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = ""
        self.separator_height = 0
        self.size_hint = (0.5, 0.4)
        self.auto_dismiss = False
        self.background_color = (0, 0, 0, 0.9)

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

        layout.add_widget(die_label)
        layout.add_widget(menu_btn)
        self.content = layout

    def return_to_menu(self, instance):
        self.dismiss()
        # เปลี่ยนหน้าไปที่ main_menu
        App.get_running_app().root.current = "main_menu"