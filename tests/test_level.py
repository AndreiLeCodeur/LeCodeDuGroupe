import pytest
from pathlib import Path
from gridworld.models.level import Level, LevelError

def test_load_valid_level_custom(tmp_path):
    # Crée un fichier JSON temporaire valide basé sur la structure attendue par level.py
    valid_data = {
        "id": "test_map",
        "grid": [
            "###",
            "#.#",
            "#E#"
        ],
        "start": {"x": 1, "y": 1},
        "exit": {"x": 1, "y": 2}
    }

    file_path = tmp_path / "valid_level.json"
    import json
    file_path.write_text(json.dumps(valid_data))

    level = Level.load(str(file_path))
    assert level.width == 3
    assert level.height == 3
    assert level.get_start() == (1, 1)
    assert level.is_walkable(1, 1) is True
    assert level.is_exit(1, 2) is True

def test_level_out_of_bounds(tmp_path):
    valid_data = {
        "id": "test_map",
        "grid": [
            "###",
            "#.#",
            "#E#"
        ],
        "start": {"x": 1, "y": 1},
        "exit": {"x": 1, "y": 2}
    }
    file_path = tmp_path / "valid_level.json"
    import json
    file_path.write_text(json.dumps(valid_data))

    level = Level.load(str(file_path))

    # get_tile lève IndexError hors de la grille ou pour des coordonnées négatives
    with pytest.raises(IndexError):
        level.get_tile(-1, 0)
    with pytest.raises(IndexError):
        level.get_tile(5, 5)

    # is_walkable et is_exit renvoient False hors de la grille
    assert level.is_walkable(-1, -1) is False
    assert level.is_exit(10, 10) is False

def test_load_invalid_or_missing_level(tmp_path):
    # Fichier manquant -> LevelError
    with pytest.raises(LevelError):
        Level.load("levels/non_existent_file.json")

    # JSON mal formé -> LevelError
    bad_json_file = tmp_path / "bad.json"
    bad_json_file.write_text("{ invalid json syntax }")
    with pytest.raises(LevelError):
        Level.load(str(bad_json_file))

def test_level_errors_structure(tmp_path):
    # Grille vide -> LevelError
    empty_grid_data = {
        "id": "empty",
        "grid": [],
        "start": {"x": 0, "y": 0},
        "exit": {"x": 0, "y": 0}
    }
    f1 = tmp_path / "empty.json"
    import json
    f1.write_text(json.dumps(empty_grid_data))
    with pytest.raises(LevelError):
        Level.load(str(f1))