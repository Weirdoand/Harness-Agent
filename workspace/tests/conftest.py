# -*- coding: utf-8 -*-
"""Make the ``notesapi`` flat modules (config/db/auth) importable.

The backend modules are imported as top-level modules (``import config``),
which is exactly how ``db.py`` imports it.  Adding ``workspace/notesapi`` to
``sys.path`` mirrors that runtime layout without touching the modules.
"""
from __future__ import annotations

import pathlib
import sys

_NOTESAPI = pathlib.Path(__file__).resolve().parents[1] / "notesapi"
if str(_NOTESAPI) not in sys.path:
    sys.path.insert(0, str(_NOTESAPI))
