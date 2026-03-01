from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock

# Key mapping helper
from kivy.core.window import Keyboard

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
# 2. Player Sprite Widget
# ==========================================
class PlayerWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0, 0.5, 1, 1)  # Blue Hero
            self.rect = Rectangle(pos=(640, 360), size=(50, 50))

    def update_pos(self, new_pos):
        self.rect.pos = new_pos


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
            "Survivor": PlayerStats("The Survivor", 100, 5, 10),
            "Scavenger": PlayerStats("The Scavenger", 70, 10, 5),
            "Veteran": PlayerStats("The Veteran", 200, 2, 15),
        }
        self.setup_ui()

    def setup_ui(self):
        layout = BoxLayout(orientation="vertical", padding=40, spacing=20)
        layout.add_widget(
            Label(text="SELECT YOUR HERO", font_size=36, size_hint=(1, 0.2))
        )
        char_layout = BoxLayout(
            orientation="horizontal", spacing=20, size_hint=(1, 0.8)
        )
        for name, stats in self.char_data.items():
            btn = Button(
                text=f"{stats.name}\nHP: {stats.hp}\nSpeed: {stats.speed}",
                halign="center",
            )
            btn.bind(on_press=lambda instance, s=stats: self.select_hero(s))
            char_layout.add_widget(btn)
        layout.add_widget(char_layout)
        self.add_widget(layout)

    def select_hero(self, stats_obj):
        App.get_running_app().current_player = stats_obj
        self.manager.current = "game_screen"


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keys_pressed = set()
        self.player_pos = [640, 360]

        # Bind Keyboard
        Window.bind(on_key_down=self._on_keydown)
        Window.bind(on_key_up=self._on_keyup)

        self.main_layout = FloatLayout()

        # HUD
        hud = BoxLayout(orientation="vertical", size_hint=(1, 1))
        top_bar = BoxLayout(size_hint=(1, 0.1), padding=10)
        self.lbl_level = Label(text="LV: 1", size_hint=(0.2, 1))
        self.exp_bar = ProgressBar(max=100, value=0)
        top_bar.add_widget(self.lbl_level)
        top_bar.add_widget(self.exp_bar)

        hud.add_widget(top_bar)
        hud.add_widget(Widget())

        btn_test = Button(
            text="[TEST] Add EXP",
            size_hint=(None, None),
            size=(150, 50),
            pos_hint={"right": 1, "bottom": 0},
        )
        btn_test.bind(on_press=self.gain_exp)

        self.main_layout.add_widget(hud)
        self.main_layout.add_widget(btn_test)

        self.player_widget = PlayerWidget()
        self.main_layout.add_widget(self.player_widget)

        self.add_widget(self.main_layout)

    def on_enter(self):
        self.player_stats = App.get_running_app().current_player
        self.update_ui()
        Clock.schedule_interval(self.update, 1.0 / 60.0)

    def on_leave(self):
        Clock.unschedule(self.update)

    def _on_keydown(self, window, key, scancode, codepoint, modifiers):
        # Using the key code (int) is more reliable than codepoints
        self.keys_pressed.add(key)

    def _on_keyup(self, window, key, scancode):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

    def update(self, dt):
        step = self.player_stats.speed

        # Check against Kivy's key codes (ASCII values)
        # 'w'=119, 's'=115, 'a'=97, 'd'=100
        if 119 in self.keys_pressed:
            self.player_pos[1] += step
        if 115 in self.keys_pressed:
            self.player_pos[1] -= step
        if 97 in self.keys_pressed:
            self.player_pos[0] -= step
        if 100 in self.keys_pressed:
            self.player_pos[0] += step

        # Screen Clamping
        self.player_pos[0] = max(0, min(self.player_pos[0], Window.width - 50))
        self.player_pos[1] = max(0, min(self.player_pos[1], Window.height - 50))

        self.player_widget.update_pos(self.player_pos)

    def update_ui(self):
        self.lbl_level.text = f"LV: {self.player_stats.level}"
        self.exp_bar.value = self.player_stats.exp

    def gain_exp(self, instance):
        self.player_stats.exp += 35
        if self.player_stats.exp >= 100:
            self.player_stats.level += 1
            self.player_stats.exp = 0
            self.manager.current = "level_up_screen"
        self.update_ui()


class LevelUpScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=30, spacing=20)
        layout.add_widget(Label(text="LEVEL UP!", font_size=40, size_hint=(1, 0.2)))

        self.cards_layout = GridLayout(cols=3, spacing=20, size_hint=(1, 0.6))
        upgrades = ["+ Damage", "+ Max HP", "+ Speed"]
        for upg in upgrades:
            btn = Button(text=upg)
            btn.bind(on_press=self.apply_upgrade)
            self.cards_layout.add_widget(btn)

        layout.add_widget(self.cards_layout)
        self.add_widget(layout)

    def apply_upgrade(self, instance):
        player = App.get_running_app().current_player
        if "+ Damage" in instance.text:
            player.damage += 5
        elif "+ Max HP" in instance.text:
            player.hp += 20
        elif "+ Speed" in instance.text:
            player.speed += 2
        self.manager.current = "game_screen"


# ==========================================
# 4. Application Controller
# ==========================================
class VampireApp(App):
    def build(self):
        self.current_player = None
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name="main_menu"))
        sm.add_widget(CharacterSelectScreen(name="char_select_screen"))
        sm.add_widget(GameScreen(name="game_screen"))
        sm.add_widget(LevelUpScreen(name="level_up_screen"))
        return sm


if __name__ == "__main__":
    VampireApp().run()
