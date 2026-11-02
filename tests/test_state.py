import pytest
import json
from unittest.mock import MagicMock

from gridworld.engine import Engine

@pytest.fixture
def engine():
    # On simule les dépendances pour isoler le moteur
    mock_level = MagicMock()
    mock_level.get_start.return_value = (0, 0)
    mock_level.to_state.return_value = {"map_data": [1, 2, 3]}
    
    mock_controller = MagicMock()
    mock_renderer = MagicMock()
    
    # On instancie le moteur avec ces faux objets
    return Engine(level=mock_level, controller=mock_controller, renderer=mock_renderer)

# --- 1. Tester les 8 champs et la conversion JSON ---
def test_get_state_fields_and_json_serializable(engine):
    state = engine.get_state()
    
    # Les 8 clés exactes définies dans ton code
    expected_keys = {"level", "entities", "player_id", "status", "turn", "message", "interaction", "extras"}
    assert set(state.keys()) == expected_keys
    
    try:
        json.dumps(state)
    except TypeError:
        pytest.fail("L'état n'est pas sérialisable en JSON")

# --- 2. Tester que la lecture ne fait pas avancer le jeu ---
def test_multiple_reads_do_not_advance_game(engine):
    state1 = engine.get_state()
    state2 = engine.get_state()
    
    assert state1["turn"] == state2["turn"]
    assert state1 == state2

# --- 3. Tester la délégation du moteur (Consigne S1-03) ---
def test_engine_delegates_correctly(engine):
    # Vérifie get_action
    engine.controller.get_action.return_value = "north"
    assert engine.get_action() == "north"
    engine.controller.get_action.assert_called_once()
    
    # Vérifie render
    fake_state = {"test": "data"}
    engine.render(fake_state)
    engine.renderer.update_render.assert_called_once_with(fake_state)

# --- 4. LE PIÈGE : L'état mutable partagé (Défaut de référence imbriquée) ---
def test_state_immutability_and_nested_references(engine):
    # On met une vraie donnée dans extras pour le test
    engine.extras = {"inventaire": ["épée"]}
    
    state1 = engine.get_state()
    
    # 💥 Modification malveillante sur un objet imbriqué
    state1["extras"]["inventaire"].append("hacked_item")
    
    # On redemande l'état au jeu
    state2 = engine.get_state()
    
    # Le vrai moteur ne doit pas contenir "hacked_item"
    # (Ce test va échouer avec ton code actuel, et c'est exactement le but !)
    assert "hacked_item" not in state2["extras"]["inventaire"]