"""Unit tests không cần DB — mock deep-translator."""

from unittest.mock import MagicMock, patch


@patch("deep_translator.GoogleTranslator")
def test_translate_text_delegates(mock_cls: MagicMock) -> None:
    inst = MagicMock()
    inst.translate.return_value = "xin chào"
    mock_cls.return_value = inst

    from app.voice_engine.translate import translate_text

    assert translate_text("hello", "auto", "vi") == "xin chào"
    mock_cls.assert_called_once()
