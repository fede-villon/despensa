"""Recorridos de usuario por las pantallas principales."""
from tests.conftest import ingresar


def test_sin_sesion_redirige_al_login(cliente):
    r = cliente.get("/")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_login_incorrecto(cliente):
    r = ingresar(cliente, clave="mal")
    assert "incorrectos" in r.get_data(as_text=True)


def test_admin_ve_todas_las_secciones(cliente):
    ingresar(cliente)
    for ruta in ("/", "/productos/", "/ventas/", "/ventas/caja", "/compras/", "/compras/nueva?proveedor_id=1",
                 "/reportes/", "/productos/1", "/productos/nuevo", "/ventas/1"):
        assert cliente.get(ruta).status_code == 200, ruta


def test_cajero_no_entra_a_reportes_ni_compras(cliente):
    ingresar(cliente, "cajero", "cajero123")
    for ruta in ("/reportes/", "/compras/", "/productos/nuevo"):
        r = cliente.get(ruta)
        assert r.status_code == 302, ruta
    assert cliente.post("/productos/1", data={"nombre": "x"}).status_code == 403


def test_flujo_de_caja_completo(cliente):
    ingresar(cliente, "cajero", "cajero123")
    cliente.post("/ventas/caja/agregar", data={"codigo": "7790002000010", "cantidad": 2})  # leche
    cliente.post("/ventas/caja/agregar", data={"codigo": "alfajor"})  # búsqueda por nombre
    r = cliente.get("/ventas/caja?q=alfajor")
    assert "Alfajor triple" in r.get_data(as_text=True)
    r = cliente.post("/ventas/caja/cobrar", data={"medio_pago": "transferencia"}, follow_redirects=True)
    texto = r.get_data(as_text=True)
    assert "registrada" in texto and "Leche entera 1 L" in texto


def test_exportar_csv(cliente):
    ingresar(cliente)
    r = cliente.get("/reportes/exportar/ventas.csv")
    assert r.status_code == 200 and r.mimetype == "text/csv"
    assert r.get_data(as_text=True).splitlines()[0].lstrip("﻿").startswith("venta;fecha")
