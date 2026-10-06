"""Shared S0 interfaces: review with the tutor and follow in your implementation."""
from typing import Literal, Protocol, TypedDict

Action = Literal["north", "east", "south", "west", "wait", "quit"]
TileKind = str

class EntityState(TypedDict):
    id: str
    kind: str
    x: int
    y: int
    appearance: str

class LevelState(TypedDict):
    id: str
    width: int
    height: int
    tiles: list[list[TileKind]]

class JsonState(TypedDict):
    level: LevelState
    entities: list[EntityState]
    player_id: str
    status: Literal["playing", "won", "lost"]
    turn: int
    message: str
    interaction: dict | None  # Reserved: always None in S0.
    extras: dict[str, object]  # JSON values only; empty in the base S0 game.

class Renderer(Protocol):
    def start(self) -> None: ...
    def update_render(self, json_state: JsonState) -> None: ...
    def close(self) -> None: ...

class InputSource(Protocol):
    """Read a raw key without translating it into an Action or applying game rules."""
    def read_key(self) -> str | None: ...
