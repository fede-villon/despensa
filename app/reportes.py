"""Reportes de ventas y exportación a CSV (se abre directo en Excel)."""
import csv
import io
from datetime import date, timedelta

from flask import Blueprint, Response, render_template, request

from .auth import solo_admin
from .db import get_db

bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _rango():
    hoy = date.today()
    desde = request.args.get("desde") or (hoy - timedelta(days=29)).isoformat()
    hasta = request.args.get("hasta") or hoy.isoformat()
    return desde, hasta


@bp.route("/")
@solo_admin
def resumen():
    db = get_db()
    desde, hasta = _rango()
    rango = (desde, hasta)
    totales = db.execute(
        """SELECT COUNT(DISTINCT v.id) AS ventas, COALESCE(SUM(vi.cantidad * vi.precio_unitario), 0) AS facturado,
                  COALESCE(SUM(vi.cantidad * (vi.precio_unitario - vi.costo_unitario)), 0) AS ganancia
           FROM ventas v JOIN venta_items vi ON vi.venta_id = v.id
           WHERE date(v.fecha) BETWEEN ? AND ?""",
        rango,
    ).fetchone()
    por_dia = db.execute(
        """SELECT date(fecha) AS dia, COUNT(*) AS ventas, SUM(total) AS total
           FROM ventas WHERE date(fecha) BETWEEN ? AND ? GROUP BY dia ORDER BY dia""",
        rango,
    ).fetchall()
    top = db.execute(
        """SELECT p.nombre, SUM(vi.cantidad) AS unidades, SUM(vi.cantidad * vi.precio_unitario) AS facturado,
                  SUM(vi.cantidad * (vi.precio_unitario - vi.costo_unitario)) AS ganancia
           FROM venta_items vi JOIN ventas v ON v.id = vi.venta_id JOIN productos p ON p.id = vi.producto_id
           WHERE date(v.fecha) BETWEEN ? AND ?
           GROUP BY p.id ORDER BY unidades DESC LIMIT 10""",
        rango,
    ).fetchall()
    medios = db.execute(
        """SELECT medio_pago, COUNT(*) AS ventas, SUM(total) AS total
           FROM ventas WHERE date(fecha) BETWEEN ? AND ? GROUP BY medio_pago ORDER BY total DESC""",
        rango,
    ).fetchall()
    categorias = db.execute(
        """SELECT COALESCE(c.nombre, 'Sin categoría') AS categoria, SUM(vi.cantidad * vi.precio_unitario) AS facturado
           FROM venta_items vi JOIN ventas v ON v.id = vi.venta_id JOIN productos p ON p.id = vi.producto_id
           LEFT JOIN categorias c ON c.id = p.categoria_id
           WHERE date(v.fecha) BETWEEN ? AND ? GROUP BY categoria ORDER BY facturado DESC""",
        rango,
    ).fetchall()
    sin_movimiento = db.execute(
        """SELECT p.nombre, p.stock, p.stock * p.precio_costo AS capital FROM productos p
           WHERE p.activo = 1 AND p.stock > 0 AND p.id NOT IN (
               SELECT vi.producto_id FROM venta_items vi JOIN ventas v ON v.id = vi.venta_id
               WHERE date(v.fecha) BETWEEN ? AND ?)
           ORDER BY capital DESC LIMIT 10""",
        rango,
    ).fetchall()
    maximo_dia = max((d["total"] for d in por_dia), default=0)
    return render_template("reportes.html", desde=desde, hasta=hasta, totales=totales, por_dia=por_dia,
                           maximo_dia=maximo_dia, top=top, medios=medios, categorias=categorias,
                           sin_movimiento=sin_movimiento)


def _csv(nombre: str, encabezado: list[str], filas) -> Response:
    buf = io.StringIO()
    buf.write("﻿")  # BOM: Excel reconoce los acentos
    w = csv.writer(buf, delimiter=";")  # ';' es el separador que espera Excel en español
    w.writerow(encabezado)
    w.writerows([list(f) for f in filas])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={nombre}"})


@bp.route("/exportar/ventas.csv")
@solo_admin
def exportar_ventas():
    desde, hasta = _rango()
    filas = get_db().execute(
        """SELECT v.id, v.fecha, u.nombre, v.medio_pago, p.codigo, p.nombre, vi.cantidad,
                  vi.precio_unitario, vi.cantidad * vi.precio_unitario,
                  vi.cantidad * (vi.precio_unitario - vi.costo_unitario)
           FROM ventas v JOIN venta_items vi ON vi.venta_id = v.id
           JOIN productos p ON p.id = vi.producto_id JOIN usuarios u ON u.id = v.usuario_id
           WHERE date(v.fecha) BETWEEN ? AND ? ORDER BY v.id""",
        (desde, hasta),
    ).fetchall()
    return _csv(f"ventas_{desde}_a_{hasta}.csv",
                ["venta", "fecha", "cajero", "medio_pago", "codigo", "producto", "cantidad",
                 "precio_unitario", "subtotal", "ganancia"], filas)


@bp.route("/exportar/stock.csv")
@solo_admin
def exportar_stock():
    filas = get_db().execute(
        """SELECT p.codigo, p.nombre, COALESCE(c.nombre, ''), p.stock, p.stock_minimo, p.precio_costo,
                  p.precio_venta, p.stock * p.precio_costo, COALESCE(p.vencimiento, '')
           FROM productos p LEFT JOIN categorias c ON c.id = p.categoria_id
           WHERE p.activo = 1 ORDER BY p.nombre"""
    ).fetchall()
    return _csv("stock.csv", ["codigo", "producto", "categoria", "stock", "stock_minimo", "costo",
                              "precio_venta", "capital_inmovilizado", "vencimiento"], filas)
