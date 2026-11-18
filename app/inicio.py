"""Panel de inicio: resumen del día y alertas."""
from flask import Blueprint, render_template

from .auth import login_requerido
from .db import get_db

bp = Blueprint("inicio", __name__)

DIAS_AVISO_VENCIMIENTO = 7


@bp.route("/")
@login_requerido
def panel():
    db = get_db()
    hoy = db.execute(
        """SELECT COUNT(*) AS cantidad, COALESCE(SUM(total), 0) AS total
           FROM ventas WHERE date(fecha) = date('now', 'localtime')"""
    ).fetchone()
    ganancia_hoy = db.execute(
        """SELECT COALESCE(SUM(vi.cantidad * (vi.precio_unitario - vi.costo_unitario)), 0)
           FROM venta_items vi JOIN ventas v ON v.id = vi.venta_id
           WHERE date(v.fecha) = date('now', 'localtime')"""
    ).fetchone()[0]
    stock_bajo = db.execute(
        """SELECT id, codigo, nombre, stock, stock_minimo FROM productos
           WHERE activo = 1 AND stock <= stock_minimo ORDER BY stock - stock_minimo, nombre"""
    ).fetchall()
    por_vencer = db.execute(
        """SELECT id, codigo, nombre, stock, vencimiento,
                  CAST(julianday(vencimiento) - julianday(date('now', 'localtime')) AS INTEGER) AS dias
           FROM productos
           WHERE activo = 1 AND stock > 0 AND vencimiento IS NOT NULL
             AND vencimiento <= date('now', 'localtime', ?)
           ORDER BY vencimiento""",
        (f"+{DIAS_AVISO_VENCIMIENTO} days",),
    ).fetchall()
    ultimas = db.execute(
        """SELECT v.id, v.fecha, v.total, v.medio_pago, u.nombre AS cajero
           FROM ventas v JOIN usuarios u ON u.id = v.usuario_id
           ORDER BY v.id DESC LIMIT 6"""
    ).fetchall()
    return render_template(
        "inicio.html", hoy=hoy, ganancia_hoy=ganancia_hoy, stock_bajo=stock_bajo,
        por_vencer=por_vencer, ultimas=ultimas, dias_aviso=DIAS_AVISO_VENCIMIENTO,
    )
