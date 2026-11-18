import pytest

from app import create_app
from app.db import get_db, init_db
from app.seed import cargar_demo


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite"), "SECRET_KEY": "test"})
    with app.app_context():
        init_db()
        cargar_demo(get_db())
    return app


@pytest.fixture
def cliente(app):
    return app.test_client()


def ingresar(cliente, usuario="admin", clave="admin123"):
    return cliente.post("/login", data={"usuario": usuario, "clave": clave})
