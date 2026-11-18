"""Conexión a SQLite y comandos de inicialización."""
import sqlite3
from pathlib import Path

import click
from flask import current_app, g


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        # isolation_level=None: las transacciones se abren a mano (BEGIN) en stock.py
        g.db = sqlite3.connect(current_app.config["DATABASE"], isolation_level=None)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    db.executescript(schema)


@click.command("init-db")
def init_db_command():
    """Borra y crea la base vacía."""
    init_db()
    click.echo("Base creada.")


@click.command("seed")
def seed_command():
    """Crea la base con datos de ejemplo (usuarios, productos y 30 días de ventas)."""
    from .seed import cargar_demo

    init_db()
    cargar_demo(get_db())
    click.echo("Base con datos de demo lista. Usuarios: admin / admin123 · cajero / cajero123")


@click.command("backup")
@click.argument("destino", required=False)
def backup_command(destino):
    """Copia la base en caliente (sin frenar el sistema)."""
    from datetime import datetime

    destino = destino or f"backup-{datetime.now():%Y-%m-%d_%H%M}.sqlite"
    with sqlite3.connect(destino) as copia:
        get_db().backup(copia)
    click.echo(f"Backup guardado en {destino}")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_command)
    app.cli.add_command(backup_command)
