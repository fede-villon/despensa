"""Compras a proveedores (ingreso de mercadería) y alta de proveedores."""
import sqlite3

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .auth import solo_admin
from .db import get_db
from .stock import ErrorStock, registrar_compra

bp = Blueprint("compras", __name__, url_prefix="/compras")


@bp.route("/")
@solo_admin
def lista():
    db = get_db()
    compras = db.execute(
        """SELECT c.*, p.nombre AS proveedor,
                  (SELECT SUM(cantidad) FROM compra_items WHERE compra_id = c.id) AS unidades
           FROM compras c JOIN proveedores p ON p.id = c.proveedor_id ORDER BY c.id DESC LIMIT 100"""
    ).fetchall()
    proveedores = db.execute(
        """SELECT pr.*, (SELECT COUNT(*) FROM productos WHERE proveedor_id = pr.id AND activo = 1) AS productos
           FROM proveedores pr ORDER BY nombre"""
    ).fetchall()
    return render_template("compras/lista.html", compras=compras, proveedores=proveedores)


@bp.route("/nueva", methods=("GET", "POST"))
@solo_admin
def nueva():
    db = get_db()
    proveedores = db.execute("SELECT id, nombre FROM proveedores ORDER BY nombre").fetchall()
    proveedor_id = request.values.get("proveedor_id", type=int)
    productos = []
    if proveedor_id:
        productos = db.execute(
            """SELECT id, codigo, nombre, stock, stock_minimo, precio_costo FROM productos
               WHERE activo = 1 AND proveedor_id = ? ORDER BY nombre""",
            (proveedor_id,),
        ).fetchall()
    if request.method == "POST" and proveedor_id:
        items = []
        for p in productos:
            cant = request.form.get(f"cant_{p['id']}", type=int, default=0) or 0
            costo = request.form.get(f"costo_{p['id']}", type=int, default=p["precio_costo"])
            if cant < 0 or costo is None or costo < 0:
                flash(f"Revisá los valores de {p['nombre']}.", "error")
                break
            items.append((p["id"], cant, costo))
        else:
            try:
                cid = registrar_compra(db, g.usuario["id"], proveedor_id, items,
                                       actualizar_costo=bool(request.form.get("actualizar_costo")))
                flash(f"Compra #{cid} registrada: el stock ya se actualizó.", "ok")
                return redirect(url_for("compras.lista"))
            except ErrorStock as e:
                flash(str(e), "error")
    return render_template("compras/nueva.html", proveedores=proveedores, proveedor_id=proveedor_id, productos=productos)


@bp.route("/proveedores", methods=("POST",))
@solo_admin
def nuevo_proveedor():
    nombre = request.form.get("nombre", "").strip()
    if not nombre:
        flash("El proveedor necesita un nombre.", "error")
    else:
        try:
            get_db().execute(
                "INSERT INTO proveedores (nombre, telefono, email) VALUES (?, ?, ?)",
                (nombre, request.form.get("telefono", "").strip() or None, request.form.get("email", "").strip() or None),
            )
            flash(f"Proveedor «{nombre}» agregado.", "ok")
        except sqlite3.IntegrityError:
            flash("Ya existe un proveedor con ese nombre.", "error")
    return redirect(url_for("compras.lista"))
