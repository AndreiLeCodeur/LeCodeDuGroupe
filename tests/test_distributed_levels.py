"""Complete the per-map test; collection and scenario execution are supplied."""
from pathlib import Path

import pytest

from gridworld.models.level import Level
from tests.s3_support import play_scenario

MAPS = sorted(Path("levels").rglob("*.json"))
if not MAPS:
    raise RuntimeError("No distributed maps found in levels/")


@pytest.mark.parametrize("map_path", MAPS, ids=lambda path: path.as_posix())
def test_distributed_map_can_be_won(map_path):
    scenario_path = Path("scenarios") / map_path.relative_to("levels")
    level = Level.load(str(map_path))
    state = play_scenario(level, scenario_path)
    assert state["status"] == "won", f"{scenario_path} does not win {map_path}: {state['message']!r}"
    assert state["message"] == "Victory!"