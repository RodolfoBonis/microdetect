from microdetect.annotation.annotator.utils.constants import (
    DEFAULT_AUTO_SAVE,
    DEFAULT_AUTO_SAVE_INTERVAL,
    HANDLE_E,
    HANDLE_N,
    HANDLE_NE,
    HANDLE_NONE,
    HANDLE_NW,
    HANDLE_S,
    HANDLE_SE,
    HANDLE_SW,
    HANDLE_W,
    KEYBOARD_SHORTCUTS,
)


class TestConstants:

    def test_default_values(self):
        """Test default configuration values"""
        assert DEFAULT_AUTO_SAVE is True
        assert DEFAULT_AUTO_SAVE_INTERVAL == 20

    def test_handle_constants(self):
        """Test handle constants have correct values"""
        assert HANDLE_NONE == 0
        assert HANDLE_NW == 1
        assert HANDLE_NE == 2
        assert HANDLE_SE == 3
        assert HANDLE_SW == 4
        assert HANDLE_N == 5
        assert HANDLE_E == 6
        assert HANDLE_S == 7
        assert HANDLE_W == 8

    def test_keyboard_shortcuts(self):
        """Test keyboard shortcuts dictionary"""
        # Check essential shortcuts exist
        assert "a" in KEYBOARD_SHORTCUTS
        assert "z" in KEYBOARD_SHORTCUTS
        assert "s" in KEYBOARD_SHORTCUTS

        # Check descriptions are strings
        for key, desc in KEYBOARD_SHORTCUTS.items():
            assert isinstance(desc, str)
            assert len(desc) > 0
