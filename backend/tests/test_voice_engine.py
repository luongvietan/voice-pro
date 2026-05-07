"""Unit tests không cần DB — mock deep-translator."""

from unittest.mock import MagicMock, patch

import pytest


@patch("deep_translator.GoogleTranslator")
def test_translate_text_delegates(mock_cls: MagicMock) -> None:
    inst = MagicMock()
    inst.translate.return_value = "xin chào"
    mock_cls.return_value = inst

    from app.voice_engine.translate import translate_text

    assert translate_text("hello", "auto", "vi") == "xin chào"
    mock_cls.assert_called_once()


@patch("deep_translator.GoogleTranslator")
def test_translate_long_text_chunks(mock_cls: MagicMock) -> None:
    inst = MagicMock()
    inst.translate.side_effect = lambda s: s  # identity — chỉ kiểm tra số lần gọi
    mock_cls.return_value = inst

    from app.voice_engine.translate import translate_text

    long_text = "word " * 2000  # >> 4500 chars
    out = translate_text(long_text, "auto", "en")
    assert inst.translate.call_count >= 2
    assert len(out) > 0


@patch("deep_translator.GoogleTranslator")
def test_translate_short_single_translate_call(mock_cls: MagicMock) -> None:
    inst = MagicMock()
    inst.translate.return_value = "ok"
    mock_cls.return_value = inst

    from app.voice_engine.translate import translate_text

    assert translate_text("short", "auto", "en") == "ok"
    assert inst.translate.call_count == 1


def test_run_sync_with_timeout_raises() -> None:
    import time

    from app.utils.sync_timeout import run_sync_with_timeout

    def slow() -> int:
        time.sleep(0.35)
        return 42

    with pytest.raises(TimeoutError, match="timed out"):
        run_sync_with_timeout(slow, timeout_seconds=0.08, operation_label="slow_op")
