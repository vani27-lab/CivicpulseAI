"""Module 5 - Officer Dashboard backend.

Drop this package into the Module 1 FastAPI project at ``app/officer/`` and call
``include_module5_routers(app)`` from the application factory / ``main.py``.

Everything that touches FastAPI is imported lazily so the pure-logic modules
(workflow, uploads, priority, queries) can be imported and unit-tested without
the web stack installed.
"""


def include_module5_routers(app) -> None:
    from .routes import register

    register(app)
