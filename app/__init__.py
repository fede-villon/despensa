"""Despensa: sistema de stock y ventas para almacenes y kioscos."""
import os
from pathlib import Path

from flask import Flask


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("DESPENSA_SECRET", "cambiar-en-produccion"),
        DATABASE=str(Path(app.instance_path) / "despensa.sqlite"),
    )
    if test_config:
        app.config.update(test_config)

    from . import db
    db.init_app(app)

    from .formato import registrar_filtros
    registrar_filtros(app)

    from . import auth, inicio, productos, ventas, compras, reportes
    for bp in (auth.bp, inicio.bp, productos.bp, ventas.bp, compras.bp, reportes.bp):
        app.register_blueprint(bp)

    return app
