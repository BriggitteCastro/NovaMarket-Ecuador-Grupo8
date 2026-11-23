# NovaMarket Ecuador — Tienda web del Grupo 8

## Ejecutar en Windows

1. Instala Python 3.10 o posterior y marca «Add Python to PATH».
2. Abre la carpeta `NovaMarket_Grupo8` en Visual Studio Code.
3. En la terminal, ejecuta `python web_app.py`.
4. Abre **http://localhost:8000** en Chrome o Edge.

También puedes hacer doble clic en `INICIAR_WEB.bat` si Python está disponible en PATH.

## Qué puedes demostrar

- **Catálogo:** seis productos con precio base inmutable y existencias.
- **Carrito:** agregar o quitar productos y actualizar inventario y recomendaciones (Observer).
- **Decorator:** descuento, impuesto y envío configurables; los precios base nunca se alteran.
- **Factory Method:** generar tres formatos de factura mediante creadores concretos.
- **Factura:** se descarga como archivo HTML y se puede imprimir desde el navegador.
- **UML:** `uml/novamarket_uml.png` corresponde a las clases del núcleo Python.

## Pruebas

Desde la carpeta del proyecto: `python -m unittest -v`.

El servidor web mantiene los cambios en memoria mientras esté abierto. Reiniciar el servidor restablece las existencias y el carrito. Se trata de un prototipo académico local, sin cobros reales, cuentas de usuario ni comprobantes fiscales autorizados.

**Responsables:** Briggitte Castro Pacheco y Aleyska Cabrera Bravo.
