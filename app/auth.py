"""Inicio de sesión y permisos por rol (admin / cajero)."""
import functools

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from .db import get_db

bp = Blueprint("auth", __name__)


@bp.before_app_request
def cargar_usuario():
    uid = session.get("usuario_id")
    g.usuario = None
    if uid is not None:
        g.usuario = get_db().execute(
            "SELECT id, usuario, nombre, rol FROM usuarios WHERE id = ? AND activo = 1", (uid,)
        ).fetchone()


def login_requerido(vista):
    @functools.wraps(vista)
    def envuelta(**kw):
        if g.usuario is None:
            return redirect(url_for("auth.login", siguiente=request.path))
        return vista(**kw)
    return envuelta


def solo_admin(vista):
    @functools.wraps(vista)
    @login_requerido
    def envuelta(**kw):
        if g.usuario["rol"] != "admin":
            flash("Esta sección es solo para administradores.", "error")
            return redirect(url_for("inicio.panel"))
        return vista(**kw)
    return envuelta


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        fila = get_db().execute(
            "SELECT * FROM usuarios WHERE usuario = ? AND activo = 1",
            (request.form.get("usuario", "").strip(),),
        ).fetchone()
        if fila is None or not check_password_hash(fila["clave_hash"], request.form.get("clave", "")):
            flash("Usuario o contraseña incorrectos.", "error")
        else:
            session.clear()
            session["usuario_id"] = fila["id"]
            destino = request.args.get("siguiente", "")
            return redirect(destino if destino.startswith("/") and not destino.startswith("//") else url_for("inicio.panel"))
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
