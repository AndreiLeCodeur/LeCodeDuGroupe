import pytest
from gridworld.models.player import Player

def test_player_independence(level_fixture):
    """Vérifie que le déplacement d'un joueur n'affecte pas les autres joueurs et la position de départ initiale du niveau."""
    start_pos = level_fixture.start_pos #position de base
    player1 = Player(position=initial_start_position) #on créer des joueurs et leur position de base
    player2 = Player(position=initial_start_position)
    player1.move("RIGHT") # Déplacer le premier joueur

    # p2 et la position de départ du niveau ne doivent pas avoir bougé
    assert player1.position != player2.position # on vérifie que le joueur a bien bougé
    assert level_fixture.start_pos == start #on vérifie que la position de départ du niveau reste inchangée


