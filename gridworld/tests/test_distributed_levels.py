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
    # TODO: load map_path with the real Level.load(str(map_path)).
    # Call play_scenario(level, scenario_path), which returns the final state.
    # Assert that state["status"] == "won" and state["message"] == "Victory!".
    pytest.fail("TODO: load the real map, run its scenario and check victory")