import pytest
from gridworld.models.level import Level, LevelError

def test_load_n0_level():
    # N0 : dimensions 7x5, départ (1,1), sortie (5,1)
    current_dir = Path(__file__).parent
    level_path = current_dir / "levels" / "n0.json"
    level = Level.load(level_path)
    assert level.width == 7
    assert level.height == 5
    assert level.start_pos == (1, 1)
    assert level.exit_pos == (5, 1)

def test_invalid_level_data_raises_level_error(tmp_path):
    # Fichier JSON mal formé
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{ invalid json ...")
    with pytest.raises(LevelError):
        Level.load(bad_json)

    # Données de carte invalides (ex: dimensions incohérentes)
    invalid_map = tmp_path / "invalid.json"
    invalid_map.write_text('{"width": -1, "height": 5, "grid": []}')
    with pytest.raises(LevelError):
        Level.load(invalid_map)

def test_missing_file_raises_level_error():
    # Fichier manquant
    with pytest.raises(LevelError):
        Level.load("non_existent_file.json")

def test_get_tile_out_of_bounds(level_fixture):
    # Coordonnées hors grille (y compris négatives) doivent lever IndexError
    with pytest.raises(IndexError):
        level_fixture.get_tile(-1, 0)
    with pytest.raises(IndexError):
        level_fixture.get_tile(0, -1)
    with pytest.raises(IndexError):
        level_fixture.get_tile(100, 100)

def test_is_walkable_and_is_exit_out_of_bounds(level_fixture):
    # Hors grille doit renvoyer False sans lever d'erreur
    assert level_fixture.is_walkable(-1, 0) is False
    assert level_fixture.is_walkable(100, 100) is False
    assert level_fixture.is_exit(-1, 0) is False
    assert level_fixture.is_exit(100, 100) is False