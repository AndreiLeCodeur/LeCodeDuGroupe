from gridworld.contracts import LevelState
from gridworld.models.tile import Tile

import json
import copy
from pathlib import Path

class LevelError(ValueError):
    """JSON loading error or violation of the map contract."""
    pass

class Level: # ce qu'on a modifié
    """Terrain grid loaded from levels/n0.json."""
    # pour valider le structure des données de la maps et initialise la map à une grille de cases
    def __init__(self, data: dict) -> None:
        # constructeur de la classe level, on prend un dictionnaire data (issu du fichier JSON)en entrée pour
        #initialiser l'instance de l'objet mais on ne renvoie rien 
        
        try : # on essaie d'accéder aux clés du dico mais si il se passe une bêtise, on la fait rentrer dans le except
            self.id = data["id"] #id du niveau 
            raw_tiles = data["grid"] # la grille est une liste de chaînes de caractères
            
            self.height = len(raw_tiles) # hauteur de la map
            if self.height == 0:
                raise LevelError("La grille est vide")
            self.width = len(raw_tiles[0]) # largeur de la map
            
            self._grid  = [] # la grille entière que l'on cartographie avec tile
            
            for i in range (len(raw_tiles)) :
                if len(raw_tiles[i]) != self.width :
                    raise LevelError (f"La largeur de la {i}e ligne ne correspond pas ")
                
                tile_row = [] #on veut reconstruire la ligne sous forme d'objets de tile
                for j in range (len(raw_tiles[i])):
                    kind = raw_tiles[i][j]
                    try:
                        tile_row.append(Tile(kind))
                    except ValueError as error:
                        raise LevelError(f"Case invalide en ({j}, {i}) : {error}") from error
                self._grid.append(tile_row) #la ligne est totalement transformée en objets tile donc on peut l'ajouter à la grille principale

            # Gestion de la position de départ du joueur
            start_data = data.get("start")
            if not start_data or "x" not in start_data or "y" not in start_data:
                raise LevelError("La position de départ du joueur n'a pas été déterminée")
            self.start_pos = (start_data["x"], start_data["y"])  # Sans underscore
            self._start_pos = self.start_pos  

            # Gestion optionnelle de la sortie (exit)
            exit_data = data.get("exit")
            if exit_data and "x" in exit_data and "y" in exit_data:
                self.exit_pos = (exit_data["x"], exit_data["y"])
            else:
                self.exit_pos = None

        except (KeyError, TypeError) as error : 
            raise LevelError (f"Erreur, structure JSON non valide ou clé absente {error}") from error

    @classmethod
    def load(cls, path: str) -> "Level":
        try : 
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            level_obj = cls(data)
            return level_obj
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e: # Si le fichier n'existe pas ou si le JSON est mal formé
            raise LevelError(f"Impossible de charger le fichier depuis {path}: {e}") from e

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
            ligne_texte = ""
            for j in range(len(self._grid[i])):
                tile_objet = self._grid[i][j]
                type_texte = tile_objet.to_state()
                ligne_texte += type_texte
            
            raw_tiles.append(ligne_texte)
        
        # On construit le dictionnaire de retour à la main
        res = {"id": self.id, "grid": raw_tiles, "start": {"x": self.start_pos[0], "y": self.start_pos[1]}}
        if self.exit_pos:
            res["exit"] = {"x": self.exit_pos[0], "y": self.exit_pos[1]}
        
        return res