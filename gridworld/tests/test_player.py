import pytest
from gridworld.models.player import Player

def test_player_independence(level_fixture):
    """Vérifie que le déplacement d'un joueur n'affecte pas les autres joueurs et la position de départ initiale du niveau."""
    start_pos = level_fixture.start_pos
    # Le Player prend x et y en paramètres
    player1 = Player(start_pos[0], start_pos[1])
    player2 = Player(start_pos[0], start_pos[1])

    # On déplace le premier joueur
    player1.move_to(start_pos[0] + 1, start_pos[1])

    assert player1.get_position() != player2.get_position() # on vérifie que le joueur a bien bougé
    assert level_fixture.start_pos == start_pos #on vérifie que la position de départ du niveau reste inchangée
