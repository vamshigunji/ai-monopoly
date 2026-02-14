"""Tests for personality configurations."""

from monopoly.agents.personalities import (
    HUSTLER,
    PERSONALITIES,
    PROFESSOR,
    SHARK,
    TURTLE,
    get_personality,
)


def test_shark_uses_gpt4o():
    assert SHARK.model == "gpt-4o"


def test_professor_uses_gemini_pro():
    assert PROFESSOR.model == "gemini-1.5-pro"


def test_hustler_uses_gpt4o_mini():
    assert HUSTLER.model == "gpt-4o-mini"


def test_turtle_uses_gemini_flash():
    assert TURTLE.model == "gemini-1.5-flash"


def test_get_personality_returns_correct_config():
    assert get_personality(0) is SHARK
    assert get_personality(1) is PROFESSOR
    assert get_personality(2) is HUSTLER
    assert get_personality(3) is TURTLE


def test_all_personalities_have_system_prompts():
    for pid, p in PERSONALITIES.items():
        assert p.system_prompt, f"Player {pid} ({p.name}) missing system prompt"
        assert len(p.system_prompt) > 100, f"Player {pid} prompt too short"


def test_all_personalities_have_distinct_colors():
    colors = {p.color for p in PERSONALITIES.values()}
    assert len(colors) == 4, "All personalities must have distinct colors"
