"""Paths and settings for the backend."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)

DB_PATH = os.path.join(REPO_ROOT, "games.db")
DATABASE_URI = f"sqlite:///{DB_PATH}"
