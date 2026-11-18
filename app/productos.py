"""Productos: listado, alta, edición, ajuste de stock e historial de movimientos."""
import sqlite3

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .auth import login_requerido, solo_admin
from .db import get_db
from .stock import ErrorStock, ajustar_stock

bp = Blueprint("productos", __name__, url_prefix="/productos")


def _opciones():
    db = get_db()
    return (
        db.execute("SELECT id, nombre FROM categorias ORDER BY nombre").fetchall(),
        db.execute("SELECT id, nombre FROM proveedores ORDER BY nombre").fetchall(),
    )


@bp.route("/")
@login_requerido
def lista():
    q = request.args.get("q", "").strip()
    cat = request.args.get("categoria", type=int)
    filtro = request.args.get("filtro", "")
    sql = """SELECT p.*, c.nombre AS categoria FROM productos p
             LEFT JOIN categorias c ON c.id = p.categoria_id WHERE p.activo = 1"""
    args: list = []
    if q:
        sql += " AND (p.nombre LIKE ? OR p.codigo LIKE ?)"
        args += [f"%{q}%", f"%{q}%"]
    if cat:
        sql += " AND p.categoria_id = ?"
        args.append(cat)
    if filtro == "bajo":
        sql += " AND p.stock <= p.stock_minimo"
    sql += " ORDER BY p.nombre"
    productos = get_db().execute(sql, args).fetchall()
    categorias, _ = _opciones()
    return render_template("productos/lista.html", productos=productos, categorias=categorias,
                           q=q, cat=cat, filtro=filtro)


def _leer_form():
    f = request.form
    errores = []
    datos = {
        "codigo": f.get("codigo", "").strip(),
        "nombre": f.get("nombre", "").strip(),
        "categoria_id": f.get("categoria_id", type=int),
        "proveedor_id": f.get("proveedor_id", type=int),
        "precio_costo": f.get("precio_costo", type=int),
        "precio_venta": f.get("precio_venta", type=int),
        "stock_minimo": f.get("stock_minimo", type=int, default=0),
        "vencimiento": f.get("vencimiento") or None,
    }
    if not datos["codigo"] or not datos["nombre"]:
        errores.append("Código y nombre son obligatorios.")
    if datos["precio_costo"] is None or datos["precio_venta"] is None or datos["precio_costo"] < 0 or datos["precio_venta"] < 0:
        errores.append("Los precios tienen que ser números enteros positivos.")
    elif datos["precio_venta"] < datos["precio_costo"]:
        errores.append("El precio de venta es menor al costo: revisalo.")
    if datos["stock_minimo"] is None or datos["stock_minimo"] < 0:
        errores.append("El stock mínimo no puede ser negativo.")
    return datos, errores


@bp.route("/nuevo", methods=("GET", "POST"))
@solo_admin
def nuevo():
    categorias, proveedores = _opciones()
    if request.method == "POST":
        datos, errores = _leer_form()
        stock_inicial = request.form.get("stock", type=int, default=0)
        if stock_inicial is None or stock_inicial < 0:
            errores.append("El stock inicial no puede ser negativo.")
        if not errores:
            db = get_db()
            try:
                db.execute("BEGIN")
                cur = db.execute(
                    """INSERT INTO productos (codigo, nombre, categoria_id, proveedor_id, precio_costo,
                       precio_venta, stock, stock_minimo, vencimiento)
                       VALUES (:codigo, :nombre, :categoria_id, :proveedor_id, :precio_costo,
                       :precio_venta, :stock, :stock_minimo, :vencimiento)""",
                    {**datos, "stock": stock_inicial},
                )
                if stock_inicial:
                    db.execute(
                        "INSERT INTO movimientos_stock (producto_id, cantidad, motivo, detalle, usuario_id) VALUES (?, ?, 'inicial', 'Alta de producto', ?)",
                        (cur.lastrowid, stock_inicial, g.usuario["id"]),
                    )
                db.commit()
                flash(f"Producto «{datos['nombre']}» creado.", "ok")
                return redirect(url_for("productos.lista"))
            except sqlite3.IntegrityError:
                db.rollback()
                errores.append("Ya existe un producto con ese código.")
        for e in errores:
            flash(e, "error")
    return render_template("productos/form.html", p=request.form, categorias=categorias,
                           proveedores=proveedores, nuevo=True)


@bp.route("/<int:pid>", methods=("GET", "POST"))
@login_requerido
def detalle(pid):
    db = get_db()
    p = db.execute("SELECT * FROM productos WHERE id = ? AND activo = 1", (pid,)).fetchone()
    if p is None:
        abort(404)
    if request.method == "POST":
        if g.usuario["rol"] != "admin":
            abort(403)
        datos, errores = _leer_form()
        if not errores:
            try:
                db.execute(
                    """UPDATE productos SET codigo=:codigo, nombre=:nombre, categoria_id=:categoria_id,
                       proveedor_id=:proveedor_id, precio_costo=:precio_costo, precio_venta=:precio_venta,
                       stock_minimo=:stock_minimo, vencimiento=:vencimiento WHERE id=:id""",
                    {**datos, "id": pid},
                )
                flash("Cambios guardados.", "ok")
                return redirect(url_for("productos.detalle", pid=pid))
            except sqlite3.IntegrityError:
                errores.append("Ya existe otro producto con ese código.")
        for e in errores:
            flash(e, "error")
    movimientos = db.execute(
        """SELECT m.*, u.nombre AS usuario FROM movimientos_stock m
           LEFT JOIN usuarios u ON u.id = m.usuario_id
           WHERE m.producto_id = ? ORDER BY m.id DESC LIMIT 30""",
        (pid,),
    ).fetchall()
    categorias, proveedores = _opciones()
    return render_template("productos/form.html", p=request.form if request.method == "POST" else p,
                           producto=p, movimientos=movimientos, categorias=categorias,
                           proveedores=proveedores, nuevo=False)


@bp.route("/<int:pid>/ajuste", methods=("POST",))
@solo_admin
def ajuste(pid):
    try:
        dif = ajustar_stock(get_db(), g.usuario["id"], pid,
                            request.form.get("stock_real", type=int, default=-1),
                            request.form.get("detalle", ""))
        flash("Stock sin cambios." if dif == 0 else f"Stock ajustado ({dif:+d}).", "ok")
    except ErrorStock as e:
        flash(str(e), "error")
    return redirect(url_for("productos.detalle", pid=pid))


@bp.route("/<int:pid>/baja", methods=("POST",))
@solo_admin
def baja(pid):
    get_db().execute("UPDATE productos SET activo = 0 WHERE id = ?", (pid,))
    flash("Producto dado de baja (el historial se conserva).", "ok")
    return redirect(url_for("productos.lista"))
