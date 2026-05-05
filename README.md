# Pokemon App

Desktop application built with Python and Tkinter to explore Pokemon data from the PokeAPI in a visual and interactive way.

## What it does

- Search Pokemon by name
- Browse Pokemon by type
- View official artwork and available sprites
- Check base stats, abilities, moves, and evolution chain
- Save favorite Pokemon locally in a JSON file
- Play a small guessing mini-game with clues

## Tech stack

- Python 3
- Tkinter
- Requests
- PokeAPI

## Project structure

The main application lives in the `Pokemon_app/` folder:

```text
Pokemon_app/
  pokemon_app.py
  README.md
  .gitignore
```

Main entry point:

```text
Pokemon_app/pokemon_app.py
```

## Installation

```powershell
git clone https://github.com/DaniSanchezDevx/Pokemon_app.py.git
cd Pokemon_app.py\Pokemon_app
pip install requests
```

## Run the app

```powershell
python pokemon_app.py
```

## Main features

### Search by name
Search any Pokemon and display its main information, including types, height, weight, stats, abilities, sprites, and moves.

### Search by type
Browse all Pokemon that belong to a selected type and open any result directly from the list.

### Favorites
Store favorite Pokemon locally in `pokemon_favoritos.json` so they remain available between sessions.

### Evolution chain
Display each evolution stage together with the method or condition required for the evolution.

### Guessing game
Start a mini-game that picks a random Pokemon from the first 151 and gives clues so the player can guess it in a limited number of attempts.

## Data source

This project uses the public PokeAPI:

https://pokeapi.co/

## Notes

- Internet connection is required to fetch Pokemon data and images.
- Favorites are stored locally on the machine where the app is executed.
