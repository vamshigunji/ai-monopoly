"""Shared test fixtures for Monopoly game engine tests."""

import pytest

from monopoly.engine.board import Board
from monopoly.engine.dice import Dice
from monopoly.engine.player import Player
from monopoly.engine.game import Game


@pytest.fixture
def board():
    """Create a standard Monopoly board."""
    return Board()


@pytest.fixture
def deterministic_dice():
    """Create dice with a fixed seed for reproducible tests."""
    return Dice(seed=42)


@pytest.fixture
def player():
    """Create a single player with default starting state."""
    return Player(player_id=0, name="TestPlayer")


@pytest.fixture
def four_players():
    """Create 4 players for a standard game."""
    return [
        Player(player_id=0, name="Player1"),
        Player(player_id=1, name="Player2"),
        Player(player_id=2, name="Player3"),
        Player(player_id=3, name="Player4"),
    ]


@pytest.fixture
def game():
    """Create a standard 4-player game with deterministic dice."""
    return Game(num_players=4, seed=42)
