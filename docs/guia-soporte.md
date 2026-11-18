# Guía de soporte

Problemas frecuentes, cómo diagnosticarlos y cómo resolverlos. Está escrita como la usaría una mesa de ayuda: síntoma → causa probable → qué hacer.

## Primeros pasos ante cualquier reporte

1. **¿Qué estaba haciendo?** Pantalla, producto y hora aproximada.
2. **¿Le pasa a todos o a un usuario?** Si es uno solo, suele ser de permisos o de sesión.
3. **¿Sale algún mensaje?** Pedí captura de pantalla.
4. **Revisá la consola del servidor**: ahí quedan los errores con fecha y ruta.

## Problemas frecuentes

### "No puedo entrar"
- **Usuario o contraseña incorrectos:** verificar mayúsculas y que el usuario esté activo.
  ```sql
  SELECT usuario, rol, activo FROM usuarios;
  ```
- **La página no carga:** el servidor no está corriendo. Iniciarlo con `flask --app app run` y verificar que el puerto (5000) no esté ocupado: `ss -ltnp | grep 5000`.

### "El cajero no ve Reportes o Compras"
Es lo esperado: esas secciones son solo para el rol `admin`. Si el cajero necesita acceso, que el dueño decida cambiarle el rol.

### "El lector de código de barras no agrega el producto"
1. Probar el lector en un bloc de notas: tiene que escribir el número y un *Enter*.
2. Si escribe bien, el código no está cargado en el sistema. Buscarlo por nombre y revisar el campo **Código** del producto.
3. Si no escribe nada, es un problema del lector o del cable USB (probar en otro puerto).

### "No me deja vender: dice que no hay stock"
El sistema tiene menos stock registrado que el que hay en la góndola.
1. Abrir el producto y revisar **Movimientos de stock**.
2. Lo común es que haya llegado mercadería sin registrar la compra. Registrarla en **Compras**, o hacer un **ajuste** con el motivo "conteo".

### "El stock no coincide con lo que hay en la góndola"
1. Revisar los movimientos del producto: ventas, compras y ajustes, con usuario y fecha.
2. Verificar que la base cuadre:
   ```sql
   SELECT p.nombre, p.stock, COALESCE(SUM(m.cantidad), 0) AS movimientos
   FROM productos p LEFT JOIN movimientos_stock m ON m.producto_id = p.id
   GROUP BY p.id HAVING p.stock <> movimientos;
   ```
3. Si cuadra, la diferencia es física (rotura, vencido, faltante): registrarla con un ajuste y su motivo.

### "El Excel exportado se ve con símbolos raros"
Abrir el archivo con doble clic: viene preparado para Excel en español (UTF-8 con BOM y separador `;`). Si se importa a mano, elegir codificación **UTF-8** y separador **punto y coma**.

### "Aparece 'database is locked'"
Hay otro programa con la base abierta (por ejemplo, un visor de SQLite). Cerrarlo y reintentar.

## Backup y restauración

La base es un único archivo: `instance/despensa.sqlite`.

**Backup en caliente** (sin cortar el sistema):
```bash
flask --app app backup                 # crea backup-AAAA-MM-DD_HHMM.sqlite
flask --app app backup /media/pendrive/despensa.sqlite
```

**Restaurar:** frenar el servidor, reemplazar `instance/despensa.sqlite` por el backup y volver a iniciarlo.

Lo recomendable es un backup diario copiado fuera de la PC del local (pendrive o nube).

## Escalar a desarrollo

Si el problema no está en esta guía, reportarlo con:
- Pasos para reproducirlo.
- Qué se esperaba y qué pasó.
- Captura y el error de la consola del servidor.
- Usuario y hora.
