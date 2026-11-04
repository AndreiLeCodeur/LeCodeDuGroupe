import pytest
from pathlib import Path
from gridworld.models.level import Level

@pytest.fixture
def level_fixture():
    # Charge un niveau par défaut (par exemple n0.json) pour les tests
    level_path = Path(__file__).parent.parent.parent / "levels" / "n0.json"
    # Si vos niveaux sont dans un autre dossier, ajustez le chemin ci-dessus
    return Level.load(level_path)

@pytest.fixture
def game_engine(level_fixture):
    # Si vous avez une classe Game ou Engine, instanciez-la ici, par exemple :
    # from gridworld.models.game import Game
    # return Game(level_fixture)
    pass

@pytest.fixture
def game_engine_near_wall(level_fixture):
    # Retourne un moteur positionné près d'un mur si nécessaire
    pass