import pytest
from datetime import date
from unittest.mock import patch

import config
import dates


def test_parse_date_dmy():
    assert dates.parse_date("01/02/2026") == date(2026, 2, 1)


def test_parse_date_ymd():
    assert dates.parse_date("2026-02-01") == date(2026, 2, 1)


def test_parse_date_com_espacos():
    assert dates.parse_date("  01/02/2026  ") == date(2026, 2, 1)


def test_parse_date_invalida():
    with pytest.raises(ValueError):
        dates.parse_date("nao-e-data")


def test_format_date():
    assert dates.format_date(date(2026, 2, 1)) == "01/02/2026"


def test_calc_days():
    with patch("dates.date") as mock_date:
        mock_date.today.return_value = date(2026, 5, 1)
        result = dates.calc_days(date(2026, 4, 16))
    assert result == 15


def test_is_expired_true():
    original = config.EXP_DAYS
    config.EXP_DAYS = 15
    try:
        with patch("dates.date") as mock_date:
            mock_date.today.return_value = date(2026, 5, 1)
            assert dates.is_expired(date(2026, 4, 16)) is True
    finally:
        config.EXP_DAYS = original


def test_is_expired_false():
    original = config.EXP_DAYS
    config.EXP_DAYS = 15
    try:
        with patch("dates.date") as mock_date:
            mock_date.today.return_value = date(2026, 5, 1)
            assert dates.is_expired(date(2026, 4, 20)) is False
    finally:
        config.EXP_DAYS = original


def test_calc_duration():
    assert dates.calc_duration(date(2026, 1, 1), date(2026, 1, 16)) == 15


def test_calc_duration_negativo():
    assert dates.calc_duration(date(2026, 1, 16), date(2026, 1, 1)) == -15
