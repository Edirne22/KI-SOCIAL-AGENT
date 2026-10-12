"""Regression tests for Telegram MotoGP approval command parsing."""
from motogp_telegram_receive_v85 import selection


def test_repeated_prefix_and_trailing_comma():
    assert selection("motogp 4, motogp 3,") == [3, 4]
    assert selection("motogp 4, motogp 3") == [3, 4]
    assert selection("motogp 4,3") == [3, 4]


def test_invalid_commands_remain_rejected():
    assert selection("motogp 4, motogp 9,") is None
    assert selection("motogp 4, garbage") is None
    assert selection("motogp 4, motogp") is None
