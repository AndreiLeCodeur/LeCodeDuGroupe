import pytest
from unittest.mock import patch

# Ajuste cet import selon le nom exact de ton fichier et de ta classe
from gridworld.controllers.terminal_input import TerminalInput

# --- 1. Tester l'interruption clavier (Ctrl+C) ---
@patch('builtins.input', side_effect=KeyboardInterrupt)
def test_keyboard_interrupt_returns_quit(mock_input):
    terminal = TerminalInput()
    assert terminal.read_key() == ":quit"

# --- 2. Tester la fin de fichier (EOF / Ctrl+D) ---
@patch('builtins.input', side_effect=EOFError)
def test_eof_returns_quit(mock_input):
    terminal = TerminalInput()
    assert terminal.read_key() == ":quit"

# --- 3. Tester la conservation de l'espace ---
@patch('builtins.input', return_value=" ")
def test_preserves_space(mock_input):
    terminal = TerminalInput()
    assert terminal.read_key() == " "