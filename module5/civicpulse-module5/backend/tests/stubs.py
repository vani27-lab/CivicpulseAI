"""Stand-ins for Module 1 dependencies, used only by the tests."""


def get_db():
    yield object()  # route-access tests are rejected before any query runs


def get_current_user():
    return {"id": "00000000-0000-0000-0000-000000000001", "name": "Test", "role": "citizen"}
