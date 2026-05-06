"""Epic 4 — credit billing helpers."""

from app.services.credit_metering import minutes_to_charge


def test_minutes_to_charge_zero_duration():
    assert minutes_to_charge(0) == 0
    assert minutes_to_charge(-1) == 0


def test_minutes_to_charge_rounds_up_per_minute():
    assert minutes_to_charge(1) == 1
    assert minutes_to_charge(59.9) == 1
    assert minutes_to_charge(60) == 1
    assert minutes_to_charge(61) == 2
    assert minutes_to_charge(120) == 2
