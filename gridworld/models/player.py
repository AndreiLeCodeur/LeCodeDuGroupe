from gridworld.contracts import EntityState


class Player:
    """To implement. Player position; collisions belong to the engine."""


#En Python un booléen est un entier est on ne le veut pas dans x,y 
# On utilise alor isinstance pour vérifier cela
    def __init__(self, x: int, y: int) -> None:
        if isinstance(x, bool) or isinstance(y,bool) :
            raise TypeError("X et Y ne doivent pas être booléen")
        if not isinstance(x, int) or not isinstance(y, int) : # UTILE ??? x et y sont des int ???
            raise TypeError("X et Y doivent être entier")
        self.x = x
        self.y = y


# On renvoi simplement la position
    def get_position(self) -> tuple[int, int]:
        return (self.x, self.y)

# changement de position plus test de init pour verifier des coordonnées valide
    def move_to(self, x: int, y: int) -> None:
        if isinstance(x, bool) or isinstance(y,bool) :
            raise TypeError("X et Y ne doivent pas être booléen")
        if not isinstance(x, int) or not isinstance(y, int) : # UTILE ??? x et y sont des int ???
            raise TypeError("X et Y doivent être entier")       
        self.x = x
        self.y = y

# On retourne un perso complet 
    def to_state(self) -> EntityState:
        return {
            "id": "player-1",
            "kind": "player",
            "x": self.x,
            "y": self.y,
            "appearance": "player",
        }