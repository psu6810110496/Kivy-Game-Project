# Apocalite - Kivy Game Project

A fast-paced, action-packed 2D survival game built with **Kivy** framework. Battle waves of enemies, defeat bosses, level up, and unlock powerful skills to survive as long as possible.

## Features

### Core Gameplay
- **Wave-based enemy spawning**: Face increasingly difficult waves of enemies
- **Character selection**: Choose from multiple playable characters (Lostman, Monkey, PTae, Ranger)
- **Dynamic skill system**: Earn skill upgrades on level-up with randomized skill selection
- **Boss battles**: Regular bosses appear every 5 waves (5, 15, 25...), and epic big bosses every 10 waves (10, 20, 30...)
- **Smooth camera system**: Camera follows the player with damping for cinematic feel

### Enemy Types
- **Normal**: Balanced melee enemies
- **Stalker**: Fast but fragile enemies
- **Ranger**: Ranged attackers that keep distance
- **Boss**: Stronger single target (appears on waves 5, 15, 25...)
- **Big Boss**: Epic boss with special attacks:
  - **Ground Slam**: Radial damage attack with warning indicator
  - **Swipe**: Fast forward slash towards player
  - **Missile Barrage**: Slow heavy projectiles (appears on waves 10, 20, 30...)

### UI & Polish
- **HUD Display**: Real-time HP bar, level display, wave counter, EXP bar
- **Skill slots**: 3 large skill display buttons (bottom-left corner)
- **Game Over screen**: Stylized overlay with "TRY AGAIN" and "BACK TO MENU" options
- **Pause menu**: Full-screen pause overlay with navigation support
- **Screen transitions**: Smooth fade transitions between screens
- **Gamepad support**: Full controller support with D-Pad, analog stick, and button navigation

### Visual Effects
- **Slam damage indicator**: Yellow warning circle → Red impact circle on big boss slam
- **Particle effects**: Slash effects, projectile animations
- **Color feedback**: Enemy knockback, damage indication via color changes
- **Sprite animations**: Walking, idle, attacking animations for all characters

## Installation

### Requirements
- Python 3.7+
- Kivy 2.0+
- Pillow (optional, for sprite sheet extraction)

### Setup

```bash
# Clone the repository
git clone https://github.com/psu6810110496/Kivy-Game-Project.git
cd Kivy-Game-Project

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

## Project Structure

```
Kivy-Game-Project/
├── main.py                 # Application entry point
├── game/
│   ├── engine.py          # Main game loop and screen manager
│   ├── player.py          # Player character definition
│   ├── player_widget.py   # Player rendering and animation
│   ├── enemy_widget.py    # Enemy rendering and AI
│   ├── projectile_widget.py # Bullet and projectile system
│   ├── skills.py          # Skill system and mechanics
│   └── __init__.py
├── ui/
│   ├── main_menu.py       # Main menu screen
│   ├── char_select.py     # Character selection screen
│   ├── game_over.py       # Game over overlay popup
│   ├── pause.py           # Pause menu popup
│   ├── level_up.py        # Level up selection screen
│   ├── hud.py             # In-game HUD display
│   └── __init__.py
├── assets/                # Game assets
│   ├── enemy/             # Enemy sprites
│   ├── effect/            # Visual effects
│   ├── maps/              # Game map backgrounds
│   ├── Lostman/           # Lostman character sprites
│   ├── Monkey/            # Monkey character sprites
│   ├── PTae/              # PTae character sprites
│   └── Ranger/            # Ranger character sprites
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## How to Play

1. **Start Game**: Select a character from the character selection screen
2. **Survive Waves**: Battle through increasingly difficult enemy waves
3. **Level Up**: Defeat enemies to gain EXP and level up
4. **Choose Skills**: When leveling up, select from 3 random skill upgrades
5. **Defeat Bosses**: 
   - Regular bosses on waves ending in 5
   - Big bosses with special attacks on waves ending in 0
6. **Game Over**: When HP reaches 0, choose to try again or return to menu

### Controls

#### Keyboard
- **WASD / Arrow Keys**: Move
- **Mouse**: Aim attacks
- **Left Click**: Attack
- **Space**: Dash
- **P / ESC**: Pause
- **F11**: Toggle fullscreen

#### Gamepad
- **D-Pad / Left Analog**: Move
- **Right Analog**: Aim
- **A Button**: Attack
- **X Button**: Dash
- **B Button**: Pause
- **Menu Navigation**: D-Pad Up/Down

## Game Mechanics

### Wave System
- Waves increase enemy count: `5 + wave * 2` enemies per wave
- Bosses spawn on specific wave intervals
- Player has 1 second delay before Game Over screen appears on death

### Combat
- Enemies take knockback on hit
- Player has invincibility frames after taking damage
- Different enemy types have unique behavior patterns

### Leveling
- Gain 10 EXP per enemy defeated
- 100 EXP = 1 level up
- Level up triggers skill selection popup

### Boss Attacks (Big Boss)
- **Slam** (every 4-6s): 250px radius, deals 60 damage, shows warning then impact circles
- **Swipe** (every 3-5s): Fast projectile at 700 speed, deals 48 damage
- **Missile** (every 4-6s): Slow projectile at 300 speed, deals 32 damage

## Future Enhancements

- [ ] Sound effects and background music
- [ ] Additional skill types and combinations
- [ ] Leaderboard/high score system
- [ ] Mobile touch controls
- [ ] Difficulty settings
- [ ] Additional character types
- [ ] Boss variations and unique mechanics

## Credits

- **Framework**: Kivy 2.0+
- **Development**: Game Development Team

## License

This project is open source and available under the MIT License.