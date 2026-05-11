import sys
from unittest.mock import patch


def test_import_does_not_create_log_directory():
    """Importing livesttt.logging must not touch the filesystem."""
    for key in list(sys.modules):
        if "livesttt" in key:
            del sys.modules[key]

    with patch("pathlib.Path.mkdir") as mock_mkdir:
        import livesttt.logging  # noqa: F401
        mock_mkdir.assert_not_called()
