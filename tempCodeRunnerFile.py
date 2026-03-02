    def build(self):
        self.current_player = None 
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(CharacterSelectScreen(name='char_select_screen'))
        sm.add_widget(GameScreen(name='game_screen'))
        return sm

if __name__ == '__main__':
    VampireApp().run()