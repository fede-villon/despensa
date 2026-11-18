# Manual de uso

Guía para el dueño del almacén y para quien atiende la caja.

## Ingresar

Abrí el navegador en la dirección del sistema (por ejemplo `http://localhost:5000`) y entrá con tu usuario y contraseña.

- **Dueño (admin):** ve todo, carga productos, registra compras y mira reportes.
- **Cajero:** vende y consulta productos y precios.

## Inicio

Lo primero que ves al entrar:

- **Vendido hoy, cantidad de ventas y ganancia del día.**
- **Reponer:** productos que llegaron al stock mínimo. Si aparece en rojo, no queda ninguno.
- **Por vencer:** lo que vence en los próximos 7 días. Conviene ponerlo adelante en la góndola o en oferta.

## Vender (Caja)

1. Escaneá el código de barras con el lector, o escribí el nombre y apretá *Enter*.
2. Si escribiste un nombre, elegí el producto de la lista con **Agregar**.
3. Para varias unidades, cambiá la cantidad antes de agregar.
4. Para sacar algo de la venta, tocá la **×**.
5. Elegí el medio de pago y apretá **Cobrar**.
6. Aparece el comprobante. Si el cliente lo pide, tocá **Imprimir**.

Si falta stock de algún producto, el sistema avisa y **no registra la venta**. Así no queda nada a medias.

## Productos

- **Buscar:** por nombre o código. Con *Solo stock bajo* ves qué hay que pedir.
- **Nuevo producto (dueño):** código, nombre, categoría, proveedor, costo, precio de venta, stock inicial, stock mínimo y vencimiento si tiene.
- **Editar precios:** entrá al producto, cambiá el valor y guardá. Las ventas anteriores no cambian.
- **Ajustar stock:** después de contar la góndola, o si hubo roturas o vencidos. Poné la cantidad real y el motivo.
- **Movimientos:** en cada producto ves quién movió stock, cuándo y por qué.

## Ingresar mercadería (Compras)

1. **Compras → Ingresar mercadería.**
2. Elegí el proveedor: aparecen sus productos (en amarillo, los que hacen falta).
3. Cargá cuánto llegó y a qué costo.
4. **Registrar compra**: el stock se suma solo.

## Reportes (dueño)

Elegí el rango de fechas para ver:

- Facturado, ganancia bruta, cantidad de ventas y ticket promedio.
- Gráfico de ventas por día: pasá el mouse por una barra para ver el detalle.
- Más vendidos, medios de pago y ventas por categoría.
- **Sin ventas en el período:** productos que no rotan y cuánta plata hay parada en ellos.

Con **Exportar** descargás ventas o stock en un archivo que se abre en Excel.
