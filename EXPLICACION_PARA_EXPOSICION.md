# Responsables del proyecto

**Briggitte Castro Pacheco y Aleyska Cabrera Bravo**

# Grupo 8 — NovaMarket Ecuador: guía breve de defensa

**Problema**: una tienda requiere catálogo, precios variables, varios tipos de factura y avisos automáticos cuando cambia el carrito.

**Decorator**: `Producto` tiene un precio base inmutable. `PrecioBase` adapta precio × cantidad a `ComponentePrecio`; los decoradores aplican descuento, impuesto y envío. El envío se aplica una sola vez al subtotal agregado. Ejemplo: $114.00 - $11.40 + $15.39 + $5.00 = $122.99. OCP.

**Factory Method**: `Pedido` usa un `CreadorFactura` abstracto; cada creador concreto instancia `FacturaNacional`, `FacturaExportacion` o `FacturaSimplificada`. El contenido comercial se presenta como HTML imprimible. OCP y DIP.

**Observer**: `CarritoCompras` registra `Observador`; cuando se agrega o elimina una unidad, notifica a `ModuloStock` y `SistemaRecomendaciones`. DIP.

**Demostración**: `python novamarket.py` muestra catálogo, eventos, existencias y tres facturas. `python novamarket.py --menu` permite operaciones interactivas. `python -m unittest -v` ejecuta 15 pruebas.

**Preguntas frecuentes**:
- ¿Por qué no modificar Producto? Porque Decorator permite combinar operaciones y mantener el precio original.
- ¿Factory Method es solo un if? No: las subclases concretas deciden qué factura instanciar mediante un método polimórfico.
- ¿Qué es el sujeto en Observer? `CarritoCompras`; los observadores son stock y recomendaciones.
- ¿Las facturas son válidas en Ecuador? No: son muestras académicas con datos inventados, sin autorización SRI.
- ¿Qué mejoraría para producción? Persistencia, transacciones de stock, reglas fiscales verificadas, autenticación y pruebas de integración.
