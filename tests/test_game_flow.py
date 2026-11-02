import pytest
import copy
from unittest.mock import MagicMock

from gridworld.engine import Engine
from gridworld.controllers.controller import Controller
from gridworld.models.level import Level 

class SpyRenderer:
    def __init__(self):
        self.history = []

    def update_render(self, state):
        self.history.append(copy.deepcopy(state))

def test_game_flow_winning_path_and_post_victory():
    # 1. Clavier simulé (Parcours gagnant N0 + touches post-victoire)
    inputs = ["d", "s", "s", "d", "d", "d", "z", "z", "k", " ", ":quit"]
    
    mock_input_source = MagicMock()
    mock_input_source.read_key.side_effect = inputs
    
    controller = Controller(mock_input_source)
    spy_renderer = SpyRenderer()
    
    # 2. Vrai niveau instancié avec le format exact attendu par Level(__init__)
    level_data = {
        "id": "n0",
        "grid": [
            "#######",
            "#..#..#",
            "#..#..#",
            "#.....#",
            "#######"
        ],
        "start": {"x": 1, "y": 1},
        "exit": {"x": 5, "y": 1}
    }
    real_level = Level(level_data)
    
    # 3. Lancer le moteur
    engine = Engine(level=real_level, controller=controller, renderer=spy_renderer)
    engine.run()
    
    # 4. Vérifications
    first_state = spy_renderer.history[0]
    assert first_state["turn"] == 0
    assert first_state["status"] == "playing"
    
    # L'indice 8 correspond au 9ème rendu (car on rend l'état 0 au début)
    win_state = spy_renderer.history[8]
    assert win_state["turn"] == 8
    assert win_state["status"] == "won"
    assert win_state["message"] == "Victory!"
    
    # L'état final après les touches supplémentaires ne doit pas avoir bougé
    final_state = spy_renderer.history[-1]
    assert final_state["turn"] == 8
    assert final_state["status"] == "won"

    # Le jeu doit avoir continué à tourner pour lire les 11 touches jusqu'au :quit
    assert mock_input_source.read_key.call_count == len(inputs)