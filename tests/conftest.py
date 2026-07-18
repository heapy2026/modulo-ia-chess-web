"""Shared pytest fixtures.

backend/ modules use flat imports (e.g. `from db import Base`), matching how
`python backend/app.py` runs them as scripts. Add backend/ to sys.path so the
same imports work from tests/.
"""

import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
