"""Caja: carrito de venta y listado de ventas."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for

from .auth import login_requerido
from .db import get_db
from .formato import MEDIOS
from .stock import ErrorStock, registrar_venta

bp = Blueprint("ventas", __name__, url_prefix="/ventas")


def _carrito() -> dict[str, int]:
    return session.setdefault("carrito", {})


@bp.route("/caja")
@login_requerido
def caja():
    db = get_db()
    carrito = _carrito()
    items, total = [], 0
    for pid, cant in carrito.items():
        p = db.execute("SELECT id, codigo, nombre, precio_venta, stock FROM productos WHERE id = ?", (int(pid),)).fetchone()
        if p:
            sub = p["precio_venta"] * cant
            total += sub
            items.append({"p": p, "cantidad": cant, "subtotal": sub})
    q = request.args.get("q", "").strip()
    resultados = []
    if q:
        resultados = db.execute(
            """SELECT id, codigo, nombre, precio_venta, stock FROM productos
               WHERE activo = 1 AND (codigo = ? OR nombre LIKE ?) ORDER BY nombre LIMIT 12""",
            (q, f"%{q}%"),
        ).fetchall()
    return render_template("ventas/caja.html", items=items, total=total, q=q, resultados=resultados)


@bp.route("/caja/agregar", methods=("POST",))
@login_requerido
def agregar():
    db = get_db()
    pid = request.form.get("producto_id", type=int)
    codigo = request.form.get("codigo", "").strip()
    cant = max(1, request.form.get("cantidad", type=int, default=1))
    if pid is None and codigo:
        fila = db.execute("SELECT id FROM productos WHERE codigo = ? AND activo = 1", (codigo,)).fetchone()
        if fila is None:
            # Si no es un código exacto, lo tratamos como búsqueda por nombre.
            return redirect(url_for("ventas.caja", q=codigo))
        pid = fila["id"]
    if pid is None:
        return redirect(url_for("ventas.caja"))
    carrito = _carrito()
    carrito[str(pid)] = carrito.get(str(pid), 0) + cant
    session.modified = True
    return redirect(url_for("ventas.caja"))


@bp.route("/caja/quitar/<int:pid>", methods=("POST",))
@login_requerido
def quitar(pid):
    _carrito().pop(str(pid), None)
    session.modified = True
    return redirect(url_for("ventas.caja"))


@bp.route("/caja/vaciar", methods=("POST",))
@login_requerido
def vaciar():
    session["carrito"] = {}
    return redirect(url_for("ventas.caja"))


@bp.route("/caja/cobrar", methods=("POST",))
@login_requerido
def cobrar():
    medio = request.form.get("medio_pago", "")
    if medio not in MEDIOS:
        flash("Elegí un medio de pago.", "error")
        return redirect(url_for("ventas.caja"))
    items = {int(k): v for k, v in _carrito().items()}
    try:
        venta_id = registrar_venta(get_db(), g.usuario["id"], items, medio)
    except ErrorStock as e:
        flash(str(e), "error")
        return redirect(url_for("ventas.caja"))
    session["carrito"] = {}
    flash(f"Venta #{venta_id} registrada.", "ok")
    return redirect(url_for("ventas.ticket", vid=venta_id))


@bp.route("/")
@login_requerido
def lista():
    desde = request.args.get("desde", "")
    hasta = request.args.get("hasta", "")
    sql = """SELECT v.*, u.nombre AS cajero, (SELECT SUM(cantidad) FROM venta_items WHERE venta_id = v.id) AS unidades
             FROM ventas v JOIN usuarios u ON u.id = v.usuario_id WHERE 1 = 1"""
    args = []
    if desde:
        sql += " AND date(v.fecha) >= ?"
        args.append(desde)
    if hasta:
        sql += " AND date(v.fecha) <= ?"
        args.append(hasta)
    sql += " ORDER BY v.id DESC LIMIT 200"
    ventas = get_db().execute(sql, args).fetchall()
    return render_template("ventas/lista.html", ventas=ventas, desde=desde, hasta=hasta)


@bp.route("/<int:vid>")
@login_requerido
def ticket(vid):
    db = get_db()
    v = db.execute(
        "SELECT v.*, u.nombre AS cajero FROM ventas v JOIN usuarios u ON u.id = v.usuario_id WHERE v.id = ?", (vid,)
    ).fetchone()
    if v is None:
        abort(404)
    items = db.execute(
        """SELECT vi.*, p.nombre, p.codigo FROM venta_items vi JOIN productos p ON p.id = vi.producto_id
           WHERE vi.venta_id = ?""",
        (vid,),
    ).fetchall()
    return render_template("ventas/ticket.html", v=v, items=items)
