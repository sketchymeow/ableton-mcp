import sys
from pathlib import Path

# The remote script is not an installed package; Live loads it from a folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "remote_script"))
