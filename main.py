from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color, PushMatrix, PopMatrix, Translate
from kivy.clock import Clock

Window.size = (1280, 720)


# ==========================================
# 1. Data Model
# ==========================================
class PlayerStats:
    def __init__(self, name, hp, speed, damage):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.damage = damage
        self.level = 1
        self.exp = 0


# ==========================================
# 2. Widgets & Popups
# ==========================================
class PlayerWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0, 0.5, 1, 1)
            self.rect = Rectangle(pos=(2500, 2500), size=(50, 50))

    def update_pos(self, new_pos):
        self.rect.pos = new_pos


class LevelUpPopup(Popup):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        self.title = "LEVEL UP!"
        self.size_hint = (0.5, 0.4)
        self.auto_dismiss = False

        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        layout.add_widget(Label(text="Choose an Upgrade", font_size=20))

        btns = GridLayout(cols=3, spacing=10)
        upgrades = ["+ Damage", "+ Max HP", "+ Speed"]
        for upg in upgrades:
            btn = Button(text=upg)
            btn.bind(on_press=self.apply_upgrade)
            btns.add_widget(btn)

        layout.add_widget(btns)
        self.content = layout

    def apply_upgrade(self, instance):
        player = App.get_running_app().current_player
        if "+ Damage" in instance.text:
            player.damage += 5
        elif "+ Max HP" in instance.text:
            player.hp += 20
        elif "+ Speed" in instance.text:
            player.speed += 2

        self.game_screen.resume_game()
        self.dismiss()


# --- เพิ่ม Pause Popup ---
class PausePopup(Popup):
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        self.title = "GAME PAUSED"
        self.size_hint = (0.4, 0.4)
        self.auto_dismiss = False

        layout = BoxLayout(orientation="vertical", padding=20, spacing=15)

        btn_resume = Button(text="RESUME", size_hint=(1, 0.5))
        btn_menu = Button(text="RETURN TO MENU", size_hint=(1, 0.5))

        btn_resume.bind(on_press=self.resume)
        btn_menu.bind(on_press=self.go_to_menu)

        layout.add_widget(btn_resume)
        layout.add_widget(btn_menu)
        self.content = layout

    def resume(self, instance):
        self.game_screen.resume_game()
        self.dismiss()

    def go_to_menu(self, instance):
        self.dismiss()
        self.game_screen.manager.current = "main_menu"


# ==========================================
# 3. UI Screens
# ==========================================
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main_layout = FloatLayout()
        menu_group = BoxLayout(
            orientation="vertical",
            spacing=45,
            size_hint=(None, None),
            size=(800, 600),
            pos_hint={"x": 0.1, "top": 0.9},
        )

        title_label = Label(
            text="VAMPIRE SURVIVORS",
            font_size=70,
            bold=True,
            halign="left",
            valign="middle",
            size_hint=(1, None),
            height=150,
        )
        title_label.bind(size=title_label.setter("text_size"))

        btn_start = Button(
            text="START SURVIVING",
            font_size=26,
            size_hint=(0.4, None),
            height=80,
            pos_hint={"center_x": 0.33},
        )
        btn_quit = Button(
            text="QUIT GAME",
            font_size=26,
            size_hint=(0.4, None),
            height=80,
            pos_hint={"center_x": 0.33},
        )

        btn_start.bind(on_press=lambda x: self.change_screen("char_select_screen"))
        btn_quit.bind(on_press=lambda x: App.get_running_app().stop())

        menu_group.add_widget(title_label)
        menu_group.add_widget(btn_start)
        menu_group.add_widget(btn_quit)
        main_layout.add_widget(menu_group)
        self.add_widget(main_layout)

    def change_screen(self, screen_name):
        self.manager.current = screen_name


class CharacterSelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.char_data = {
            "Survivor": PlayerStats("Survivor", 100, 5, 10),
            "Scavenger": PlayerStats("Scavenger", 70, 10, 5),
            "Veteran": PlayerStats("Veteran", 200, 2, 15),
        }
        layout = BoxLayout(orientation="vertical", padding=50, spacing=20)
        layout.add_widget(Label(text="SELECT YOUR CHARACTER", font_size=30))

        chars = BoxLayout(spacing=20)
        for name, stats in self.char_data.items():
            btn = Button(text=f"{name}\nHP: {stats.hp}\nSPD: {stats.speed}")
            btn.bind(on_press=lambda inst, s=stats: self.select_char(s))
            chars.add_widget(btn)

        layout.add_widget(chars)
        self.add_widget(layout)

    def select_char(self, stats):
        App.get_running_app().current_player = stats
        self.manager.current = "game_screen"


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keys_pressed = set()
        self.player_pos = [2500, 2500]
        self.player_stats = None
        self.is_paused = False

        Window.bind(on_key_down=self._on_keydown)
        Window.bind(on_key_up=self._on_keyup)

        self.root_layout = FloatLayout()

        # World & Camera
        self.world_layout = FloatLayout(size_hint=(None, None), size=(5000, 5000))
        with self.world_layout.canvas.before:
            PushMatrix()
            self.camera = Translate(0, 0)
            Color(0.2, 0.2, 0.2, 1)
            for i in range(0, 5001, 100):
                Rectangle(pos=(0, i), size=(5000, 1))
                Rectangle(pos=(i, 0), size=(1, 5000))
        with self.world_layout.canvas.after:
            PopMatrix()

        self.player_widget = PlayerWidget()
        self.world_layout.add_widget(self.player_widget)
        self.root_layout.add_widget(self.world_layout)

        # --- HUD ---
        self.hud = FloatLayout(size_hint=(1, 1))

        # XP Bar & Level
        top_ui = BoxLayout(
            size_hint=(0.8, 0.05), pos_hint={"center_x": 0.5, "top": 0.98}, spacing=10
        )
        self.lbl_level = Label(text="LV: 1", size_hint=(0.1, 1), bold=True)
        self.exp_bar = ProgressBar(max=100, value=0)
        top_ui.add_widget(self.lbl_level)
        top_ui.add_widget(self.exp_bar)
        self.hud.add_widget(top_ui)

        # Pause Button (บนขวา)
        btn_pause = Button(
            text="||",
            size_hint=(None, None),
            size=(50, 50),
            pos_hint={"right": 0.98, "top": 0.98},
        )
        btn_pause.bind(on_press=self.pause_game)
        self.hud.add_widget(btn_pause)

        # Test EXP Button (ล่างขวา)
        btn_test = Button(
            text="+EXP",
            size_hint=(None, None),
            size=(80, 40),
            pos_hint={"right": 0.98, "y": 0.02},
        )
        btn_test.bind(on_press=self.gain_exp)
        self.hud.add_widget(btn_test)

        self.root_layout.add_widget(self.hud)
        self.add_widget(self.root_layout)

    def on_enter(self):
        self.player_stats = App.get_running_app().current_player
        if self.player_stats:
            self.update_ui()
            Clock.schedule_interval(self.update_frame, 1.0 / 60.0)

    def on_leave(self):
        Clock.unschedule(self.update_frame)
        self.is_paused = False
        self.player_pos = [2500, 2500]  # รีเซ็ตตำแหน่งถ้าออกไปหน้าเมนู

    def update_ui(self):
        if self.player_stats:
            self.lbl_level.text = f"LV: {self.player_stats.level}"
            self.exp_bar.value = self.player_stats.exp

    def pause_game(self, instance):
        self.is_paused = True
        PausePopup(game_screen=self).open()

    def resume_game(self):
        self.is_paused = False
        self.keys_pressed.clear()

    def update_frame(self, dt):
        if not self.player_stats or self.is_paused:
            return

        step = self.player_stats.speed
        if "w" in self.keys_pressed:
            self.player_pos[1] += step
        if "s" in self.keys_pressed:
            self.player_pos[1] -= step
        if "a" in self.keys_pressed:
            self.player_pos[0] -= step
        if "d" in self.keys_pressed:
            self.player_pos[0] += step

        self.player_widget.update_pos(self.player_pos)
        self.camera.x = (Window.width / 2) - self.player_pos[0] - 25
        self.camera.y = (Window.height / 2) - self.player_pos[1] - 25

    def gain_exp(self, instance):
        if self.player_stats:
            self.player_stats.exp += 35
            if self.player_stats.exp >= 100:
                self.player_stats.level += 1
                self.player_stats.exp -= 100
                self.is_paused = True
                LevelUpPopup(game_screen=self).open()
            self.update_ui()

    def _on_keydown(self, window, key, scancode, codepoint, modifiers):
        if codepoint:
            self.keys_pressed.add(codepoint.lower())
        # กด ESC เพื่อ Pause ได้ด้วย
        if key == 27:
            self.pause_game(None)
            return True  # ป้องกันการปิด App บน Android

    def _on_keyup(self, window, key, scancode):
        try:
            key_char = chr(key).lower()
            if key_char in self.keys_pressed:
                self.keys_pressed.remove(key_char)
        except:
            pass


class VampireApp(App):
    def build(self):
        self.current_player = None
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name="main_menu"))
        sm.add_widget(CharacterSelectScreen(name="char_select_screen"))
        sm.add_widget(GameScreen(name="game_screen"))
        return sm


if __name__ == "__main__":
    VampireApp().run()
