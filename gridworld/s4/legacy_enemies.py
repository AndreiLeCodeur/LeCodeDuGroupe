"""SUPPLIED working behaviors with deliberately inconsistent interfaces.

Read this file, then refactor into enemies.py. Do not connect these classes
to Engine. Keep this reference so your tests can compare old and new behavior.
"""


class HorizontalGuard:
    def __init__(self, name, x, y):
        self.name, self.x, self.y, self.direction = name, x, y, 1

    def walk(self, board):
        if board.can_enter(self.name, self.x + self.direction, self.y):
            self.x += self.direction
        else:
            self.direction *= -1

    def as_entity(self):
        return {"id": self.name, "kind": "enemy", "x": self.x, "y": self.y,
                "appearance": "enemy.horizontal"}


class VerticalGuard:
    def __init__(self, identifier, x, y):
        self.identifier, self.coords, self.step = identifier, [x, y], 1

    def advance(self, environment):
        x, y = self.coords
        if environment.can_enter(self.identifier, x, y + self.step):
            self.coords[1] += self.step
        else:
            self.step = -self.step

    def dump(self):
        return {"id": self.identifier, "kind": "enemy",
                "x": self.coords[0], "y": self.coords[1],
                "appearance": "enemy.vertical"}


class Hunter:
    def __init__(self, key, x, y):
        self.key, self.location = key, (x, y)

    def chase(self, target, board):
        x, y = self.location
        px, py = target
        distance = abs(x - px) + abs(y - py)
        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if abs(nx - px) + abs(ny - py) < distance and board.can_enter(self.key, nx, ny):
                self.location = (nx, ny)
                return

    def snapshot(self):
        return {"id": self.key, "kind": "enemy",
                "x": self.location[0], "y": self.location[1],
                "appearance": "enemy.chaser"}
