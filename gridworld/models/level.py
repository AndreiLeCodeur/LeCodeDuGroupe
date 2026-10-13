from gridworld.contracts import LevelState
from gridworld.models.tile import Tile

import json
import copy
from pathlib import Path

class LevelError(ValueError):
    """JSON loading error or violation of the map contract."""

class Level(): # ce qu'on a modifié
    """Terrain grid loaded from levels/n0.json."""
    # pour valider le structure des données de la maps et initialise la map à une grille de cases
    def __init__(self, data: dict) -> None:
        # constructeur de la classe level, on prend un dictionnaire data (issu du fichier JSON)en entrée pour
        #initialiser l'instance de l'objet mais on ne renvoie rien 
        
        try : # on essaie d'accéder aux clés du dico mais si il se passe une bêtise, on la fait rentrer dans le except
            self.id = data["id"] #id du niveau
            raw_tiles = data["grid"] #la map est une liste de lignes de texte : '#' = mur, '.' = sol
            self.height = len(raw_tiles) # hauteur de la map
            if self.height == 0 :
                raise LevelError ("La grille est vide")
            self.width = len(raw_tiles[0]) # largeur de la map
            exit_x, exit_y = data["exit"]["x"], data["exit"]["y"] #position de la sortie
            symbols = {"#": "wall", ".": "floor"} #traduction des caractères en types de case
            self._grid = [] # la grille entière que l'on cartographie avec tile
            for i in range (len(raw_tiles)) :
                if len(raw_tiles[i])!= self.width :
                    raise LevelError (f"La largeur de la {i}e ligne ne correspond pas ")

                tile_row = [] #on veut reconstruire la ligne sous forlme d'objets de tile
                for j in  range (len(raw_tiles[i])):
                    kind = "exit" if (j, i) == (exit_x, exit_y) else symbols.get(raw_tiles[i][j], raw_tiles[i][j])
                    try:
                        tile_row.append(Tile(kind))
                    except ValueError as error:
                        raise LevelError(f"Case invalide en ({j}, {i}) : {error}") from error
                self._grid.append(tile_row) #la ligne est totalement transformée en objets tile donc on peut l'ajouter à la grille principale

            start_x, start_y = data["start"]["x"], data["start"]["y"] #position de départ du joueur
            if not self.is_walkable(start_x, start_y):
                raise LevelError("La position de départ du joueur n'est pas sur une case libre")
            if not self.is_exit(exit_x, exit_y):
                raise LevelError("La sortie est en dehors de la grille")

            self._start_pos = (start_x, start_y)

        except (KeyError, TypeError) as error :
            raise LevelError (f"Erreur, structure JSON non valide où clé absente {error}") from error

    @classmethod
    def load(cls, path: str) -> "Level":
        try : 
            f = open (path, "r", encoding="utf-8")
            data = json.load(f)
            f.close()  # On ferme le fichier et on crée l'objet level avec les bonnes données
            level_obj = cls(data)
            return level_obj
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e: # Si le fichier n'existe pas ou si le JSON est mal formé
            raise LevelError(f"Impossible de lire le niveau {path} : {e}") from e

    def get_start(self) -> tuple[int, int]:
        # Donne les coordonnées de départ (trouvées avant)
        return self._start_pos

    def get_tile(self, x: int, y: int) -> Tile:
        # On vérifie si les coordonnées sont en dehors de la grille
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            raise IndexError(f"Coordonnées ({x}, {y}) hors de la grille.")
        tile = self._grid[y][x] # On récupère l'élément en (x,y)
        return tile
        
    def is_walkable(self, x: int, y: int) -> bool:
        # On vérifie d'abord si la case est dans la grille
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        
        # Si elle est dans la grille, on regarde si c'est pas un mur
        tile = self._grid[y][x]
        return tile.is_walkable()
    
    def is_exit(self, x: int, y: int) -> bool:
        # On vérifie d'abord si la case est dans la grille
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return False
        
        # Si elle est dans la grille, on demande à la case si c'est la sortie
        tile = self._grid[y][x]
        return tile.is_exit()

    def to_state(self) -> LevelState:
        # On reconstruit le tableau 2D de texte 'raw_tiles' 
        raw_tiles = []
        
        for i in range(len(self._grid)):
            ligne_texte = []
            for j in range(len(self._grid[i])):
                tile_objet = self._grid[i][j]
                type_texte = tile_objet.to_state()
                ligne_texte.append(type_texte)
            
            raw_tiles.append(ligne_texte)
        
        # On construit le dictionnaire de retour à la main
        res = {"id": self.id,"width": self.width, "height": self.height,"tiles": raw_tiles}
        
        return res
      