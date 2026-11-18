"""Filtros de plantilla para mostrar pesos y fechas al estilo argentino."""
from datetime import datetime


def pesos(valor) -> str:
    n = int(valor or 0)
    signo = "-" if n < 0 else ""
    return f"{signo}${abs(n):,}".replace(",", ".")


def fecha(valor) -> str:
    if not valor:
        return "—"
    texto = str(valor)
    for fmt, salida in (("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"), ("%Y-%m-%d", "%d/%m/%Y")):
        try:
            return datetime.strptime(texto, fmt).strftime(salida)
        except ValueError:
            continue
    return texto


MEDIOS = {"efectivo": "Efectivo", "debito": "Débito", "credito": "Crédito", "transferencia": "Transferencia"}


def registrar_filtros(app):
    app.jinja_env.filters["pesos"] = pesos
    app.jinja_env.filters["fecha"] = fecha
    app.jinja_env.globals["MEDIOS"] = MEDIOS
