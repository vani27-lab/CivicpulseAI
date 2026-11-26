import os

# Point Module 5's Module-1 dependencies at lightweight stubs for tests.
os.environ.setdefault("M5_GET_DB", "tests.stubs:get_db")
os.environ.setdefault("M5_GET_CURRENT_USER", "tests.stubs:get_current_user")
