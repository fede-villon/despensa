"""Datos de demostración: un almacén de barrio ficticio con 30 días de ventas."""
import random
from datetime import date, datetime, timedelta

from werkzeug.security import generate_password_hash

PROVEEDORES = [
    ("Distribuidora Del Litoral", "343 455-1020", "pedidos@dellitoral.example"),
    ("Lácteos La Pradera", "343 488-3311", "ventas@lapradera.example"),
    ("Bebidas Norte", "343 470-7788", None),
    ("Panificados Don Julio", "343 461-2299", None),
]

# (código, nombre, categoría, proveedor, costo, venta, stock, mínimo, días hasta vencer o None)
PRODUCTOS = [
    ("7790001000011", "Yerba mate 1 kg", "Almacén", 0, 3900, 5200, 24, 8, None),
    ("7790001000028", "Azúcar 1 kg", "Almacén", 0, 1100, 1500, 30, 10, None),
    ("7790001000035", "Fideos tallarín 500 g", "Almacén", 0, 950, 1350, 40, 12, None),
    ("7790001000042", "Arroz largo fino 1 kg", "Almacén", 0, 1400, 1950, 22, 8, None),
    ("7790001000059", "Aceite girasol 1,5 L", "Almacén", 0, 2600, 3500, 15, 6, None),
    ("7790001000066", "Harina 000 1 kg", "Almacén", 0, 700, 990, 18, 8, None),
    ("7790001000073", "Puré de tomate 520 g", "Almacén", 0, 650, 950, 35, 10, None),
    ("7790001000080", "Café molido 250 g", "Almacén", 0, 3200, 4400, 6, 4, None),
    ("7790001000097", "Galletitas de agua 300 g", "Almacén", 0, 900, 1300, 3, 10, None),
    ("7790001000103", "Dulce de leche 400 g", "Almacén", 1, 1500, 2100, 14, 6, 90),
    ("7790002000010", "Leche entera 1 L", "Lácteos", 1, 900, 1250, 36, 15, 5),
    ("7790002000027", "Yogur bebible 1 L", "Lácteos", 1, 1300, 1800, 12, 6, 4),
    ("7790002000034", "Queso cremoso 1 kg", "Lácteos", 1, 6200, 8500, 4, 3, 12),
    ("7790002000041", "Manteca 200 g", "Lácteos", 1, 1600, 2250, 2, 5, 20),
    ("7790002000058", "Crema de leche 200 ml", "Lácteos", 1, 1100, 1550, 9, 4, 3),
    ("7790003000017", "Gaseosa cola 2,25 L", "Bebidas", 2, 2100, 2900, 28, 12, None),
    ("7790003000024", "Agua mineral 2 L", "Bebidas", 2, 700, 1100, 30, 12, None),
    ("7790003000031", "Cerveza lata 473 ml", "Bebidas", 2, 1100, 1600, 48, 24, None),
    ("7790003000048", "Jugo en polvo", "Bebidas", 2, 250, 450, 60, 20, None),
    ("7790003000055", "Vino tinto 750 ml", "Bebidas", 2, 2800, 4200, 10, 4, None),
    ("7790003000062", "Soda sifón 2 L", "Bebidas", 2, 600, 950, 7, 8, None),
    ("7790004000014", "Pan francés 1 kg", "Panadería", 3, 1500, 2300, 8, 4, 1),
    ("7790004000021", "Facturas (docena)", "Panadería", 3, 3000, 4800, 3, 2, 1),
    ("7790004000038", "Pan lactal", "Panadería", 3, 1700, 2500, 6, 3, 6),
    ("7790005000011", "Lavandina 1 L", "Limpieza", 0, 600, 900, 20, 6, None),
    ("7790005000028", "Detergente 500 ml", "Limpieza", 0, 900, 1350, 14, 6, None),
    ("7790005000035", "Papel higiénico x4", "Limpieza", 0, 1800, 2600, 12, 6, None),
    ("7790005000042", "Jabón en polvo 800 g", "Limpieza", 0, 2700, 3700, 5, 4, None),
    ("7790006000018", "Alfajor triple", "Kiosco", 0, 600, 1000, 45, 15, 60),
    ("7790006000025", "Chocolate 100 g", "Kiosco", 0, 1500, 2300, 18, 8, 120),
    ("7790006000032", "Caramelos (bolsa)", "Kiosco", 0, 900, 1500, 20, 6, None),
    ("7790006000049", "Papas fritas 150 g", "Kiosco", 2, 1400, 2100, 16, 6, 45),
    ("7790006000056", "Chicles", "Kiosco", 0, 300, 600, 40, 10, None),
]

# Peso relativo de venta (los de almacén básico salen más)
POPULARIDAD = {
    "Leche entera 1 L": 9, "Pan francés 1 kg": 9, "Gaseosa cola 2,25 L": 7, "Yerba mate 1 kg": 6,
    "Alfajor triple": 7, "Agua mineral 2 L": 5, "Cerveza lata 473 ml": 6, "Fideos tallarín 500 g": 5,
    "Facturas (docena)": 4, "Galletitas de agua 300 g": 4, "Chicles": 4, "Azúcar 1 kg": 3,
}


def cargar_demo(db):
    rnd = random.Random(42)
    db.execute("BEGIN")
    db.executemany(
        "INSERT INTO usuarios (usuario, nombre, clave_hash, rol) VALUES (?, ?, ?, ?)",
        [
            ("admin", "Marta (dueña)", generate_password_hash("admin123"), "admin"),
            ("cajero", "Lucas (caja)", generate_password_hash("cajero123"), "cajero"),
        ],
    )
    db.executemany("INSERT INTO proveedores (nombre, telefono, email) VALUES (?, ?, ?)", PROVEEDORES)
    prov_ids = [r[0] for r in db.execute("SELECT id FROM proveedores ORDER BY id")]
    cats = sorted({p[2] for p in PRODUCTOS})
    db.executemany("INSERT INTO categorias (nombre) VALUES (?)", [(c,) for c in cats])
    cat_id = {r["nombre"]: r["id"] for r in db.execute("SELECT id, nombre FROM categorias")}

    hoy = date.today()
    productos = []
    for cod, nom, cat, prov, costo, venta, stock, minimo, vence in PRODUCTOS:
        venc = (hoy + timedelta(days=vence)).isoformat() if vence is not None else None
        cur = db.execute(
            """INSERT INTO productos (codigo, nombre, categoria_id, proveedor_id, precio_costo, precio_venta,
               stock, stock_minimo, vencimiento) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cod, nom, cat_id[cat], prov_ids[prov], costo, venta, stock, minimo, venc),
        )
        db.execute(
            "INSERT INTO movimientos_stock (fecha, producto_id, cantidad, motivo, detalle, usuario_id) VALUES (?, ?, ?, 'inicial', 'Inventario inicial', 1)",
            ((hoy - timedelta(days=31)).isoformat() + " 08:00:00", cur.lastrowid, stock),
        )
        productos.append({"id": cur.lastrowid, "nombre": nom, "costo": costo, "venta": venta})

    # Historial de ventas de los últimos 30 días. Se cargan solo como histórico para los reportes:
    # no descuentan stock (el stock de arriba representa lo que hay hoy en la góndola).
    pesos = [POPULARIDAD.get(p["nombre"], 2) for p in productos]
    medios = ["efectivo"] * 5 + ["debito"] * 3 + ["transferencia"] * 3 + ["credito"]
    for dias_atras in range(30, -1, -1):
        dia = hoy - timedelta(days=dias_atras)
        cantidad_ventas = rnd.randint(14, 26) if dia.weekday() < 5 else rnd.randint(22, 34)
        if dias_atras == 0:
            cantidad_ventas = 9
        for _ in range(cantidad_ventas):
            hora = datetime.combine(dia, datetime.min.time()) + timedelta(
                hours=rnd.choice([8, 9, 10, 11, 12, 17, 18, 19, 20, 21]), minutes=rnd.randint(0, 59))
            if dias_atras == 0 and hora > datetime.now():
                hora = datetime.now() - timedelta(minutes=rnd.randint(5, 300))
            elegidos = {}
            for p in rnd.choices(productos, weights=pesos, k=rnd.randint(1, 4)):
                elegidos[p["id"]] = (p, elegidos.get(p["id"], (p, 0))[1] + rnd.choice([1, 1, 1, 2]))
            total = sum(p["venta"] * c for p, c in elegidos.values())
            cur = db.execute(
                "INSERT INTO ventas (fecha, usuario_id, medio_pago, total) VALUES (?, ?, ?, ?)",
                (hora.strftime("%Y-%m-%d %H:%M:%S"), rnd.choice([1, 2, 2]), rnd.choice(medios), total),
            )
            db.executemany(
                "INSERT INTO venta_items (venta_id, producto_id, cantidad, precio_unitario, costo_unitario) VALUES (?, ?, ?, ?, ?)",
                [(cur.lastrowid, p["id"], c, p["venta"], p["costo"]) for p, c in elegidos.values()],
            )
    db.commit()
