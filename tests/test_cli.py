"""Tests for the command-line interface."""

from src.cli import main


def test_cli_analytics_command_prints_required_functions(tmp_path, monkeypatch, capsys) -> None:
    """The corrector can reach analytics from the terminal."""

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "habits.db"))
    main(["seed"])
    capsys.readouterr()

    main(["analytics"])
    output = capsys.readouterr().out

    assert "current_streak:" in output
    assert "longest_streak_all:" in output
    assert "completion_rate:" in output
    assert "habits_by_periodicity:" in output
    assert "daily=" in output
    assert "weekly=" in output
