# test/conftest.py
import os
import sys
from pathlib import Path

# This file is imported by pytest before tests are collected.
# Ensure the project root (the directory that contains base_aws/, base_auth/, daskhub/, etc.)
# is on sys.path so absolute imports work in CI.
PROJECT_ROOT = Path(__file__).resolve().parent  # .../platform
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
