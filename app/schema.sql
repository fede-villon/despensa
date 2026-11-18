-- Despensa: modelo de datos (SQLite)
-- Los precios se guardan en pesos enteros (sin centavos).

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS movimientos_stock;
DROP TABLE IF EXISTS compra_items;
DROP TABLE IF EXISTS compras;
DROP TABLE IF EXISTS venta_items;
DROP TABLE IF EXISTS ventas;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS proveedores;
DROP TABLE IF EXISTS categorias;
DROP TABLE IF EXISTS usuarios;

CREATE TABLE usuarios (
    id          INTEGER PRIMARY KEY,
    usuario     TEXT NOT NULL UNIQUE,
    nombre      TEXT NOT NULL,
    clave_hash  TEXT NOT NULL,
    rol         TEXT NOT NULL CHECK (rol IN ('admin', 'cajero')),
    activo      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE categorias (
    id      INTEGER PRIMARY KEY,
    nombre  TEXT NOT NULL UNIQUE
);

CREATE TABLE proveedores (
    id        INTEGER PRIMARY KEY,
    nombre    TEXT NOT NULL UNIQUE,
    telefono  TEXT,
    email     TEXT
);

CREATE TABLE productos (
    id            INTEGER PRIMARY KEY,
    codigo        TEXT NOT NULL UNIQUE,          -- código de barras o interno
    nombre        TEXT NOT NULL,
    categoria_id  INTEGER REFERENCES categorias(id),
    proveedor_id  INTEGER REFERENCES proveedores(id),
    precio_costo  INTEGER NOT NULL CHECK (precio_costo >= 0),
    precio_venta  INTEGER NOT NULL CHECK (precio_venta >= 0),
    stock         INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    stock_minimo  INTEGER NOT NULL DEFAULT 0 CHECK (stock_minimo >= 0),
    vencimiento   TEXT,                          -- AAAA-MM-DD, opcional
    activo        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE ventas (
    id          INTEGER PRIMARY KEY,
    fecha       TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
    medio_pago  TEXT NOT NULL CHECK (medio_pago IN ('efectivo', 'debito', 'credito', 'transferencia')),
    total       INTEGER NOT NULL
);

CREATE TABLE venta_items (
    id               INTEGER PRIMARY KEY,
    venta_id         INTEGER NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    producto_id      INTEGER NOT NULL REFERENCES productos(id),
    cantidad         INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario  INTEGER NOT NULL,   -- precio al momento de la venta
    costo_unitario   INTEGER NOT NULL    -- costo al momento de la venta (para calcular margen)
);

CREATE TABLE compras (
    id            INTEGER PRIMARY KEY,
    fecha         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    proveedor_id  INTEGER NOT NULL REFERENCES proveedores(id),
    usuario_id    INTEGER NOT NULL REFERENCES usuarios(id),
    total         INTEGER NOT NULL
);

CREATE TABLE compra_items (
    id              INTEGER PRIMARY KEY,
    compra_id       INTEGER NOT NULL REFERENCES compras(id) ON DELETE CASCADE,
    producto_id     INTEGER NOT NULL REFERENCES productos(id),
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    costo_unitario  INTEGER NOT NULL
);

-- Cada cambio de stock queda registrado: permite auditar diferencias.
CREATE TABLE movimientos_stock (
    id           INTEGER PRIMARY KEY,
    fecha        TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    producto_id  INTEGER NOT NULL REFERENCES productos(id),
    cantidad     INTEGER NOT NULL,       -- positivo entra, negativo sale
    motivo       TEXT NOT NULL CHECK (motivo IN ('venta', 'compra', 'ajuste', 'inicial')),
    detalle      TEXT,
    usuario_id   INTEGER REFERENCES usuarios(id)
);

CREATE INDEX idx_ventas_fecha ON ventas(fecha);
CREATE INDEX idx_venta_items_producto ON venta_items(producto_id);
CREATE INDEX idx_movimientos_producto ON movimientos_stock(producto_id);
