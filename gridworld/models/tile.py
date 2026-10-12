from gridworld.contracts import TileKind

#On définit les types possibles :
TILE_KINDS = {"floor", "wall", "exit"}


class Tile:

# Ici on vérifie que le type est bien dans la liste 
    def __init__(self, kind: TileKind) -> None:
        if kind not in TILE_KINDS :
            raise ValueError("type de case inconnue")
        self.kind = kind # Pour bien stocker le type !


# Ici on renvoie True seulement si ce n'est pas un mur, si c'est un mur on renvoi false
    def is_walkable(self) -> bool: 
        if self.kind == "wall" : 
            return False 
        else : 
            return True


# Ici on vérifie que le type est bien une exit
    def is_exit(self) -> bool:
        if self.kind == "exit" : 
            return True 
        else : 
            return False

    def to_state(self) -> TileKind:
        return self.kind
