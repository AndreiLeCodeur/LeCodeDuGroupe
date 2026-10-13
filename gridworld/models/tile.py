from gridworld.contracts import TileKind


class Tile:
    """Terrain without player or rendering logic."""

    def __init__(self, kind: TileKind) -> None:
        raise NotImplementedError("validate and store the tile kind")

    def is_walkable(self) -> bool:
        raise NotImplementedError("a wall tile is not walkable")

    def is_exit(self) -> bool:
        raise NotImplementedError("identify the exit")

    def to_state(self) -> TileKind:
        raise NotImplementedError("expose the terrain kind")

from gridworld.contracts import TileKind


class Tile:
    """Terrain without player or rendering logic."""

    def __init__(self, kind: TileKind) -> None:
        # On regarde si l'on est sur un case d'un type acceptable
        if kind not in ("floor", "wall", "exit"):
            raise ValueError(f"Type de case inconnu : {kind}")
        self.kind: TileKind = kind

    def is_walkable(self) -> bool:
        # Les murs bloquent le passage, le sol et la sortie sont franchissables
        return self.kind != "wall"

    def is_exit(self) -> bool:
        # Renvoie True uniquement s'il s'agit d'une case de sortie
        return self.kind == "exit"

    def to_state(self) -> TileKind:
        # Expose le type de terrain
        return self.kind