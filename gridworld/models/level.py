from gridworld.contracts import LevelState
from gridworld.models.tile import Tile

import json


class LevelError(ValueError):
    """JSON loading error or violation of the map contract."""
    pass


# traduction des caractères du JSON en types de case
SYMBOLS = {"#": "wall", ".": "floor", "E": "exit"}


class Level:
    """Terrain grid loaded from levels/n0.json."""

    # pour valider la structure des données de la map et initialiser la map en une grille de cases
    def __init__(self, data: dict) -> None:
        try:  # si une clé manque ou si un type est faux, on le transforme en LevelError
            self.id = data["id"]  # id du niveau
            raw_tiles = data["grid"]  # liste de lignes de texte : '#' = mur, '.' = sol, 'E' = sortie
            if not isinstance(raw_tiles, list) or len(raw_tiles) == 0:
                raise LevelError("La grille est vide ou n'est pas une liste")
            self.height = len(raw_tiles)  # hauteur de la map
            self.width = len(raw_tiles[0])  # largeur de la map
            if self.width == 0:
                raise LevelError("La première ligne de la grille est vide")

            self._grid: list[list[Tile]] = []  # la grille entière sous forme d'objets Tile
            for y, row in enumerate(raw_tiles):
                if not isinstance(row, str) or len(row) != self.width:
                    raise LevelError(f"La ligne {y} n'a pas la largeur attendue ({self.width})")
                tile_row = []
                for x, symbol in enumerate(row):
                    if symbol not in SYMBOLS:
                        raise LevelError(f"Case invalide en ({x}, {y}) : {symbol!r}")
                    tile_row.append(Tile(SYMBOLS[symbol]))
                self._grid.append(tile_row)

            start_x, start_y = data["start"]["x"], data["start"]["y"]  # position de départ du joueur
            exit_x, exit_y = data["exit"]["x"], data["exit"]["y"]  # position de la sortie
        except (KeyError, TypeError) as error:
            raise LevelError(f"Structure JSON non valide ou clé absente : {error}") from error

        for name, value in (("start.x", start_x), ("start.y", start_y), ("exit.x", exit_x), ("exit.y", exit_y)):
            if isinstance(value, bool) or not isinstance(value, int):
                raise LevelError(f"{name} doit être un entier")

        # la sortie doit être dans la grille et pas sur un mur ; on y place une case "exit"
        if not self._in_bounds(exit_x, exit_y):
            raise LevelError("La sortie est en dehors de la grille")
        if not self._grid[exit_y][exit_x].is_walkable():
            raise LevelError("La sortie est sur un mur")
        self._grid[exit_y][exit_x] = Tile("exit")

        if not self.is_walkable(start_x, start_y):
            raise LevelError("La position de départ du joueur n'est pas sur une case libre")

        self.start_pos = (start_x, start_y)
        self.exit_pos = (exit_x, exit_y)

    @classmethod
    def load(cls, path: str) -> "Level":
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
            # fichier absent, illisible ou JSON mal formé
            raise LevelError(f"Impossible de lire le niveau {path} : {e}") from e
        return cls(data)

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_start(self) -> tuple[int, int]:
        return self.start_pos

    def get_tile(self, x: int, y: int) -> Tile:
        if not self._in_bounds(x, y):
            raise IndexError(f"Coordonnées ({x}, {y}) hors de la grille.")
        return self._grid[y][x]

    def is_walkable(self, x: int, y: int) -> bool:
        # hors de la grille -> False, sinon on demande à la case
        return self._in_bounds(x, y) and self._grid[y][x].is_walkable()

    def is_exit(self, x: int, y: int) -> bool:
        return self._in_bounds(x, y) and self._grid[y][x].is_exit()

    def to_state(self) -> LevelState:
        # nouvel état indépendant, au format LevelState (voir contracts.py et initial_state.json)
        return {
            "id": self.id,
            "width": self.width,
            "height": self.height,
            "tiles": [[tile.to_state() for tile in row] for row in self._grid],
        }
