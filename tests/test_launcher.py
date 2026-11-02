import pytest
import sys
from unittest.mock import patch

# Remplace __main__ par le nom exact de ton fichier si besoin
from gridworld.__main__ import main 

# --- 1. Tester le rendu par défaut (terminal) ---
@patch("gridworld.__main__.Level.load")
@patch("gridworld.__main__.BashRender")
@patch("gridworld.__main__.TerminalInput")
@patch("gridworld.__main__.Engine")
def test_main_default_is_terminal(mock_engine, mock_term_input, mock_bash, mock_level):
    # On simule l'appel sans aucun argument
    with patch.object(sys, "argv", ["gridworld"]):
        main()
    
    # Vérifications : terminal doit être sélectionné par défaut
    mock_level.assert_called_once_with("levels/n0.json")
    mock_bash.assert_called_once()
    mock_term_input.assert_called_once()
    mock_engine.assert_called_once()

# --- 2. Tester le rendu pygame et un niveau spécifique ---
@patch("gridworld.__main__.Level.load")
@patch("gridworld.__main__.PygameRender")
@patch("gridworld.__main__.PygameInput")
@patch("gridworld.__main__.Engine")
def test_main_pygame_and_custom_level(mock_engine, mock_pygame_input, mock_pygame_render, mock_level):
    # On simule : python -m gridworld --render pygame --level custom.json
    with patch.object(sys, "argv", ["gridworld", "--render", "pygame", "--level", "custom.json"]):
        main()
        
    # Vérifications
    mock_level.assert_called_once_with("custom.json")
    mock_pygame_render.assert_called_once()
    mock_pygame_input.assert_called_once()

# --- 3. Tester qu'un renderer inconnu est rejeté avant démarrage ---
@patch("gridworld.__main__.Level.load")
def test_invalid_renderer_rejected(mock_level):
    # On simule un argument invalide
    with patch.object(sys, "argv", ["gridworld", "--render", "3d_vr"]):
        # argparse détecte l'erreur et lève une exception SystemExit(2)
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 2
        # Preuve que le rejet a eu lieu AVANT le démarrage : le niveau n'est pas chargé
        mock_level.assert_not_called()

# --- 4. Tester la sécurité : start() et close() appelés même si le jeu plante ---
@patch("gridworld.__main__.Level.load")
@patch("gridworld.__main__.BashRender")
@patch("gridworld.__main__.TerminalInput")
@patch("gridworld.__main__.Engine")
def test_renderer_starts_and_closes_even_on_crash(mock_engine, mock_term_input, mock_bash, mock_level):
    # On sabote le moteur pour qu'il plante dès qu'on appelle run()
    mock_engine_instance = mock_engine.return_value
    mock_engine_instance.run.side_effect = RuntimeError("Le jeu a planté !")
    
    mock_bash_instance = mock_bash.return_value
    
    with patch.object(sys, "argv", ["gridworld"]):
        # On vérifie que l'erreur remonte bien
        with pytest.raises(RuntimeError, match="Le jeu a planté !"):
            main()
            
    # CRITÈRE : Malgré l'erreur, le lanceur doit avoir allumé et éteint l'écran
    mock_bash_instance.start.assert_called_once()
    mock_bash_instance.close.assert_called_once()