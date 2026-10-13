from gridworld.contracts import LevelState
from gridworld.models.tile import Tile

import json
import copy
frome pathlib import Path

class LevelError(ValueError):
    """JSON loading error or violation of the map contract."""

class Level: # ce qu'on a modifié
    """Terrain grid loaded from levels/n0.json."""
    # pour valider le structure des données de la maps et initialise la map à une grille de cases
    def __init__(self, data: dict) -> None:
        # constructeur de la classe level, on prend un dictionnaire data (issu du fichier JSON)en entrée pour
        #initialiser l'instance de l'objet mais on ne renvoie rien 
        
        try : # on essaie d'accéder aux clés du dico mais si il se passe une bêtise, on la fait rentrer dans le except
            lvl_data = data ["level"] #on extrait le sous-dico sous clé "level" pour ne pas tjrs le réecrire
            self.id = lvl_data["id"] #id du niveau 
            self.width = lvl_data["width"] # largeur de la map
            self.height = lvl_data["height"] # hauteur de la map
            raw_tiles = level_data["tiles"] #la map est en réalité une  grosse grille que l'on peut écrire sous forme de tableau 2D
            self.total_grid:  = [] # la grille entière que l'on cartographie avec tile
            if len(raw_tiles)!= self.height :
                raise LevelError ("La hauteur de la grille n'est pas la bonne" )
            for i in range (len(raw_tiles)) :
                if len(raw_tiles[i])!= self.width :
                    raise LevelError (f"La largeur de la {i}e ligne ne correspond pas ")
                
                tile_row = [] #on veut reconstruire la ligne sous forlme d'objets de tile
                for j in  range (len(raw_tiles[i])):
                    kind = raw_tiles[i][j]
                    try:
                        tile_row.append(Tile(kind))
                    except ValueError as error:
                        raise LevelError(f"Case invalide en ({j}, {i}) : {error}") from error
                self.total_grid.append(tile_row) #la ligne est totalement transformée en objets tile donc on peut l'ajouter à la grille principale

            entities = data.get("entities", []) #on récupère les entités du dico
            start_x, start_y = None, None #on veut ici enregistrer la position de départ du joueur
            for ent in entities:
                if ent.get("kind") == "player":
                    start_x = ent.get("x")
                    start_y = ent.get("y")
                    break
            if start_x is None or start_y is None:
                raise LevelError("La position du joueur n'a pas été déterminée ")
            
            self.start_pos = (start_x, start_y)


        except (KeyError, TypeError) as error : 
            raise LevelError (f"Erreur, structure JSON non valide où clé absente {error}") from error
        
        
        
        
        
        
        raise NotImplementedError("validate the map and create its tiles")

    @classmethod
    def load(cls, path: str) -> "Level":
        try : 
            f = open (path, "r", encoding="utf-8")
            data = json.load(f)
            f.close()  # On ferme le fichier et on crée l'objet level avec les bonnes données
            level_obj = cls(data)
            return level_obj
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e: # Si le fichier n'existe pas ou si le JSON est mal formé
            raise NotImplementedError("read JSON and convert errors to LevelError")

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
      