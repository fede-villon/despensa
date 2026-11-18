"""Reglas de negocio: el stock siempre tiene que cuadrar con los movimientos."""
import pytest

from app.db import get_db
from app.stock import ErrorStock, ajustar_stock, registrar_compra, registrar_venta


def producto(db, nombre):
    return db.execute("SELECT * FROM productos WHERE nombre = ?", (nombre,)).fetchone()


def test_venta_descuenta_stock_y_registra_movimiento(app):
    with app.app_context():
        db = get_db()
        leche = producto(db, "Leche entera 1 L")
        vid = registrar_venta(db, 1, {leche["id"]: 3}, "efectivo")
        assert producto(db, "Leche entera 1 L")["stock"] == leche["stock"] - 3
        venta = db.execute("SELECT * FROM ventas WHERE id = ?", (vid,)).fetchone()
        assert venta["total"] == 3 * leche["precio_venta"]
        mov = db.execute("SELECT * FROM movimientos_stock WHERE detalle = ?", (f"Venta #{vid}",)).fetchone()
        assert mov["cantidad"] == -3 and mov["motivo"] == "venta"


def test_venta_sin_stock_no_cambia_nada(app):
    with app.app_context():
        db = get_db()
        leche = producto(db, "Leche entera 1 L")
        manteca = producto(db, "Manteca 200 g")  # stock 2
        ventas_antes = db.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
        with pytest.raises(ErrorStock, match="No hay stock suficiente"):
            registrar_venta(db, 1, {leche["id"]: 1, manteca["id"]: 5}, "efectivo")
        # La transacción se deshace completa: ni la leche se descuenta.
        assert producto(db, "Leche entera 1 L")["stock"] == leche["stock"]
        assert db.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] == ventas_antes


def test_venta_guarda_precio_historico(app):
    with app.app_context():
        db = get_db()
        yerba = producto(db, "Yerba mate 1 kg")
        vid = registrar_venta(db, 1, {yerba["id"]: 1}, "debito")
        db.execute("UPDATE productos SET precio_venta = 9999 WHERE id = ?", (yerba["id"],))
        item = db.execute("SELECT * FROM venta_items WHERE venta_id = ?", (vid,)).fetchone()
        assert item["precio_unitario"] == yerba["precio_venta"]


def test_compra_suma_stock_y_actualiza_costo(app):
    with app.app_context():
        db = get_db()
        cafe = producto(db, "Café molido 250 g")
        registrar_compra(db, 1, cafe["proveedor_id"], [(cafe["id"], 12, 3500)])
        nuevo = producto(db, "Café molido 250 g")
        assert nuevo["stock"] == cafe["stock"] + 12
        assert nuevo["precio_costo"] == 3500


def test_ajuste_exige_motivo_y_deja_registro(app):
    with app.app_context():
        db = get_db()
        pan = producto(db, "Pan lactal")
        with pytest.raises(ErrorStock):
            ajustar_stock(db, 1, pan["id"], 2, "  ")
        dif = ajustar_stock(db, 1, pan["id"], 2, "Conteo semanal")
        assert dif == 2 - pan["stock"]
        assert producto(db, "Pan lactal")["stock"] == 2


def test_stock_cuadra_con_movimientos_despues_de_operar(app):
    """Invariante: el stock de cada producto es la suma de todos sus movimientos."""
    with app.app_context():
        db = get_db()
        alfajor = producto(db, "Alfajor triple")
        registrar_venta(db, 2, {alfajor["id"]: 5}, "efectivo")
        registrar_compra(db, 1, alfajor["proveedor_id"], [(alfajor["id"], 24, 600)])
        ajustar_stock(db, 1, alfajor["id"], 60, "Conteo")
        suma = db.execute("SELECT SUM(cantidad) FROM movimientos_stock WHERE producto_id = ?", (alfajor["id"],)).fetchone()[0]
        assert producto(db, "Alfajor triple")["stock"] == suma == 60


def test_demo_cuadra_en_todos_los_productos(app):
    with app.app_context():
        filas = get_db().execute(
            """SELECT p.id FROM productos p LEFT JOIN movimientos_stock m ON m.producto_id = p.id
               GROUP BY p.id HAVING p.stock <> COALESCE(SUM(m.cantidad), 0)"""
        ).fetchall()
        assert filas == []
