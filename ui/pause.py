from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import kivy.app

class PausePopup(Popup):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        self.title = "GAME PAUSED"
        self.size_hint = (0.4, 0.4)
        self.auto_dismiss = False
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        btn_resume = Button(text="RESUME", size_hint=(1, 0.5))
        btn_menu = Button(text="RETURN TO MENU", size_hint=(1, 0.5))
        
        btn_resume.bind(on_press=lambda x: self.resume())
        btn_menu.bind(on_press=lambda x: self.go_to_menu())
        
        layout.add_widget(btn_resume)
        layout.add_widget(btn_menu)
        self.content = layout

    def resume(self):
        # เรียกฟังก์ชัน resume ใน game_screen
        self.game_screen.resume_game()
        self.dismiss()

    def go_to_menu(self):
        # ปิด Popup และเปลี่ยน Screen
        self.dismiss()
        self.game_screen.manager.current = 'main_menu'