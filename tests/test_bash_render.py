import copy
from unittest.mock import MagicMock

import pytest

from gridworld.views.bash_render import BashRender


@pytest.fixture
def sample_state():
    """Faux état de jeu au format JsonState (voir contracts.py / initial_state.json)."""
    return {
        "level": {
            "id": "test",
            "width": 3,
            "height": 2,
            "tiles": [
                ["floor", "wall", "floor"],
                ["floor", "floor", "exit"],
            ],
        },
        "entities": [
            {"id": "m-1", "kind": "monster", "x": 1, "y": 1, "appearance": "monster"},  # entité inconnue
            {"id": "player-1", "kind": "player", "x": 0, "y": 0, "appearance": "player"},
        ],
        "player_id": "player-1",
        "status": "playing",
        "turn": 12,
        "message": "Le joueur avance",
        "interaction": None,
        "extras": {},
    }


# --- 1. Tester le rendu texte et l'immutabilité ---
def test_state_to_string_format_and_immutability(sample_state):
    renderer = BashRender()
    original_state = copy.deepcopy(sample_state)

    texte = renderer.state_to_string(sample_state)
    lines = texte.splitlines()

    # floor=., wall=#, exit=E ; player=P, entité inconnue=?
    assert lines[0] == "P#."
    assert lines[1] == ".?E"
    assert "Turn: 12" in texte
    assert "Le joueur avance" in texte

    # Immutabilité : le dictionnaire d'entrée n'a pas été modifié
    assert sample_state == original_state


def test_entities_drawn_in_order(sample_state):
    # Deux entités sur la même case : la dernière de la liste est visible
    sample_state["entities"][0].update(x=0, y=0)
    texte = BashRender().state_to_string(sample_state)
    assert texte.splitlines()[0] == "P#."


def test_state_to_string_does_not_print(sample_state, capsys):
    BashRender().state_to_string(sample_state)
    assert capsys.readouterr().out == ""


# --- 2. Tester la délégation dans update_render ---
def test_update_render_calls_methods_exactly_once(sample_state):
    renderer = BashRender()

    renderer.state_to_string = MagicMock(return_value="grille_dessinee")
    renderer.refresh = MagicMock()

    renderer.update_render(sample_state)

    renderer.state_to_string.assert_called_once_with(sample_state)
    renderer.refresh.assert_called_once_with("grille_dessinee")


def test_start_and_close_are_safe():
    renderer = BashRender()
    renderer.start()
    renderer.close()
    renderer.close()  # close doit être idempotent
