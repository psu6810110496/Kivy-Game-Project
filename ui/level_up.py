from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import Clock
import kivy.app


# ==========================================
# --- คลาส Level Up Popup ---
# ==========================================
class LevelUpPopup(Popup):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        self.title = "LEVEL UP! Choose your Upgrade:"
        self.title_font_size = 22

        self.background = ""
        self.background_color = (0.05, 0.08, 0.1, 0.95)
        self.separator_color = (0.3, 0.5, 0.6, 1)  

        self.size_hint = (0.6, 0.5)
        self.auto_dismiss = False

        # --- [ระบบ Joy Navigation] ---
        self.selectable_buttons = []
        self.selected_index = 0
        self.joy_cooldown = False
        self.bind(on_open=self.setup_joy, on_dismiss=self.remove_joy)
        # ---------------------------

        layout = BoxLayout(orientation="vertical", padding=20, spacing=20)
        cards_layout = GridLayout(cols=3, spacing=15)

        upgrades = ["+ Damage", "+ Max HP", "+ Speed"]

        for upg in upgrades:
            btn = Button(
                text=upg,
                font_size=20,
                bold=True,
                background_normal="",
                background_color=(0.1, 0.15, 0.2, 0.9),
                color=(0.8, 0.9, 1, 1),
            )
            btn.bind(on_press=self.apply_upgrade)
            cards_layout.add_widget(btn)
            self.selectable_buttons.append(btn) # เก็บปุ่มลง List

        layout.add_widget(cards_layout)
        self.content = layout

    # --- [ระบบ Joy ของ Level Up] ---
    def setup_joy(self, *args):
        Window.bind(on_joy_axis=self._on_joy_axis, on_joy_hat=self._on_joy_hat, on_joy_button_down=self._on_joy_button_down)
        self.selected_index = 0
        self.update_highlight()

    def remove_joy(self, *args):
        Window.unbind(on_joy_axis=self._on_joy_axis, on_joy_hat=self._on_joy_hat, on_joy_button_down=self._on_joy_button_down)

    def update_highlight(self):
        for i, btn in enumerate(self.selectable_buttons):
            if i == self.selected_index:
                btn.background_color = (0.3, 0.5, 0.7, 1) # ไฮไลท์สีฟ้าสว่าง
            else:
                btn.background_color = (0.1, 0.15, 0.2, 0.9) # สีมืดปกติ

    def _reset_cooldown(self, dt):
        self.joy_cooldown = False

    def navigate(self, direction):
        if self.joy_cooldown: return
        self.joy_cooldown = True
        Clock.schedule_once(self._reset_cooldown, 0.2)
        if direction == "next":
            self.selected_index = (self.selected_index + 1) % len(self.selectable_buttons)
        elif direction == "prev":
            self.selected_index = (self.selected_index - 1) % len(self.selectable_buttons)
        self.update_highlight()

    def _on_joy_axis(self, window, stickid, axisid, value):
        normalized = value / 32767.0
        if abs(normalized) > 0.5:
            if axisid == 0 or axisid == 1: # รองรับทั้งซ้าย-ขวา และ บน-ล่าง
                self.navigate("next" if normalized > 0 else "prev")

    def _on_joy_hat(self, window, stickid, hatid, value):
        x, y = value
        if x == 1 or y == -1: self.navigate("next")
        elif x == -1 or y == 1: self.navigate("prev")

    def _on_joy_button_down(self, window, stickid, buttonid):
        if buttonid == 0: # ปุ่ม A
            self.selectable_buttons[self.selected_index].dispatch('on_press')
    # --------------------------------

    def apply_upgrade(self, instance):
        player = kivy.app.App.get_running_app().current_player
        if player:
            if "+ Damage" in instance.text:
                player.damage += 5
            elif "+ Max HP" in instance.text:
                player.hp += 20
            elif "+ Speed" in instance.text:
                player.speed += 2

        self.game_screen.resume_game()
        self.dismiss()


