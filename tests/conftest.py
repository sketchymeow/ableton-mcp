import os
import sys
from pathlib import Path

import pytest

# The remote script is not an installed package; Live loads it from a folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))


def pytest_collection_modifyitems(config, items):
    if os.environ.get("ABLETON_MCP_LIVE_TESTS") == "1":
        return
    skip = pytest.mark.skip(
        reason="needs Live running; set ABLETON_MCP_LIVE_TESTS=1"
    )
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)
