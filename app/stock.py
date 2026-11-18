"""Reglas de negocio de stock, ventas y compras.

Todo lo que modifica stock pasa por acá, dentro de una transacción, y deja
un registro en movimientos_stock. Así las pantallas no tocan el stock directo.
"""
import sqlite3


class ErrorStock(Exception):
    """Error de negocio que se muestra al usuario (ej. falta stock)."""


def registrar_venta(db: sqlite3.Connection, usuario_id: int, items: dict[int, int], medio_pago: str) -> int:
    """items = {producto_id: cantidad}. Devuelve el id de la venta."""
    if not items:
        raise ErrorStock("El carrito está vacío.")
    try:
        db.execute("BEGIN IMMEDIATE")
        filas = []
        for pid, cant in items.items():
            p = db.execute("SELECT * FROM productos WHERE id = ? AND activo = 1", (pid,)).fetchone()
            if p is None:
                raise ErrorStock("Un producto del carrito ya no existe.")
            if cant <= 0:
                raise ErrorStock(f"Cantidad inválida para {p['nombre']}.")
            if p["stock"] < cant:
                raise ErrorStock(f"No hay stock suficiente de {p['nombre']} (quedan {p['stock']}).")
            filas.append((p, cant))
        total = sum(p["precio_venta"] * c for p, c in filas)
        cur = db.execute(
            "INSERT INTO ventas (usuario_id, medio_pago, total) VALUES (?, ?, ?)",
            (usuario_id, medio_pago, total),
        )
        venta_id = cur.lastrowid
        for p, c in filas:
            db.execute(
                "INSERT INTO venta_items (venta_id, producto_id, cantidad, precio_unitario, costo_unitario) VALUES (?, ?, ?, ?, ?)",
                (venta_id, p["id"], c, p["precio_venta"], p["precio_costo"]),
            )
            _mover(db, p["id"], -c, "venta", f"Venta #{venta_id}", usuario_id)
        db.commit()
        return venta_id
    except Exception:
        db.rollback()
        raise


def registrar_compra(db: sqlite3.Connection, usuario_id: int, proveedor_id: int, items: list[tuple[int, int, int]],
                     actualizar_costo: bool = True) -> int:
    """items = [(producto_id, cantidad, costo_unitario)]. Suma stock y, opcionalmente, actualiza el costo."""
    items = [(p, c, k) for p, c, k in items if c > 0]
    if not items:
        raise ErrorStock("Cargá al menos un producto con cantidad.")
    try:
        db.execute("BEGIN IMMEDIATE")
        total = sum(c * k for _, c, k in items)
        cur = db.execute(
            "INSERT INTO compras (proveedor_id, usuario_id, total) VALUES (?, ?, ?)",
            (proveedor_id, usuario_id, total),
        )
        compra_id = cur.lastrowid
        for pid, cant, costo in items:
            db.execute(
                "INSERT INTO compra_items (compra_id, producto_id, cantidad, costo_unitario) VALUES (?, ?, ?, ?)",
                (compra_id, pid, cant, costo),
            )
            _mover(db, pid, cant, "compra", f"Compra #{compra_id}", usuario_id)
            if actualizar_costo:
                db.execute("UPDATE productos SET precio_costo = ? WHERE id = ?", (costo, pid))
        db.commit()
        return compra_id
    except Exception:
        db.rollback()
        raise


def ajustar_stock(db: sqlite3.Connection, usuario_id: int, producto_id: int, stock_real: int, detalle: str) -> int:
    """Corrige el stock al valor contado físicamente. Devuelve la diferencia aplicada."""
    if stock_real < 0:
        raise ErrorStock("El stock no puede ser negativo.")
    if not detalle.strip():
        raise ErrorStock("Indicá el motivo del ajuste (ej. rotura, conteo, vencido).")
    try:
        db.execute("BEGIN IMMEDIATE")
        actual = db.execute("SELECT stock FROM productos WHERE id = ?", (producto_id,)).fetchone()
        if actual is None:
            raise ErrorStock("Producto inexistente.")
        dif = stock_real - actual["stock"]
        if dif:
            _mover(db, producto_id, dif, "ajuste", detalle.strip(), usuario_id)
        db.commit()
        return dif
    except Exception:
        db.rollback()
        raise


def _mover(db, producto_id, cantidad, motivo, detalle, usuario_id):
    db.execute("UPDATE productos SET stock = stock + ? WHERE id = ?", (cantidad, producto_id))
    db.execute(
        "INSERT INTO movimientos_stock (producto_id, cantidad, motivo, detalle, usuario_id) VALUES (?, ?, ?, ?, ?)",
        (producto_id, cantidad, motivo, detalle, usuario_id),
    )
