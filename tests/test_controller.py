import pytest
from unittest.mock import MagicMock

# Ajuste cet import selon l'architecture exacte de ton dossier
from gridworld.controllers.controller import Controller

# --- 1. Tester toutes les touches valides ---
@pytest.mark.parametrize("key, expected_action", [
    ("z", "north"), ("Z", "north"), ("ArrowUp", "north"),
    ("s", "south"), ("S", "south"), ("ArrowDown", "south"),
    ("q", "west"), ("Q", "west"), ("ArrowLeft", "west"),
    ("d", "east"), ("D", "east"), ("ArrowRight", "east"),
    (" ", "wait"),
    (":quit", "quit"), ("Escape", "quit")
])
def test_valid_keys_return_correct_action(key, expected_action):
    # On crée un faux input_source, on n'en a pas besoin pour cette méthode
    mock_input = MagicMock()
    controller = Controller(mock_input)
    
    assert controller.key_to_action(key) == expected_action


# --- 2. Tester les touches inconnues ---
def test_unknown_key_returns_none():
    mock_input = MagicMock()
    controller = Controller(mock_input)
    
    # Une touche qui n'est pas dans le dictionnaire
    assert controller.key_to_action("k") is None
    assert controller.key_to_action("n'importe quoi") is None


# --- 3. Tester l'absence d'entrée ---
def test_no_input_returns_none():
    mock_input = MagicMock()
    controller = Controller(mock_input)
    
    assert controller.key_to_action(None) is None


# --- 4. Tester get_action et la lecture unique ---
def test_get_action_reads_source_exactly_once():
    mock_input = MagicMock()
    # On dit au faux clavier de renvoyer "z" quand on l'appelle
    mock_input.read_key.return_value = "z" 
    
    controller = Controller(mock_input)
    result = controller.get_action()
    
    # On vérifie que ça a bien renvoyé l'action attendue pour "z"
    assert result == "north"
    # On vérifie que la méthode read_key a été appelée exactement une fois
    mock_input.read_key.assert_called_once()