import pytest
import copy
from unittest.mock import MagicMock

# Ajuste le chemin d'import selon ton projet
from gridworld.views.bash_render import BashRender

@pytest.fixture
def sample_state():
    """Crée un faux état de jeu pour nos tests."""
    return {
        "turn": 12,
        "messages": ["Le joueur avance"],
        "map_width": 3,
        "map_height": 2,
        "wall_coords": [(1, 0)],
        "exit_coords": [(2, 1)],
        "entities": [
            {"coords": (0, 0), "appearance": "player"},
            {"coords": (1, 1), "appearance": "monster"} # Entité inconnue
        ]
    }

# --- 1. Tester le rendu texte et l'immutabilité ---
def test_state_to_string_format_and_immutability(sample_state):
    renderer = BashRender()
    
    # On fait une copie exacte de l'état pour vérifier qu'il ne bouge pas
    original_state = copy.deepcopy(sample_state)
    
    # Appel de la méthode
    texte = renderer.state_to_string(sample_state)
    
    # Vérifications du texte généré
    assert "Turn: 12" in texte
    assert "Le joueur avance" in texte
    
    # Le prof demande P pour player, ? pour inconnu, # pour mur, . pour vide, E pour exit
    # On vérifie au moins la présence de ces caractères dans le rendu
    assert "P" in texte
    assert "?" in texte
    
    # Vérification CRUCIALE (immutabilité) : le dictionnaire d'entrée n'a pas été modifié
    assert sample_state == original_state

# --- 2. Tester la délégation dans update_render ---
def test_update_render_calls_methods_exactly_once(sample_state):
    renderer = BashRender()
    
    # On remplace temporairement les méthodes par des "espions" (Mocks)
    renderer.state_to_string = MagicMock(return_value="grille_dessinee")
    renderer.refresh = MagicMock()
    
    # Appel de la méthode à tester
    renderer.update_render(sample_state)
    
    # Vérifications : chaque méthode doit être appelée UNE seule fois, avec les bons arguments
    renderer.state_to_string.assert_called_once_with(sample_state)
    renderer.refresh.assert_called_once_with("grille_dessinee")